"""CHK-04 — testes de API para autenticação, sessão e credenciais."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.main import app
from app.modules.audit_logs.model import AuditLog
from app.modules.auth.service import create_user_tokens
from app.modules.clinics.model import Clinic
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User

CURRENT_PASSWORD = "SenhaAtual123"
NEW_PASSWORD = "SenhaNova456"


@dataclass(frozen=True)
class AuthData:
    doctor_id: int
    admin_id: int
    inactive_user_id: int
    inactive_clinic_user_id: int
    active_clinic_id: int
    inactive_clinic_id: int


@dataclass(frozen=True)
class ApiContext:
    client: TestClient
    session_factory: sessionmaker
    data: AuthData


def _seed_auth_data(db: Session) -> AuthData:
    active_user_status = Status(
        name="active",
        display_name="Ativo",
        applies_to="user",
    )
    inactive_user_status = Status(
        name="inactive",
        display_name="Inativo",
        applies_to="user",
    )
    active_clinic_status = Status(
        name="active",
        display_name="Ativa",
        applies_to="clinic",
    )
    inactive_clinic_status = Status(
        name="inactive",
        display_name="Inativa",
        applies_to="clinic",
    )

    doctor_role = Role(
        name="doctor",
        display_name="Médico",
        permissions_initialized=True,
    )
    admin_role = Role(
        name="admin_master",
        display_name="Administrador Master",
        permissions_initialized=True,
    )

    read_profile = Permission(
        name="users:read_profile",
        display_name="Ler próprio perfil",
        module="users",
    )
    update_profile = Permission(
        name="users:update_profile",
        display_name="Atualizar próprio perfil",
        module="users",
    )

    active_clinic = Clinic(
        name="Clínica Ativa",
        cnpj="11111111000191",
        email="ativa@example.com",
        status=active_clinic_status,
    )
    inactive_clinic = Clinic(
        name="Clínica Inativa",
        cnpj="22222222000191",
        email="inativa@example.com",
        status=inactive_clinic_status,
    )

    db.add_all(
        [
            active_user_status,
            inactive_user_status,
            active_clinic_status,
            inactive_clinic_status,
            doctor_role,
            admin_role,
            read_profile,
            update_profile,
            active_clinic,
            inactive_clinic,
        ]
    )
    db.flush()

    db.add_all(
        [
            RolePermission(role=doctor_role, permission=read_profile),
            RolePermission(role=doctor_role, permission=update_profile),
        ]
    )

    doctor = User(
        name="Médico Ativo",
        email="medico.ativo@clinicai.local",
        cpf="11111111111",
        password_hash=get_password_hash(CURRENT_PASSWORD),
        token_version=0,
        role=doctor_role,
        status=active_user_status,
        clinic=active_clinic,
    )
    admin = User(
        name="Administrador",
        email="admin@clinicai.local",
        cpf="22222222222",
        password_hash=get_password_hash(CURRENT_PASSWORD),
        token_version=0,
        role=admin_role,
        status=active_user_status,
        clinic=None,
    )
    inactive_user = User(
        name="Usuário Inativo",
        email="usuario.inativo@clinicai.local",
        cpf="33333333333",
        password_hash=get_password_hash(CURRENT_PASSWORD),
        token_version=0,
        role=doctor_role,
        status=inactive_user_status,
        clinic=active_clinic,
    )
    inactive_clinic_user = User(
        name="Usuário de Clínica Inativa",
        email="clinica.inativa@example.com",
        cpf="44444444444",
        password_hash=get_password_hash(CURRENT_PASSWORD),
        token_version=0,
        role=doctor_role,
        status=active_user_status,
        clinic=inactive_clinic,
    )

    db.add_all([doctor, admin, inactive_user, inactive_clinic_user])
    db.commit()

    return AuthData(
        doctor_id=doctor.id,
        admin_id=admin.id,
        inactive_user_id=inactive_user.id,
        inactive_clinic_user_id=inactive_clinic_user.id,
        active_clinic_id=active_clinic.id,
        inactive_clinic_id=inactive_clinic.id,
    )


@pytest.fixture
def api_context() -> Iterator[ApiContext]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    with testing_session_factory() as db:
        data = _seed_auth_data(db)

    def override_get_db() -> Iterator[Session]:
        db = testing_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield ApiContext(
            client=client,
            session_factory=testing_session_factory,
            data=data,
        )

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _login(client: TestClient, email: str, password: str = CURRENT_PASSWORD):
    return client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"user-agent": "pytest-clinicai"},
    )


def _authorization(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _assert_no_credential_fields(payload: dict) -> None:
    serialized = str(payload).lower()
    for forbidden in (
        "password",
        "password_hash",
        "current_password",
        "access_token",
        "refresh_token",
        "authorization",
        "secret_key",
    ):
        assert forbidden not in serialized


def _assert_audit_logs_do_not_contain_credentials(db: Session) -> None:
    for audit_log in db.query(AuditLog).all():
        serialized = str(
            {
                "description": audit_log.description,
                "old_data": audit_log.old_data,
                "new_data": audit_log.new_data,
            }
        ).lower()
        for forbidden in (
            CURRENT_PASSWORD.lower(),
            NEW_PASSWORD.lower(),
            "password_hash",
            "current_password",
            "access_token",
            "refresh_token",
            "authorization",
            "secret_key",
        ):
            assert forbidden not in serialized


def test_login_valido_e_respostas_publicas_nao_expoem_credenciais(
    api_context: ApiContext,
) -> None:
    response = _login(api_context.client, "medico.ativo@clinicai.local")

    assert response.status_code == 200
    token_payload = response.json()
    assert set(token_payload) == {"access_token", "refresh_token", "token_type"}
    assert token_payload["token_type"] == "bearer"

    me_response = api_context.client.get(
        "/auth/me",
        headers=_authorization(token_payload["access_token"]),
    )
    assert me_response.status_code == 200
    _assert_no_credential_fields(me_response.json())

    profile_response = api_context.client.get(
        "/users/me",
        headers=_authorization(token_payload["access_token"]),
    )
    assert profile_response.status_code == 200
    _assert_no_credential_fields(profile_response.json())


def test_login_invalido_nao_enumera_contas_e_registra_tentativas_sanitizadas(
    api_context: ApiContext,
) -> None:
    wrong_password = _login(
        api_context.client,
        "medico.ativo@clinicai.local",
        "SenhaIncorreta123",
    )
    unknown_email = _login(
        api_context.client,
        "nao.existe@clinicai.local",
        "SenhaIncorreta123",
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json() == {
        "detail": "Email ou senha inválidos."
    }

    with api_context.session_factory() as db:
        failures = (
            db.query(AuditLog)
            .filter(AuditLog.action == "login_failed")
            .order_by(AuditLog.id)
            .all()
        )
        assert len(failures) == 2
        assert all(log.ip_address for log in failures)
        assert all(log.user_agent == "pytest-clinicai" for log in failures)
        _assert_audit_logs_do_not_contain_credentials(db)


def test_token_ausente_expirado_tipo_incorreto_e_sub_malformado_retornam_401(
    api_context: ApiContext,
) -> None:
    without_token = api_context.client.get("/auth/me")
    assert without_token.status_code == 401

    with api_context.session_factory() as db:
        user = db.get(User, api_context.data.doctor_id)
        assert user is not None
        token_data = {"sub": str(user.id), "token_version": user.token_version}

        expired_access = create_access_token(
            token_data,
            expires_delta=timedelta(seconds=-1),
        )
        expired_refresh = create_refresh_token(
            token_data,
            expires_delta=timedelta(seconds=-1),
        )
        valid_refresh = create_refresh_token(token_data)
        valid_access = create_access_token(token_data)
        malformed_sub = create_access_token(
            {"sub": "nao-e-inteiro", "token_version": user.token_version}
        )

    assert api_context.client.get(
        "/auth/me", headers=_authorization(expired_access)
    ).status_code == 401
    assert api_context.client.get(
        "/auth/me", headers=_authorization(valid_refresh)
    ).status_code == 401
    assert api_context.client.get(
        "/auth/me", headers=_authorization(malformed_sub)
    ).status_code == 401

    assert api_context.client.post(
        "/auth/refresh", json={"refresh_token": expired_refresh}
    ).status_code == 401
    assert api_context.client.post(
        "/auth/refresh", json={"refresh_token": valid_access}
    ).status_code == 401


def test_refresh_rotaciona_tokens_e_invalida_o_par_anterior(
    api_context: ApiContext,
) -> None:
    login_response = _login(api_context.client, "medico.ativo@clinicai.local")
    old_tokens = login_response.json()

    refresh_response = api_context.client.post(
        "/auth/refresh",
        json={"refresh_token": old_tokens["refresh_token"]},
        headers={"user-agent": "pytest-refresh"},
    )

    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert new_tokens["access_token"] != old_tokens["access_token"]
    assert new_tokens["refresh_token"] != old_tokens["refresh_token"]

    assert api_context.client.get(
        "/auth/me", headers=_authorization(old_tokens["access_token"])
    ).status_code == 401
    assert api_context.client.post(
        "/auth/refresh",
        json={"refresh_token": old_tokens["refresh_token"]},
    ).status_code == 401
    assert api_context.client.get(
        "/auth/me", headers=_authorization(new_tokens["access_token"])
    ).status_code == 200

    with api_context.session_factory() as db:
        refresh_log = (
            db.query(AuditLog)
            .filter(AuditLog.action == "refresh_token")
            .one()
        )
        assert refresh_log.new_data == {"token_version": 1}
        _assert_audit_logs_do_not_contain_credentials(db)


def test_logout_encerra_access_e_refresh_token(
    api_context: ApiContext,
) -> None:
    tokens = _login(api_context.client, "medico.ativo@clinicai.local").json()

    logout_response = api_context.client.post(
        "/auth/logout",
        headers=_authorization(tokens["access_token"]),
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Logout realizado com sucesso."}
    _assert_no_credential_fields(logout_response.json())

    assert api_context.client.get(
        "/auth/me", headers=_authorization(tokens["access_token"])
    ).status_code == 401
    assert api_context.client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    ).status_code == 401


def test_usuario_e_clinica_inativos_sao_recusados_com_403(
    api_context: ApiContext,
) -> None:
    inactive_user_login = _login(
        api_context.client,
        "usuario.inativo@clinicai.local",
    )
    inactive_clinic_login = _login(
        api_context.client,
        "clinica.inativa@example.com",
    )

    assert inactive_user_login.status_code == 403
    assert inactive_user_login.json() == {"detail": "Usuário inativo ou bloqueado."}
    assert inactive_clinic_login.status_code == 403
    assert inactive_clinic_login.json() == {"detail": "Clínica inativa ou bloqueada."}

    with api_context.session_factory() as db:
        inactive_user = db.get(User, api_context.data.inactive_user_id)
        inactive_clinic_user = db.get(User, api_context.data.inactive_clinic_user_id)
        assert inactive_user is not None
        assert inactive_clinic_user is not None
        inactive_user_tokens = create_user_tokens(inactive_user)
        inactive_clinic_tokens = create_user_tokens(inactive_clinic_user)

    assert api_context.client.get(
        "/auth/me",
        headers=_authorization(inactive_user_tokens["access_token"]),
    ).status_code == 403
    assert api_context.client.post(
        "/auth/refresh",
        json={"refresh_token": inactive_clinic_tokens["refresh_token"]},
    ).status_code == 403


def test_inativar_usuario_encerra_sessao_e_impede_reuso_apos_reativacao(
    api_context: ApiContext,
) -> None:
    doctor_tokens = _login(api_context.client, "medico.ativo@clinicai.local").json()
    admin_tokens = _login(api_context.client, "admin@clinicai.local").json()

    inactivate_response = api_context.client.patch(
        f"/users/{api_context.data.doctor_id}/inactivate",
        headers=_authorization(admin_tokens["access_token"]),
    )
    assert inactivate_response.status_code == 200

    assert api_context.client.get(
        "/auth/me", headers=_authorization(doctor_tokens["access_token"])
    ).status_code == 401
    assert _login(
        api_context.client, "medico.ativo@clinicai.local"
    ).status_code == 403

    activate_response = api_context.client.patch(
        f"/users/{api_context.data.doctor_id}/activate",
        headers=_authorization(admin_tokens["access_token"]),
    )
    assert activate_response.status_code == 200

    # A reativação não ressuscita o token emitido antes da inativação.
    assert api_context.client.get(
        "/auth/me", headers=_authorization(doctor_tokens["access_token"])
    ).status_code == 401
    assert _login(api_context.client, "medico.ativo@clinicai.local").status_code == 200


def test_inativar_clinica_encerra_sessoes_dos_usuarios_vinculados(
    api_context: ApiContext,
) -> None:
    doctor_tokens = _login(api_context.client, "medico.ativo@clinicai.local").json()
    admin_tokens = _login(api_context.client, "admin@clinicai.local").json()

    inactivate_response = api_context.client.patch(
        f"/clinics/{api_context.data.active_clinic_id}/inactivate",
        headers=_authorization(admin_tokens["access_token"]),
    )
    assert inactivate_response.status_code == 200

    assert api_context.client.get(
        "/auth/me", headers=_authorization(doctor_tokens["access_token"])
    ).status_code == 401
    assert _login(
        api_context.client, "medico.ativo@clinicai.local"
    ).status_code == 403

    activate_response = api_context.client.patch(
        f"/clinics/{api_context.data.active_clinic_id}/activate",
        headers=_authorization(admin_tokens["access_token"]),
    )
    assert activate_response.status_code == 200

    assert api_context.client.get(
        "/auth/me", headers=_authorization(doctor_tokens["access_token"])
    ).status_code == 401
    assert _login(api_context.client, "medico.ativo@clinicai.local").status_code == 200


def test_troca_da_propria_senha_exige_senha_atual_e_preserva_so_a_sessao_atual(
    api_context: ApiContext,
) -> None:
    old_tokens = _login(api_context.client, "medico.ativo@clinicai.local").json()

    wrong_current = api_context.client.patch(
        "/users/me/password",
        headers=_authorization(old_tokens["access_token"]),
        json={
            "current_password": "SenhaAtualErrada",
            "password": NEW_PASSWORD,
        },
    )
    assert wrong_current.status_code == 400
    assert wrong_current.json() == {"detail": "Senha atual incorreta."}

    password_response = api_context.client.patch(
        "/users/me/password",
        headers=_authorization(old_tokens["access_token"]),
        json={
            "current_password": CURRENT_PASSWORD,
            "password": NEW_PASSWORD,
        },
    )
    assert password_response.status_code == 200
    new_tokens = password_response.json()
    assert set(new_tokens) == {"access_token", "refresh_token", "token_type"}

    assert api_context.client.get(
        "/auth/me", headers=_authorization(old_tokens["access_token"])
    ).status_code == 401
    assert api_context.client.post(
        "/auth/refresh",
        json={"refresh_token": old_tokens["refresh_token"]},
    ).status_code == 401
    assert api_context.client.get(
        "/auth/me", headers=_authorization(new_tokens["access_token"])
    ).status_code == 200

    assert _login(
        api_context.client,
        "medico.ativo@clinicai.local",
        CURRENT_PASSWORD,
    ).status_code == 401
    assert _login(
        api_context.client,
        "medico.ativo@clinicai.local",
        NEW_PASSWORD,
    ).status_code == 200

    with api_context.session_factory() as db:
        _assert_audit_logs_do_not_contain_credentials(db)


def test_reset_administrativo_de_senha_nao_retorna_hash_e_invalida_sessao_alvo(
    api_context: ApiContext,
) -> None:
    doctor_tokens = _login(api_context.client, "medico.ativo@clinicai.local").json()
    admin_tokens = _login(api_context.client, "admin@clinicai.local").json()

    reset_response = api_context.client.patch(
        f"/users/{api_context.data.doctor_id}/password",
        headers=_authorization(admin_tokens["access_token"]),
        json={"password": NEW_PASSWORD},
    )

    assert reset_response.status_code == 200
    _assert_no_credential_fields(reset_response.json())
    assert api_context.client.get(
        "/auth/me", headers=_authorization(doctor_tokens["access_token"])
    ).status_code == 401
    assert _login(
        api_context.client,
        "medico.ativo@clinicai.local",
        NEW_PASSWORD,
    ).status_code == 200
