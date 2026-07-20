"""CHK-08 — testes de escopo, vínculos e transferência de pacientes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
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
from app.modules.exams.model import Exam
from app.modules.patients.model import Patient
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User

PASSWORD = "SenhaTeste123"


@dataclass(frozen=True)
class PatientData:
    admin_id: int
    doctor_a_id: int
    doctor_a2_id: int
    manager_a_id: int
    doctor_b_id: int
    manager_b_id: int
    inactive_doctor_a_id: int
    doctor_inactive_clinic_id: int
    admin_role_id: int
    doctor_role_id: int
    manager_role_id: int
    clinic_a_id: int
    clinic_b_id: int
    inactive_clinic_id: int
    active_patient_status_id: int
    inactive_patient_status_id: int
    patient_a1_id: int
    patient_a2_id: int
    patient_b_id: int
    patient_with_exam_id: int
    inactive_valid_patient_id: int
    inactive_bad_doctor_patient_id: int
    inactive_bad_clinic_patient_id: int


@dataclass(frozen=True)
class PatientApiContext:
    client: TestClient
    session_factory: sessionmaker
    data: PatientData
    admin_headers: dict[str, str]
    doctor_a_headers: dict[str, str]
    doctor_a2_headers: dict[str, str]
    manager_a_headers: dict[str, str]
    doctor_b_headers: dict[str, str]
    manager_b_headers: dict[str, str]


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_user_tokens(user)['access_token']}"}


def _seed_patients(db: Session) -> tuple[PatientData, dict[str, dict[str, str]]]:
    active_user = Status(name="active", display_name="Ativo", applies_to="user")
    inactive_user = Status(name="inactive", display_name="Inativo", applies_to="user")
    active_clinic = Status(name="active", display_name="Ativa", applies_to="clinic")
    inactive_clinic = Status(name="inactive", display_name="Inativa", applies_to="clinic")
    active_patient = Status(name="active", display_name="Ativo", applies_to="patient")
    inactive_patient = Status(name="inactive", display_name="Inativo", applies_to="patient")
    processing_exam = Status(name="processing", display_name="Processando", applies_to="exam")

    admin_role = Role(name="admin_master", display_name="Administrador Master", permissions_initialized=True)
    doctor_role = Role(name="doctor", display_name="Médico", permissions_initialized=True)
    manager_role = Role(name="clinic_manager", display_name="Gestor", permissions_initialized=True)

    permissions = [
        Permission(name="patients:create", display_name="Cadastrar pacientes", module="patients"),
        Permission(name="patients:read", display_name="Consultar pacientes", module="patients"),
        Permission(name="patients:update", display_name="Atualizar pacientes", module="patients"),
        Permission(name="patients:change_status", display_name="Alterar status", module="patients"),
    ]

    clinic_a = Clinic(name="Clínica A", cnpj="11222333000181", status=active_clinic)
    clinic_b = Clinic(name="Clínica B", cnpj="11444777000161", status=active_clinic)
    clinic_inactive = Clinic(name="Clínica Inativa", cnpj="27865757000102", status=inactive_clinic)

    db.add_all([
        active_user,
        inactive_user,
        active_clinic,
        inactive_clinic,
        active_patient,
        inactive_patient,
        processing_exam,
        admin_role,
        doctor_role,
        manager_role,
        *permissions,
        clinic_a,
        clinic_b,
        clinic_inactive,
    ])
    db.flush()

    for role in (doctor_role, manager_role):
        db.add_all([RolePermission(role=role, permission=permission) for permission in permissions])

    admin = User(
        name="Administrador",
        email="admin.pacientes@example.com",
        cpf="11144477735",
        password_hash=get_password_hash(PASSWORD),
        role=admin_role,
        status=active_user,
    )
    doctor_a = User(
        name="Médico A",
        email="medico.a.pacientes@example.com",
        cpf="52998224725",
        password_hash=get_password_hash(PASSWORD),
        role=doctor_role,
        status=active_user,
        clinic=clinic_a,
    )
    doctor_a2 = User(
        name="Médico A2",
        email="medico.a2.pacientes@example.com",
        cpf="16899535009",
        password_hash=get_password_hash(PASSWORD),
        role=doctor_role,
        status=active_user,
        clinic=clinic_a,
    )
    manager_a = User(
        name="Gestor A",
        email="manager.a.pacientes@example.com",
        cpf="12345678909",
        password_hash=get_password_hash(PASSWORD),
        role=manager_role,
        status=active_user,
        clinic=clinic_a,
    )
    doctor_b = User(
        name="Médico B",
        email="medico.b.pacientes@example.com",
        cpf="98765432100",
        password_hash=get_password_hash(PASSWORD),
        role=doctor_role,
        status=active_user,
        clinic=clinic_b,
    )
    manager_b = User(
        name="Gestor B",
        email="manager.b.pacientes@example.com",
        cpf="39053344705",
        password_hash=get_password_hash(PASSWORD),
        role=manager_role,
        status=active_user,
        clinic=clinic_b,
    )
    inactive_doctor_a = User(
        name="Médico Inativo A",
        email="medico.inativo.a@example.com",
        cpf="93541134780",
        password_hash=get_password_hash(PASSWORD),
        role=doctor_role,
        status=inactive_user,
        clinic=clinic_a,
    )
    doctor_inactive_clinic = User(
        name="Médico Clínica Inativa",
        email="medico.clinica.inativa@example.com",
        cpf="86288366757",
        password_hash=get_password_hash(PASSWORD),
        role=doctor_role,
        status=active_user,
        clinic=clinic_inactive,
    )
    db.add_all([
        admin,
        doctor_a,
        doctor_a2,
        manager_a,
        doctor_b,
        manager_b,
        inactive_doctor_a,
        doctor_inactive_clinic,
    ])
    db.flush()

    patient_a1 = Patient(
        clinic=clinic_a,
        doctor=doctor_a,
        status=active_patient,
        name="Paciente A1",
        cpf="52998224725",
        birth_date=date(1990, 1, 10),
    )
    patient_a2 = Patient(
        clinic=clinic_a,
        doctor=doctor_a2,
        status=active_patient,
        name="Paciente A2",
        cpf="16899535009",
        birth_date=date(1985, 5, 20),
    )
    patient_b = Patient(
        clinic=clinic_b,
        doctor=doctor_b,
        status=active_patient,
        name="Paciente B",
        cpf="52998224725",
        birth_date=date(1975, 8, 5),
    )
    patient_with_exam = Patient(
        clinic=clinic_a,
        doctor=doctor_a,
        status=active_patient,
        name="Paciente com Exame",
        cpf="12345678909",
        birth_date=date(2000, 2, 2),
    )
    inactive_valid = Patient(
        clinic=clinic_a,
        doctor=doctor_a2,
        status=inactive_patient,
        name="Paciente Inativo Válido",
        cpf="98765432100",
    )
    inactive_bad_doctor = Patient(
        clinic=clinic_a,
        doctor=inactive_doctor_a,
        status=inactive_patient,
        name="Paciente Médico Inativo",
        cpf="39053344705",
    )
    inactive_bad_clinic = Patient(
        clinic=clinic_inactive,
        doctor=doctor_inactive_clinic,
        status=inactive_patient,
        name="Paciente Clínica Inativa",
        cpf="93541134780",
    )
    db.add_all([
        patient_a1,
        patient_a2,
        patient_b,
        patient_with_exam,
        inactive_valid,
        inactive_bad_doctor,
        inactive_bad_clinic,
    ])
    db.flush()

    db.add(
        Exam(
            clinic=clinic_a,
            patient=patient_with_exam,
            doctor=doctor_a,
            status=processing_exam,
            exam_type="endoscopy",
            description="Exame existente",
        )
    )
    db.commit()

    headers = {
        "admin": _headers(admin),
        "doctor_a": _headers(doctor_a),
        "doctor_a2": _headers(doctor_a2),
        "manager_a": _headers(manager_a),
        "doctor_b": _headers(doctor_b),
        "manager_b": _headers(manager_b),
    }
    data = PatientData(
        admin_id=admin.id,
        doctor_a_id=doctor_a.id,
        doctor_a2_id=doctor_a2.id,
        manager_a_id=manager_a.id,
        doctor_b_id=doctor_b.id,
        manager_b_id=manager_b.id,
        inactive_doctor_a_id=inactive_doctor_a.id,
        doctor_inactive_clinic_id=doctor_inactive_clinic.id,
        admin_role_id=admin_role.id,
        doctor_role_id=doctor_role.id,
        manager_role_id=manager_role.id,
        clinic_a_id=clinic_a.id,
        clinic_b_id=clinic_b.id,
        inactive_clinic_id=clinic_inactive.id,
        active_patient_status_id=active_patient.id,
        inactive_patient_status_id=inactive_patient.id,
        patient_a1_id=patient_a1.id,
        patient_a2_id=patient_a2.id,
        patient_b_id=patient_b.id,
        patient_with_exam_id=patient_with_exam.id,
        inactive_valid_patient_id=inactive_valid.id,
        inactive_bad_doctor_patient_id=inactive_bad_doctor.id,
        inactive_bad_clinic_patient_id=inactive_bad_clinic.id,
    )
    return data, headers


@pytest.fixture
def patient_api_context() -> Iterator[PatientApiContext]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    with factory() as db:
        data, headers = _seed_patients(db)

    def override_get_db() -> Iterator[Session]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield PatientApiContext(
            client=client,
            session_factory=factory,
            data=data,
            admin_headers=headers["admin"],
            doctor_a_headers=headers["doctor_a"],
            doctor_a2_headers=headers["doctor_a2"],
            manager_a_headers=headers["manager_a"],
            doctor_b_headers=headers["doctor_b"],
            manager_b_headers=headers["manager_b"],
        )

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _patient_payload(*, clinic_id: int, doctor_id: int, cpf: str = "86288366757") -> dict:
    return {
        "clinic_id": clinic_id,
        "doctor_id": doctor_id,
        "name": "Paciente Novo",
        "cpf": cpf,
        "birth_date": "1995-06-15",
        "sex": "not_informed",
        "phone": "(88) 99999-0000",
        "email": "PACIENTE.NOVO@EXAMPLE.COM",
        "zip_code": "63000-000",
        "address": "Rua Acadêmica",
        "number": "10",
        "city": "Juazeiro do Norte",
        "state": "ce",
    }


def test_scope_list_filters_and_cross_access(patient_api_context: PatientApiContext) -> None:
    ctx = patient_api_context

    doctor_rows = ctx.client.get(
        "/patients/",
        params={"include_inactive": True},
        headers=ctx.doctor_a_headers,
    ).json()
    assert {row["id"] for row in doctor_rows} == {
        ctx.data.patient_a1_id,
        ctx.data.patient_with_exam_id,
    }

    manager_rows = ctx.client.get(
        "/patients/",
        params={"include_inactive": True},
        headers=ctx.manager_a_headers,
    ).json()
    assert ctx.data.patient_b_id not in {row["id"] for row in manager_rows}
    assert ctx.data.patient_a1_id in {row["id"] for row in manager_rows}
    assert ctx.data.patient_a2_id in {row["id"] for row in manager_rows}

    admin_rows = ctx.client.get(
        "/patients/",
        params={"include_inactive": True, "search": "Paciente B"},
        headers=ctx.admin_headers,
    ).json()
    assert [row["id"] for row in admin_rows] == [ctx.data.patient_b_id]

    assert ctx.client.get(
        f"/patients/{ctx.data.patient_a2_id}",
        headers=ctx.doctor_a_headers,
    ).status_code == 403
    assert ctx.client.get(
        f"/patients/{ctx.data.patient_b_id}",
        headers=ctx.manager_a_headers,
    ).status_code == 403
    assert ctx.client.get(
        "/patients/",
        params={"clinic_id": ctx.data.clinic_b_id},
        headers=ctx.manager_a_headers,
    ).status_code == 403
    assert ctx.client.get(
        "/patients/",
        params={"doctor_id": ctx.data.doctor_a2_id},
        headers=ctx.doctor_a_headers,
    ).status_code == 403


def test_cpf_birth_date_and_assignment_validation(patient_api_context: PatientApiContext) -> None:
    ctx = patient_api_context
    cpf = "86288366757"

    first = ctx.client.post(
        "/patients/",
        json=_patient_payload(
            clinic_id=ctx.data.clinic_a_id,
            doctor_id=ctx.data.doctor_a_id,
            cpf=cpf,
        ),
        headers=ctx.admin_headers,
    )
    assert first.status_code == 201
    assert first.json()["cpf"] == cpf
    assert first.json()["email"] == "paciente.novo@example.com"
    assert first.json()["state"] == "CE"

    duplicate = ctx.client.post(
        "/patients/",
        json=_patient_payload(
            clinic_id=ctx.data.clinic_a_id,
            doctor_id=ctx.data.doctor_a_id,
            cpf=cpf,
        ),
        headers=ctx.admin_headers,
    )
    assert duplicate.status_code == 400

    other_clinic = ctx.client.post(
        "/patients/",
        json=_patient_payload(
            clinic_id=ctx.data.clinic_b_id,
            doctor_id=ctx.data.doctor_b_id,
            cpf=cpf,
        ),
        headers=ctx.admin_headers,
    )
    assert other_clinic.status_code == 201

    future_payload = _patient_payload(
        clinic_id=ctx.data.clinic_a_id,
        doctor_id=ctx.data.doctor_a_id,
        cpf="93541134780",
    )
    future_payload["birth_date"] = str(date.today() + timedelta(days=1))
    assert ctx.client.post(
        "/patients/", json=future_payload, headers=ctx.admin_headers
    ).status_code == 422

    ancient_payload = _patient_payload(
        clinic_id=ctx.data.clinic_a_id,
        doctor_id=ctx.data.doctor_a_id,
        cpf="39053344705",
    )
    ancient_payload["birth_date"] = str(date.today().replace(year=date.today().year - 131))
    assert ctx.client.post(
        "/patients/", json=ancient_payload, headers=ctx.admin_headers
    ).status_code == 422

    wrong_doctor = ctx.client.post(
        "/patients/",
        json=_patient_payload(
            clinic_id=ctx.data.clinic_a_id,
            doctor_id=ctx.data.doctor_b_id,
            cpf="93541134780",
        ),
        headers=ctx.admin_headers,
    )
    assert wrong_doctor.status_code == 400

    inactive_doctor = ctx.client.post(
        "/patients/",
        json=_patient_payload(
            clinic_id=ctx.data.clinic_a_id,
            doctor_id=ctx.data.inactive_doctor_a_id,
            cpf="39053344705",
        ),
        headers=ctx.admin_headers,
    )
    assert inactive_doctor.status_code == 400


def test_doctor_can_create_only_for_self_and_own_clinic(patient_api_context: PatientApiContext) -> None:
    ctx = patient_api_context

    wrong_doctor = ctx.client.post(
        "/patients/",
        json=_patient_payload(
            clinic_id=ctx.data.clinic_a_id,
            doctor_id=ctx.data.doctor_a2_id,
            cpf="86288366757",
        ),
        headers=ctx.doctor_a_headers,
    )
    assert wrong_doctor.status_code == 403

    wrong_clinic = ctx.client.post(
        "/patients/",
        json=_patient_payload(
            clinic_id=ctx.data.clinic_b_id,
            doctor_id=ctx.data.doctor_a_id,
            cpf="86288366757",
        ),
        headers=ctx.doctor_a_headers,
    )
    assert wrong_clinic.status_code == 403

    own = ctx.client.post(
        "/patients/",
        json=_patient_payload(
            clinic_id=ctx.data.clinic_a_id,
            doctor_id=ctx.data.doctor_a_id,
            cpf="86288366757",
        ),
        headers=ctx.doctor_a_headers,
    )
    assert own.status_code == 201
    assert own.json()["doctor_id"] == ctx.data.doctor_a_id


def test_doctor_cannot_reassign_but_manager_can_inside_clinic(patient_api_context: PatientApiContext) -> None:
    ctx = patient_api_context

    denied = ctx.client.patch(
        f"/patients/{ctx.data.patient_a1_id}",
        json={"doctor_id": ctx.data.doctor_a2_id},
        headers=ctx.doctor_a_headers,
    )
    assert denied.status_code == 403

    reassigned = ctx.client.patch(
        f"/patients/{ctx.data.patient_a1_id}",
        json={"doctor_id": ctx.data.doctor_a2_id},
        headers=ctx.manager_a_headers,
    )
    assert reassigned.status_code == 200
    assert reassigned.json()["doctor_id"] == ctx.data.doctor_a2_id

    assert ctx.client.get(
        f"/patients/{ctx.data.patient_a1_id}", headers=ctx.doctor_a_headers
    ).status_code == 403
    assert ctx.client.get(
        f"/patients/{ctx.data.patient_a1_id}", headers=ctx.doctor_a2_headers
    ).status_code == 200

    cross_clinic = ctx.client.patch(
        f"/patients/{ctx.data.patient_a2_id}",
        json={
            "clinic_id": ctx.data.clinic_b_id,
            "doctor_id": ctx.data.doctor_b_id,
        },
        headers=ctx.manager_a_headers,
    )
    assert cross_clinic.status_code == 403


def test_admin_transfer_without_history_and_cpf_conflict(patient_api_context: PatientApiContext) -> None:
    ctx = patient_api_context

    conflict = ctx.client.patch(
        f"/patients/{ctx.data.patient_a1_id}",
        json={
            "clinic_id": ctx.data.clinic_b_id,
            "doctor_id": ctx.data.doctor_b_id,
        },
        headers=ctx.admin_headers,
    )
    assert conflict.status_code == 400
    assert "CPF" in conflict.json()["detail"]

    transferred = ctx.client.patch(
        f"/patients/{ctx.data.patient_a2_id}",
        json={
            "clinic_id": ctx.data.clinic_b_id,
            "doctor_id": ctx.data.doctor_b_id,
        },
        headers=ctx.admin_headers,
    )
    assert transferred.status_code == 200
    assert transferred.json()["clinic_id"] == ctx.data.clinic_b_id
    assert transferred.json()["doctor_id"] == ctx.data.doctor_b_id

    with ctx.session_factory() as db:
        log = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity == "patient",
                AuditLog.entity_id == ctx.data.patient_a2_id,
            )
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert log is not None
        assert log.description == "Vínculo do paciente atualizado."
        assert log.old_data["clinic_id"] == ctx.data.clinic_a_id
        assert log.new_data["clinic_id"] == ctx.data.clinic_b_id
        assert log.new_data["assignment_changed"] is True


def test_reassignment_is_blocked_when_patient_has_exam(patient_api_context: PatientApiContext) -> None:
    ctx = patient_api_context

    response = ctx.client.patch(
        f"/patients/{ctx.data.patient_with_exam_id}",
        json={"doctor_id": ctx.data.doctor_a2_id},
        headers=ctx.manager_a_headers,
    )
    assert response.status_code == 409
    assert "exames vinculados" in response.json()["detail"]

    response = ctx.client.patch(
        f"/patients/{ctx.data.patient_with_exam_id}",
        json={
            "clinic_id": ctx.data.clinic_b_id,
            "doctor_id": ctx.data.doctor_b_id,
        },
        headers=ctx.admin_headers,
    )
    assert response.status_code == 409


def test_status_is_dedicated_idempotent_and_revalidates_links(patient_api_context: PatientApiContext) -> None:
    ctx = patient_api_context

    assert ctx.client.patch(
        f"/patients/{ctx.data.patient_a1_id}",
        json={"status_id": ctx.data.inactive_patient_status_id},
        headers=ctx.manager_a_headers,
    ).status_code == 422

    with ctx.session_factory() as db:
        before = db.query(AuditLog).filter(AuditLog.entity == "patient").count()

    first_inactivate = ctx.client.patch(
        f"/patients/{ctx.data.patient_a1_id}/inactivate",
        headers=ctx.manager_a_headers,
    )
    second_inactivate = ctx.client.patch(
        f"/patients/{ctx.data.patient_a1_id}/inactivate",
        headers=ctx.manager_a_headers,
    )
    assert first_inactivate.status_code == 200
    assert second_inactivate.status_code == 200

    first_activate = ctx.client.patch(
        f"/patients/{ctx.data.patient_a1_id}/activate",
        headers=ctx.manager_a_headers,
    )
    second_activate = ctx.client.patch(
        f"/patients/{ctx.data.patient_a1_id}/activate",
        headers=ctx.manager_a_headers,
    )
    assert first_activate.status_code == 200
    assert second_activate.status_code == 200

    with ctx.session_factory() as db:
        after = db.query(AuditLog).filter(AuditLog.entity == "patient").count()
    assert after - before == 2

    assert ctx.client.patch(
        f"/patients/{ctx.data.inactive_bad_doctor_patient_id}/activate",
        headers=ctx.admin_headers,
    ).status_code == 400
    assert ctx.client.patch(
        f"/patients/{ctx.data.inactive_bad_clinic_patient_id}/activate",
        headers=ctx.admin_headers,
    ).status_code == 400
    assert ctx.client.patch(
        f"/patients/{ctx.data.inactive_valid_patient_id}/activate",
        headers=ctx.admin_headers,
    ).status_code == 200


def test_required_fields_cannot_be_cleared(patient_api_context: PatientApiContext) -> None:
    ctx = patient_api_context

    for field in ("name", "cpf", "clinic_id", "doctor_id"):
        response = ctx.client.patch(
            f"/patients/{ctx.data.patient_a1_id}",
            json={field: None},
            headers=ctx.manager_a_headers,
        )
        assert response.status_code == 400, (field, response.text)


def test_doctor_context_cannot_change_while_active_patients_exist(
    patient_api_context: PatientApiContext,
) -> None:
    ctx = patient_api_context

    inactivate = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}/inactivate",
        headers=ctx.admin_headers,
    )
    assert inactivate.status_code == 409

    change_role = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}",
        json={"role_id": ctx.data.manager_role_id},
        headers=ctx.admin_headers,
    )
    assert change_role.status_code == 409

    change_clinic = ctx.client.patch(
        f"/users/{ctx.data.doctor_a_id}",
        json={"clinic_id": ctx.data.clinic_b_id},
        headers=ctx.admin_headers,
    )
    assert change_clinic.status_code == 409
