"""CHK-06 — testes de API e regras de negócio do módulo de clínicas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pytest
from fastapi import HTTPException
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
from app.modules.exams.model import Exam
from app.modules.exams.service import validate_clinic_is_active as validate_exam_clinic_active
from app.modules.patients.model import Patient
from app.modules.patients.service import (
    validate_clinic_is_active as validate_patient_clinic_active,
)
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User
from app.modules.users.service import get_active_clinic_or_none

PASSWORD = "SenhaTeste123"


@dataclass(frozen=True)
class ClinicData:
    admin_id: int
    doctor_a_id: int
    doctor_b_id: int
    clinic_a_id: int
    clinic_b_id: int
    inactive_clinic_id: int
    active_clinic_status_id: int
    inactive_clinic_status_id: int
    active_user_status_id: int
    patient_id: int
    exam_id: int


@dataclass(frozen=True)
class ClinicApiContext:
    client: TestClient
    session_factory: sessionmaker
    data: ClinicData
    admin_headers: dict[str, str]
    doctor_a_headers: dict[str, str]
    doctor_b_headers: dict[str, str]


def _headers(user: User) -> dict[str, str]:
    token = create_user_tokens(user)["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_clinic_data(db: Session) -> tuple[ClinicData, dict[str, str], dict[str, str], dict[str, str]]:
    active_user = Status(name="active", display_name="Ativo", applies_to="user")
    active_clinic = Status(name="active", display_name="Ativa", applies_to="clinic")
    inactive_clinic = Status(name="inactive", display_name="Inativa", applies_to="clinic")
    active_patient = Status(name="active", display_name="Ativo", applies_to="patient")
    processing_exam = Status(
        name="processing",
        display_name="Em processamento",
        applies_to="exam",
    )

    admin_role = Role(
        name="admin_master",
        display_name="Administrador Master",
        permissions_initialized=True,
    )
    doctor_role = Role(
        name="doctor",
        display_name="Médico",
        permissions_initialized=True,
    )

    read_profile = Permission(
        name="clinics:read_profile",
        display_name="Consultar própria clínica",
        module="clinics",
    )
    update_profile = Permission(
        name="clinics:update_profile",
        display_name="Atualizar própria clínica",
        module="clinics",
    )

    clinic_a = Clinic(
        name="Clínica A",
        cnpj="11222333000181",
        email="clinica.a@example.com",
        phone="8833334444",
        mobile_phone="88999998888",
        zip_code="63000000",
        address="Rua A",
        number="10",
        neighborhood="Centro",
        city="Barbalha",
        state="CE",
        status=active_clinic,
    )
    clinic_b = Clinic(
        name="Clínica B",
        cnpj="11444777000161",
        email="clinica.b@example.com",
        status=active_clinic,
    )
    clinic_inactive = Clinic(
        name="Clínica Inativa",
        cnpj="27865757000102",
        email="inativa@example.com",
        status=inactive_clinic,
    )

    db.add_all(
        [
            active_user,
            active_clinic,
            inactive_clinic,
            active_patient,
            processing_exam,
            admin_role,
            doctor_role,
            read_profile,
            update_profile,
            clinic_a,
            clinic_b,
            clinic_inactive,
        ]
    )
    db.flush()

    db.add_all(
        [
            RolePermission(role=doctor_role, permission=read_profile),
            RolePermission(role=doctor_role, permission=update_profile),
        ]
    )

    admin = User(
        name="Administrador",
        email="admin.clinicas@clinicai.local",
        cpf="11144477735",
        password_hash=get_password_hash(PASSWORD),
        token_version=0,
        role=admin_role,
        status=active_user,
        clinic=None,
    )
    doctor_a = User(
        name="Médico A",
        email="medico.a@clinicai.local",
        cpf="52998224725",
        password_hash=get_password_hash(PASSWORD),
        token_version=0,
        role=doctor_role,
        status=active_user,
        clinic=clinic_a,
    )
    doctor_b = User(
        name="Médico B",
        email="medico.b@clinicai.local",
        cpf="16899535009",
        password_hash=get_password_hash(PASSWORD),
        token_version=0,
        role=doctor_role,
        status=active_user,
        clinic=clinic_b,
    )
    db.add_all([admin, doctor_a, doctor_b])
    db.flush()

    patient = Patient(
        name="Paciente da Clínica A",
        cpf="12345678909",
        clinic=clinic_a,
        doctor=doctor_a,
        status=active_patient,
    )
    db.add(patient)
    db.flush()

    exam = Exam(
        exam_type="endoscopy",
        description="Exame preservado",
        clinic=clinic_a,
        patient=patient,
        doctor=doctor_a,
        status=processing_exam,
    )
    db.add(exam)
    db.commit()

    return (
        ClinicData(
            admin_id=admin.id,
            doctor_a_id=doctor_a.id,
            doctor_b_id=doctor_b.id,
            clinic_a_id=clinic_a.id,
            clinic_b_id=clinic_b.id,
            inactive_clinic_id=clinic_inactive.id,
            active_clinic_status_id=active_clinic.id,
            inactive_clinic_status_id=inactive_clinic.id,
            active_user_status_id=active_user.id,
            patient_id=patient.id,
            exam_id=exam.id,
        ),
        _headers(admin),
        _headers(doctor_a),
        _headers(doctor_b),
    )


@pytest.fixture
def clinic_api_context() -> Iterator[ClinicApiContext]:
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
        data, admin_headers, doctor_a_headers, doctor_b_headers = _seed_clinic_data(db)

    def override_get_db() -> Iterator[Session]:
        db = testing_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield ClinicApiContext(
            client=client,
            session_factory=testing_session_factory,
            data=data,
            admin_headers=admin_headers,
            doctor_a_headers=doctor_a_headers,
            doctor_b_headers=doctor_b_headers,
        )

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_admin_crud_and_normalization(clinic_api_context: ClinicApiContext) -> None:
    ctx = clinic_api_context
    payload = {
        "name": "  Clínica Nova  ",
        "cnpj": "19.131.243/0001-97",
        "email": "  CONTATO.NOVA@EXAMPLE.COM  ",
        "phone": "(88) 3333-4444",
        "mobile_phone": "(88) 99999-8888",
        "zip_code": "63.180-000",
        "address": "  Rua Principal  ",
        "number": " 100 ",
        "complement": " Sala 2 ",
        "neighborhood": " Centro ",
        "city": " Barbalha ",
        "state": "ce",
        "status_id": ctx.data.active_clinic_status_id,
    }

    created = ctx.client.post("/clinics/", json=payload, headers=ctx.admin_headers)
    assert created.status_code == 201, created.text
    body = created.json()
    clinic_id = body["id"]
    assert body["name"] == "Clínica Nova"
    assert body["cnpj"] == "19131243000197"
    assert body["email"] == "contato.nova@example.com"
    assert body["phone"] == "8833334444"
    assert body["mobile_phone"] == "88999998888"
    assert body["zip_code"] == "63180000"
    assert body["address"] == "Rua Principal"
    assert body["number"] == "100"
    assert body["state"] == "CE"
    assert body["status_name"] == "active"

    listed = ctx.client.get("/clinics/", headers=ctx.admin_headers)
    assert listed.status_code == 200
    assert clinic_id in {item["id"] for item in listed.json()}

    fetched = ctx.client.get(f"/clinics/{clinic_id}", headers=ctx.admin_headers)
    assert fetched.status_code == 200
    assert fetched.json()["status_display_name"] == "Ativa"

    updated = ctx.client.patch(
        f"/clinics/{clinic_id}",
        json={
            "email": "NOVO.CONTATO@EXAMPLE.COM",
            "phone": "(88) 3222-1111",
            "address": "Avenida Atualizada",
            "city": "Crato",
        },
        headers=ctx.admin_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["email"] == "novo.contato@example.com"
    assert updated.json()["phone"] == "8832221111"
    assert updated.json()["address"] == "Avenida Atualizada"
    assert updated.json()["city"] == "Crato"

    with ctx.session_factory() as db:
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.entity == "clinic", AuditLog.entity_id == clinic_id)
            .order_by(AuditLog.id.asc())
            .all()
        )
        assert [log.action for log in logs] == ["create", "update"]
        assert logs[0].new_data["cnpj"] == "19131243000197"
        assert logs[1].old_data["email"] == "contato.nova@example.com"
        assert logs[1].new_data["email"] == "novo.contato@example.com"


def test_duplicate_cnpj_and_case_insensitive_email_are_rejected(
    clinic_api_context: ClinicApiContext,
) -> None:
    ctx = clinic_api_context
    base = {
        "name": "Clínica Duplicada",
        "cnpj": "45.997.418/0001-53",
        "email": "Duplicada@Example.com",
        "status_id": ctx.data.active_clinic_status_id,
    }
    first = ctx.client.post("/clinics/", json=base, headers=ctx.admin_headers)
    assert first.status_code == 201, first.text

    duplicate_cnpj = ctx.client.post(
        "/clinics/",
        json={**base, "name": "Outro nome", "email": "outro@example.com"},
        headers=ctx.admin_headers,
    )
    assert duplicate_cnpj.status_code == 400
    assert duplicate_cnpj.json()["detail"] == "CNPJ já cadastrado."

    duplicate_email = ctx.client.post(
        "/clinics/",
        json={
            **base,
            "name": "Outro nome",
            "cnpj": "04.252.011/0001-10",
            "email": "DUPLICADA@example.com",
        },
        headers=ctx.admin_headers,
    )
    assert duplicate_email.status_code == 400
    assert duplicate_email.json()["detail"] == "E-mail já cadastrado."


def test_clinic_status_scope_and_logical_deletion_contract(
    clinic_api_context: ClinicApiContext,
) -> None:
    ctx = clinic_api_context

    wrong_scope = ctx.client.post(
        "/clinics/",
        json={
            "name": "Clínica com status incorreto",
            "cnpj": "04.252.011/0001-10",
            "status_id": ctx.data.active_user_status_id,
        },
        headers=ctx.admin_headers,
    )
    assert wrong_scope.status_code == 400
    assert wrong_scope.json()["detail"] == "Status inválido para clinic."

    # O CRUD de clínicas usa exclusão lógica por status; DELETE físico não é exposto.
    delete_response = ctx.client.delete(
        f"/clinics/{ctx.data.clinic_b_id}",
        headers=ctx.admin_headers,
    )
    assert delete_response.status_code == 405


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("cnpj", "00.000.000/0000-00"),
        ("phone", "123"),
        ("zip_code", "12345"),
        ("state", "Ceará"),
    ),
)
def test_invalid_cnpj_contact_or_address_returns_422(
    clinic_api_context: ClinicApiContext,
    field: str,
    value: str,
) -> None:
    ctx = clinic_api_context
    payload = {
        "name": "Clínica Inválida",
        "cnpj": "19.131.243/0001-97",
        "email": "valida@example.com",
        "phone": "(88) 3333-4444",
        "zip_code": "63.180-000",
        "state": "CE",
        "status_id": ctx.data.active_clinic_status_id,
        field: value,
    }
    response = ctx.client.post("/clinics/", json=payload, headers=ctx.admin_headers)
    assert response.status_code == 422


def test_status_can_only_change_through_dedicated_routes(
    clinic_api_context: ClinicApiContext,
) -> None:
    ctx = clinic_api_context

    forbidden_patch = ctx.client.patch(
        f"/clinics/{ctx.data.clinic_a_id}",
        json={"status_id": ctx.data.inactive_clinic_status_id},
        headers=ctx.admin_headers,
    )
    assert forbidden_patch.status_code == 422
    assert forbidden_patch.json()["detail"][0]["type"] == "extra_forbidden"

    inactivated = ctx.client.patch(
        f"/clinics/{ctx.data.clinic_a_id}/inactivate",
        headers=ctx.admin_headers,
    )
    assert inactivated.status_code == 200, inactivated.text
    assert inactivated.json()["status_name"] == "inactive"

    with ctx.session_factory() as db:
        doctor = db.get(User, ctx.data.doctor_a_id)
        patient = db.get(Patient, ctx.data.patient_id)
        exam = db.get(Exam, ctx.data.exam_id)
        log = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity == "clinic",
                AuditLog.entity_id == ctx.data.clinic_a_id,
                AuditLog.action == "change_status_inactivate",
            )
            .one()
        )
        assert doctor.token_version == 1
        assert patient.clinic_id == ctx.data.clinic_a_id
        assert exam.clinic_id == ctx.data.clinic_a_id
        assert patient.status.name == "active"
        assert exam.status.name == "processing"
        assert log.new_data["associated_users"] == 1
        assert log.new_data["associated_patients"] == 1
        assert log.new_data["associated_exams"] == 1
        assert log.new_data["related_records_preserved"] is True

        with pytest.raises(HTTPException) as patient_error:
            validate_patient_clinic_active(db, ctx.data.clinic_a_id)
        assert patient_error.value.status_code == 400

        with pytest.raises(HTTPException) as exam_error:
            validate_exam_clinic_active(db, ctx.data.clinic_a_id)
        assert exam_error.value.status_code == 400

        with pytest.raises(HTTPException) as user_error:
            get_active_clinic_or_none(db, ctx.data.clinic_a_id)
        assert user_error.value.status_code == 400

    old_session = ctx.client.get("/clinics/me", headers=ctx.doctor_a_headers)
    assert old_session.status_code == 401

    login = ctx.client.post(
        "/auth/login",
        data={"username": "medico.a@clinicai.local", "password": PASSWORD},
    )
    assert login.status_code == 403

    # Repetir a mesma inativação é idempotente: não invalida a sessão novamente
    # nem cria um segundo evento de auditoria.
    repeated = ctx.client.patch(
        f"/clinics/{ctx.data.clinic_a_id}/inactivate",
        headers=ctx.admin_headers,
    )
    assert repeated.status_code == 200
    with ctx.session_factory() as db:
        doctor = db.get(User, ctx.data.doctor_a_id)
        count = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity == "clinic",
                AuditLog.entity_id == ctx.data.clinic_a_id,
                AuditLog.action == "change_status_inactivate",
            )
            .count()
        )
        assert doctor.token_version == 1
        assert count == 1

    activated = ctx.client.patch(
        f"/clinics/{ctx.data.clinic_a_id}/activate",
        headers=ctx.admin_headers,
    )
    assert activated.status_code == 200
    assert activated.json()["status_name"] == "active"


def test_user_reads_and_edits_only_own_clinic(
    clinic_api_context: ClinicApiContext,
) -> None:
    ctx = clinic_api_context

    own = ctx.client.get("/clinics/me", headers=ctx.doctor_a_headers)
    assert own.status_code == 200, own.text
    assert own.json()["id"] == ctx.data.clinic_a_id
    assert own.json()["status_name"] == "active"
    assert own.json()["status_display_name"] == "Ativa"

    updated = ctx.client.patch(
        "/clinics/me",
        json={
            "phone": "(88) 3555-1212",
            "address": "Rua da Própria Clínica",
            "city": "Barbalha",
        },
        headers=ctx.doctor_a_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["id"] == ctx.data.clinic_a_id
    assert updated.json()["phone"] == "8835551212"

    change_status = ctx.client.patch(
        "/clinics/me",
        json={"status_id": ctx.data.inactive_clinic_status_id},
        headers=ctx.doctor_a_headers,
    )
    assert change_status.status_code == 422

    read_other = ctx.client.get(
        f"/clinics/{ctx.data.clinic_b_id}",
        headers=ctx.doctor_a_headers,
    )
    assert read_other.status_code == 403

    update_other = ctx.client.patch(
        f"/clinics/{ctx.data.clinic_b_id}",
        json={"phone": "88999990000"},
        headers=ctx.doctor_a_headers,
    )
    assert update_other.status_code == 403

    with ctx.session_factory() as db:
        clinic_a = db.get(Clinic, ctx.data.clinic_a_id)
        clinic_b = db.get(Clinic, ctx.data.clinic_b_id)
        assert clinic_a.phone == "8835551212"
        assert clinic_b.phone is None


def test_non_admin_cannot_use_admin_clinic_operations(
    clinic_api_context: ClinicApiContext,
) -> None:
    ctx = clinic_api_context
    responses = (
        ctx.client.get("/clinics/", headers=ctx.doctor_b_headers),
        ctx.client.post(
            "/clinics/",
            json={
                "name": "Clínica Indevida",
                "cnpj": "04.252.011/0001-10",
                "status_id": ctx.data.active_clinic_status_id,
            },
            headers=ctx.doctor_b_headers,
        ),
        ctx.client.patch(
            f"/clinics/{ctx.data.clinic_a_id}/inactivate",
            headers=ctx.doctor_b_headers,
        ),
        ctx.client.patch(
            f"/clinics/{ctx.data.clinic_a_id}/activate",
            headers=ctx.doctor_b_headers,
        ),
    )
    assert all(response.status_code == 403 for response in responses)
