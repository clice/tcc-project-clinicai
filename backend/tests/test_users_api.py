"""CHK-07 — testes de invariantes e exposição do módulo de usuários."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.modules.audit_logs.model import AuditLog
from app.modules.auth.service import create_user_tokens
from app.modules.clinics.model import Clinic
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User

PASSWORD = "SenhaTeste123"
NEW_PASSWORD = "NovaSenha456"


@dataclass(frozen=True)
class UserData:
    admin_a_id: int
    admin_b_id: int
    doctor_a_id: int
    staff_a_id: int
    doctor_b_id: int
    inactive_doctor_id: int
    admin_role_id: int
    doctor_role_id: int
    staff_role_id: int
    active_user_status_id: int
    inactive_user_status_id: int
    active_clinic_status_id: int
    inactive_clinic_status_id: int
    clinic_a_id: int
    clinic_b_id: int
    inactive_clinic_id: int


@dataclass(frozen=True)
class UserApiContext:
    client: TestClient
    session_factory: sessionmaker
    data: UserData
    admin_a_headers: dict[str, str]
    admin_b_headers: dict[str, str]
    doctor_a_headers: dict[str, str]
    staff_a_headers: dict[str, str]
    doctor_b_headers: dict[str, str]


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_user_tokens(user)['access_token']}"}


def _seed_users(db: Session) -> tuple[UserData, dict[str, dict[str, str]]]:
    active_user = Status(name="active", display_name="Ativo", applies_to="user")
    inactive_user = Status(name="inactive", display_name="Inativo", applies_to="user")
    active_clinic = Status(name="active", display_name="Ativa", applies_to="clinic")
    inactive_clinic = Status(name="inactive", display_name="Inativa", applies_to="clinic")

    admin_role = Role(name="admin_master", display_name="Administrador Master", permissions_initialized=True)
    doctor_role = Role(name="doctor", display_name="Médico", permissions_initialized=True)
    staff_role = Role(name="clinic_manager", display_name="Funcionário", permissions_initialized=True)

    users_create = Permission(name="users:create", display_name="Criar usuários", module="users")
    users_read = Permission(name="users:read", display_name="Consultar usuários", module="users")
    users_update = Permission(name="users:update", display_name="Atualizar usuários", module="users")
    users_change_status = Permission(name="users:change_status", display_name="Alterar status", module="users")
    read_profile = Permission(name="users:read_profile", display_name="Consultar perfil", module="users")
    update_profile = Permission(name="users:update_profile", display_name="Atualizar perfil", module="users")
    patients_read = Permission(name="patients:read", display_name="Consultar pacientes", module="patients")

    clinic_a = Clinic(name="Clínica A", cnpj="11222333000181", status=active_clinic)
    clinic_b = Clinic(name="Clínica B", cnpj="11444777000161", status=active_clinic)
    clinic_inactive = Clinic(name="Clínica Inativa", cnpj="27865757000102", status=inactive_clinic)

    db.add_all([
        active_user,
        inactive_user,
        active_clinic,
        inactive_clinic,
        admin_role,
        doctor_role,
        staff_role,
        users_create,
        users_read,
        users_update,
        users_change_status,
        read_profile,
        update_profile,
        patients_read,
        clinic_a,
        clinic_b,
        clinic_inactive,
    ])
    db.flush()

    db.add_all([
        RolePermission(role=doctor_role, permission=read_profile),
        RolePermission(role=doctor_role, permission=update_profile),
        RolePermission(role=doctor_role, permission=patients_read),
        RolePermission(role=staff_role, permission=users_create),
        RolePermission(role=staff_role, permission=users_read),
        RolePermission(role=staff_role, permission=users_update),
        RolePermission(role=staff_role, permission=users_change_status),
        RolePermission(role=staff_role, permission=read_profile),
        RolePermission(role=staff_role, permission=update_profile),
        RolePermission(role=staff_role, permission=patients_read),
    ])

    admin_a = User(
        name="Admin A",
        email="admin.a@example.com",
        cpf="11144477735",
        password_hash=get_password_hash(PASSWORD),
        role=admin_role,
        status=active_user,
    )
    admin_b = User(
        name="Admin B",
        email="admin.b@example.com",
        cpf="52998224725",
        password_hash=get_password_hash(PASSWORD),
        role=admin_role,
        status=active_user,
    )
    doctor_a = User(
        name="Médico A",
        email="medico.a@example.com",
        cpf="16899535009",
        password_hash=get_password_hash(PASSWORD),
        role=doctor_role,
        status=active_user,
        clinic=clinic_a,
    )
    staff_a = User(
        name="Funcionário A",
        email="funcionario.a@example.com",
        cpf="12345678909",
        password_hash=get_password_hash(PASSWORD),
        role=staff_role,
        status=active_user,
        clinic=clinic_a,
    )
    doctor_b = User(
        name="Médico B",
        email="medico.b@example.com",
        cpf="98765432100",
        password_hash=get_password_hash(PASSWORD),
        role=doctor_role,
        status=active_user,
        clinic=clinic_b,
    )
    inactive_doctor = User(
        name="Médico Inativo",
        email="medico.inativo@example.com",
        cpf="39053344705",
        password_hash=get_password_hash(PASSWORD),
        role=doctor_role,
        status=inactive_user,
        clinic=clinic_a,
    )
    db.add_all([admin_a, admin_b, doctor_a, staff_a, doctor_b, inactive_doctor])
    db.commit()

    headers = {
        "admin_a": _headers(admin_a),
        "admin_b": _headers(admin_b),
        "doctor_a": _headers(doctor_a),
        "staff_a": _headers(staff_a),
        "doctor_b": _headers(doctor_b),
    }
    return (
        UserData(
            admin_a_id=admin_a.id,
            admin_b_id=admin_b.id,
            doctor_a_id=doctor_a.id,
            staff_a_id=staff_a.id,
            doctor_b_id=doctor_b.id,
            inactive_doctor_id=inactive_doctor.id,
            admin_role_id=admin_role.id,
            doctor_role_id=doctor_role.id,
            staff_role_id=staff_role.id,
            active_user_status_id=active_user.id,
            inactive_user_status_id=inactive_user.id,
            active_clinic_status_id=active_clinic.id,
            inactive_clinic_status_id=inactive_clinic.id,
            clinic_a_id=clinic_a.id,
            clinic_b_id=clinic_b.id,
            inactive_clinic_id=clinic_inactive.id,
        ),
        headers,
    )


@pytest.fixture
def user_api_context() -> Iterator[UserApiContext]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    with factory() as db:
        data, headers = _seed_users(db)

    def override_get_db() -> Iterator[Session]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield UserApiContext(
            client=client,
            session_factory=factory,
            data=data,
            admin_a_headers=headers["admin_a"],
            admin_b_headers=headers["admin_b"],
            doctor_a_headers=headers["doctor_a"],
            staff_a_headers=headers["staff_a"],
            doctor_b_headers=headers["doctor_b"],
        )

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _create_payload(ctx: UserApiContext, **overrides) -> dict:
    payload = {
        "name": "Novo Médico",
        "email": "novo.medico@example.com",
        "cpf": "86288366757",
        "phone": "(88) 99999-0000",
        "password": PASSWORD,
        "role_id": ctx.data.doctor_role_id,
        "status_id": ctx.data.active_user_status_id,
        "clinic_id": ctx.data.clinic_a_id,
    }
    payload.update(overrides)
    return payload


def test_admin_crud_normalization_and_safe_response(user_api_context: UserApiContext) -> None:
    ctx = user_api_context
    response = ctx.client.post(
        "/users/",
        json=_create_payload(
            ctx,
            name="  Novo Médico  ",
            email="  NOVO.MEDICO@EXAMPLE.COM  ",
            cpf="862.883.667-57",
            phone="(88) 99999-0000",
        ),
        headers=ctx.admin_a_headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    user_id = body["id"]
    assert body["name"] == "Novo Médico"
    assert body["email"] == "novo.medico@example.com"
    assert body["cpf"] == "86288366757"
    assert body["phone"] == "88999990000"
    assert {"password", "password_hash", "token_version"}.isdisjoint(body)

    listed = ctx.client.get("/users/", headers=ctx.admin_a_headers)
    assert listed.status_code == 200
    assert user_id in {item["id"] for item in listed.json()}

    fetched = ctx.client.get(f"/users/{user_id}", headers=ctx.admin_a_headers)
    assert fetched.status_code == 200
    assert fetched.json()["clinic_name"] == "Clínica A"
    assert {"password", "password_hash", "token_version"}.isdisjoint(fetched.json())


def test_email_and_cpf_are_unique_in_create_and_update(user_api_context: UserApiContext) -> None:
    ctx = user_api_context
    duplicate_email = ctx.client.post(
        "/users/",
        json=_create_payload(ctx, email="MEDICO.A@EXAMPLE.COM"),
        headers=ctx.admin_a_headers,
    )
    assert duplicate_email.status_code == 400
    assert duplicate_email.json()["detail"] == "E-mail já cadastrado."

    duplicate_cpf = ctx.client.post(
        "/users/",
        json=_create_payload(ctx, email="outro@example.com", cpf="168.995.350-09"),
        headers=ctx.admin_a_headers,
    )
    assert duplicate_cpf.status_code == 400
    assert duplicate_cpf.json()["detail"] == "CPF já cadastrado."

    update = ctx.client.patch(
        f"/users/{ctx.data.staff_a_id}",
        json={"email": "MEDICO.A@EXAMPLE.COM"},
        headers=ctx.admin_a_headers,
    )
    assert update.status_code == 400

    for required_field in ("name", "email", "cpf", "role_id"):
        invalid = ctx.client.patch(
            f"/users/{ctx.data.staff_a_id}",
            json={required_field: None},
            headers=ctx.admin_a_headers,
        )
        assert invalid.status_code == 400, (required_field, invalid.text)


def test_role_clinic_invariants_are_enforced_by_api(user_api_context: UserApiContext) -> None:
    ctx = user_api_context
    cases = (
        _create_payload(ctx, role_id=ctx.data.admin_role_id, clinic_id=ctx.data.clinic_a_id),
        _create_payload(ctx, clinic_id=None),
        _create_payload(ctx, clinic_id=ctx.data.inactive_clinic_id),
    )
    for payload in cases:
        response = ctx.client.post("/users/", json=payload, headers=ctx.admin_a_headers)
        assert response.status_code == 400, response.text

    invalid_promotion = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}",
        json={"role_id": ctx.data.admin_role_id},
        headers=ctx.admin_a_headers,
    )
    assert invalid_promotion.status_code == 400

    promoted = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}",
        json={"role_id": ctx.data.admin_role_id, "clinic_id": None},
        headers=ctx.admin_a_headers,
    )
    assert promoted.status_code == 200, promoted.text
    assert promoted.json()["role_id"] == ctx.data.admin_role_id
    assert promoted.json()["clinic_id"] is None

    invalid_demotion = ctx.client.patch(
        f"/users/{ctx.data.admin_b_id}",
        json={"role_id": ctx.data.doctor_role_id},
        headers=ctx.admin_a_headers,
    )
    assert invalid_demotion.status_code == 400

    demoted = ctx.client.patch(
        f"/users/{ctx.data.admin_b_id}",
        json={"role_id": ctx.data.doctor_role_id, "clinic_id": ctx.data.clinic_b_id},
        headers=ctx.admin_a_headers,
    )
    assert demoted.status_code == 200, demoted.text
    assert demoted.json()["clinic_id"] == ctx.data.clinic_b_id


def test_role_or_clinic_change_revokes_existing_session_and_is_audited(
    user_api_context: UserApiContext,
) -> None:
    ctx = user_api_context
    changed = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}",
        json={"clinic_id": ctx.data.clinic_b_id},
        headers=ctx.admin_a_headers,
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["clinic_id"] == ctx.data.clinic_b_id

    old_session = ctx.client.get("/users/me", headers=ctx.doctor_a_headers)
    assert old_session.status_code == 401

    with ctx.session_factory() as db:
        user = db.get(User, ctx.data.doctor_a_id)
        log = (
            db.query(AuditLog)
            .filter(AuditLog.entity == "user", AuditLog.entity_id == user.id, AuditLog.action == "update")
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert user.token_version == 1
        assert log is not None
        assert log.old_data["clinic_id"] == ctx.data.clinic_a_id
        assert log.new_data["clinic_id"] == ctx.data.clinic_b_id
        assert log.new_data["security_context_changed"] is True
        assert log.new_data["token_version"] == 1


def test_self_edit_accepts_only_profile_fields(user_api_context: UserApiContext) -> None:
    ctx = user_api_context
    updated = ctx.client.patch(
        "/users/me",
        json={
            "name": " Médico Atualizado ",
            "email": "MEDICO.ATUALIZADO@EXAMPLE.COM",
            "cpf": "168.995.350-09",
            "phone": "(88) 98888-7777",
        },
        headers=ctx.doctor_a_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Médico Atualizado"
    assert updated.json()["email"] == "medico.atualizado@example.com"
    assert updated.json()["phone"] == "88988887777"

    for forbidden_field, value in (
        ("role_id", ctx.data.staff_role_id),
        ("clinic_id", ctx.data.clinic_b_id),
        ("status_id", ctx.data.inactive_user_status_id),
    ):
        response = ctx.client.patch(
            "/users/me",
            json={forbidden_field: value},
            headers=ctx.doctor_a_headers,
        )
        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_status_uses_dedicated_routes_and_revokes_session(user_api_context: UserApiContext) -> None:
    ctx = user_api_context
    generic = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}",
        json={"status_id": ctx.data.inactive_user_status_id},
        headers=ctx.admin_a_headers,
    )
    assert generic.status_code == 422

    inactivated = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}/inactivate",
        headers=ctx.admin_a_headers,
    )
    assert inactivated.status_code == 200
    assert inactivated.json()["status_name"] == "inactive"
    assert ctx.client.get("/users/me", headers=ctx.doctor_a_headers).status_code == 401

    repeated = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}/inactivate",
        headers=ctx.admin_a_headers,
    )
    assert repeated.status_code == 200
    with ctx.session_factory() as db:
        user = db.get(User, ctx.data.doctor_a_id)
        count = db.query(AuditLog).filter(
            AuditLog.entity == "user",
            AuditLog.entity_id == user.id,
            AuditLog.action == "change_status_inactivate",
        ).count()
        assert user.token_version == 1
        assert count == 1

    activated = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}/activate",
        headers=ctx.admin_a_headers,
    )
    assert activated.status_code == 200
    assert activated.json()["status_name"] == "active"


def test_user_cannot_be_activated_with_inactive_clinic(user_api_context: UserApiContext) -> None:
    ctx = user_api_context
    with ctx.session_factory() as db:
        user = db.get(User, ctx.data.inactive_doctor_id)
        user.clinic_id = ctx.data.inactive_clinic_id
        db.commit()

    response = ctx.client.patch(
        f"/users/{ctx.data.inactive_doctor_id}/activate",
        headers=ctx.admin_a_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Clínica não encontrada ou não está ativa."


def test_last_active_admin_is_protected(user_api_context: UserApiContext) -> None:
    ctx = user_api_context
    first = ctx.client.patch(
        f"/users/{ctx.data.admin_b_id}/inactivate",
        headers=ctx.admin_a_headers,
    )
    assert first.status_code == 200

    last = ctx.client.patch(
        f"/users/{ctx.data.admin_a_id}/inactivate",
        headers=ctx.admin_a_headers,
    )
    assert last.status_code == 400
    assert last.json()["detail"] == "Não é permitido remover ou inativar o último administrador master ativo."


def test_doctor_selector_is_minimal_and_tenant_scoped(user_api_context: UserApiContext) -> None:
    ctx = user_api_context
    own = ctx.client.get(
        "/users/doctors",
        params={"clinic_id": ctx.data.clinic_a_id},
        headers=ctx.staff_a_headers,
    )
    assert own.status_code == 200, own.text
    assert own.json()
    assert all(set(item) == {"id", "name"} for item in own.json())
    assert ctx.data.doctor_a_id in {item["id"] for item in own.json()}

    other = ctx.client.get(
        "/users/doctors",
        params={"clinic_id": ctx.data.clinic_b_id},
        headers=ctx.staff_a_headers,
    )
    assert other.status_code == 403


def test_password_flows_revoke_tokens_without_exposing_credentials(
    user_api_context: UserApiContext,
) -> None:
    ctx = user_api_context
    wrong = ctx.client.patch(
        "/users/me/password",
        json={"current_password": "incorreta", "password": NEW_PASSWORD},
        headers=ctx.doctor_a_headers,
    )
    assert wrong.status_code == 400

    changed = ctx.client.patch(
        "/users/me/password",
        json={"current_password": PASSWORD, "password": NEW_PASSWORD},
        headers=ctx.doctor_a_headers,
    )
    assert changed.status_code == 200, changed.text
    assert set(changed.json()) == {"access_token", "refresh_token", "token_type"}
    assert ctx.client.get("/users/me", headers=ctx.doctor_a_headers).status_code == 401

    reset = ctx.client.patch(
        f"/users/{ctx.data.staff_a_id}/password",
        json={"password": NEW_PASSWORD},
        headers=ctx.admin_a_headers,
    )
    assert reset.status_code == 200, reset.text
    assert {"password", "password_hash", "token_version", "access_token", "refresh_token"}.isdisjoint(reset.json())

    with ctx.session_factory() as db:
        logs = db.query(AuditLog).filter(AuditLog.entity == "user").all()
        serialized = repr([(log.old_data, log.new_data) for log in logs]).lower()
        assert "current_password" not in serialized
        assert PASSWORD.lower() not in serialized
        assert NEW_PASSWORD.lower() not in serialized


def test_clinic_manager_manages_only_doctors_from_own_clinic(
    user_api_context: UserApiContext,
) -> None:
    ctx = user_api_context
    manager_headers = ctx.staff_a_headers

    options = ctx.client.get(
        "/users/doctor-management-options",
        headers=manager_headers,
    )
    assert options.status_code == 200, options.text
    options_body = options.json()
    assert options_body["role"] == {
        "id": ctx.data.doctor_role_id,
        "name": "doctor",
        "display_name": "Médico",
    }
    assert options_body["clinic"]["id"] == ctx.data.clinic_a_id
    assert options_body["clinic"]["name"] == "Clínica A"
    assert {
        status["name"]
        for status in options_body["statuses"]
    } == {"active", "inactive"}

    doctor_options = ctx.client.get(
        "/users/doctor-management-options",
        headers=ctx.doctor_a_headers,
    )
    assert doctor_options.status_code == 403

    own_list = ctx.client.get(
        "/users/",
        headers=manager_headers,
    )
    assert own_list.status_code == 200, own_list.text
    own_items = own_list.json()
    assert ctx.data.doctor_a_id in {
        item["id"] for item in own_items
    }
    assert ctx.data.staff_a_id not in {
        item["id"] for item in own_items
    }
    assert ctx.data.doctor_b_id not in {
        item["id"] for item in own_items
    }
    assert all(
        item["role_name"] == "doctor"
        and item["clinic_id"] == ctx.data.clinic_a_id
        for item in own_items
    )

    cross_clinic_list = ctx.client.get(
        "/users/",
        params={"clinic_id": ctx.data.clinic_b_id},
        headers=manager_headers,
    )
    assert cross_clinic_list.status_code == 403

    non_doctor_list = ctx.client.get(
        "/users/",
        params={"role": "clinic_manager"},
        headers=manager_headers,
    )
    assert non_doctor_list.status_code == 403

    own_doctor = ctx.client.get(
        f"/users/{ctx.data.doctor_a_id}",
        headers=manager_headers,
    )
    assert own_doctor.status_code == 200

    for forbidden_user_id in (
        ctx.data.doctor_b_id,
        ctx.data.staff_a_id,
        ctx.data.admin_a_id,
    ):
        forbidden = ctx.client.get(
            f"/users/{forbidden_user_id}",
            headers=manager_headers,
        )
        assert forbidden.status_code == 403

    wrong_clinic = ctx.client.post(
        "/users/",
        json=_create_payload(
            ctx,
            clinic_id=ctx.data.clinic_b_id,
        ),
        headers=manager_headers,
    )
    assert wrong_clinic.status_code == 403

    wrong_role = ctx.client.post(
        "/users/",
        json=_create_payload(
            ctx,
            role_id=ctx.data.staff_role_id,
        ),
        headers=manager_headers,
    )
    assert wrong_role.status_code == 403

    created = ctx.client.post(
        "/users/",
        json=_create_payload(ctx),
        headers=manager_headers,
    )
    assert created.status_code == 201, created.text
    created_body = created.json()
    created_id = created_body["id"]
    assert created_body["role_name"] == "doctor"
    assert created_body["clinic_id"] == ctx.data.clinic_a_id

    updated = ctx.client.patch(
        f"/users/{created_id}",
        json={
            "name": "Médico Gerenciado",
            "phone": "(88) 98888-1111",
        },
        headers=manager_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Médico Gerenciado"

    forbidden_role_change = ctx.client.patch(
        f"/users/{created_id}",
        json={"role_id": ctx.data.staff_role_id},
        headers=manager_headers,
    )
    assert forbidden_role_change.status_code == 403

    reset = ctx.client.patch(
        f"/users/{created_id}/password",
        json={"password": NEW_PASSWORD},
        headers=manager_headers,
    )
    assert reset.status_code == 200, reset.text

    inactivated = ctx.client.patch(
        f"/users/{created_id}/inactivate",
        headers=manager_headers,
    )
    assert inactivated.status_code == 200
    assert inactivated.json()["status_name"] == "inactive"

    activated = ctx.client.patch(
        f"/users/{created_id}/activate",
        headers=manager_headers,
    )
    assert activated.status_code == 200
    assert activated.json()["status_name"] == "active"

    forbidden_status_change = ctx.client.patch(
        f"/users/{ctx.data.doctor_b_id}/inactivate",
        headers=manager_headers,
    )
    assert forbidden_status_change.status_code == 403
