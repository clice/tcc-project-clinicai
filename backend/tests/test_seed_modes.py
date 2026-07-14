"""Testes do bootstrap estrutural e da massa acadêmica do CHK-03."""

import pytest
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.ai_analysis.model import AIAnalysis
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.patients.model import Patient
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.seeds import bootstrap_reference_data, seed_academic_demo
from app.modules.users.model import User
from app.modules.users.seed import ACADEMIC_DEMO_EMAILS


def count(db: Session, model: type) -> int:
    return int(db.query(func.count(model.id)).scalar())


def test_bootstrap_does_not_create_demo_records(db_session: Session) -> None:
    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    assert len(bootstrap.statuses) == 17
    assert len(bootstrap.roles) == 3
    assert count(db_session, Permission) == len(bootstrap.permissions)
    assert count(db_session, Clinic) == 0
    assert count(db_session, User) == 0
    assert count(db_session, Patient) == 0
    assert count(db_session, Exam) == 0
    assert count(db_session, AIAnalysis) == 0


def test_three_bootstraps_preserve_admin_configuration(db_session: Session) -> None:
    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    doctor = bootstrap.roles["doctor"]
    exam_pending = bootstrap.statuses["exam_pending"]
    download = bootstrap.permissions["exams:download"]
    audit_read = bootstrap.permissions["audit_logs:read"]

    doctor.display_name = "Médico personalizado"
    exam_pending.display_name = "Fila personalizada"
    db_session.query(RolePermission).filter_by(
        role_id=doctor.id,
        permission_id=download.id,
    ).delete()
    db_session.add(RolePermission(role_id=doctor.id, permission_id=audit_read.id))
    db_session.commit()

    for _ in range(3):
        bootstrap_reference_data(db_session)
        db_session.commit()

    db_session.refresh(doctor)
    db_session.refresh(exam_pending)
    permission_names = {
        name
        for (name,) in (
            db_session.query(Permission.name)
            .join(RolePermission)
            .filter(RolePermission.role_id == doctor.id)
            .all()
        )
    }

    assert doctor.display_name == "Médico personalizado"
    assert exam_pending.display_name == "Fila personalizada"
    assert "exams:download" not in permission_names
    assert "audit_logs:read" in permission_names


def test_academic_demo_is_predictable_and_idempotent(db_session: Session) -> None:
    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    demo = seed_academic_demo(db_session, bootstrap)
    db_session.commit()

    assert len(demo.clinics) == 8
    assert len(demo.users) == 5
    assert len(demo.patients) == 8
    assert len(demo.exams) == 3
    assert len(demo.ai_analyses) == 2
    assert {user.email for user in demo.users.values()} == set(ACADEMIC_DEMO_EMAILS)

    primary_clinic = demo.clinics["clinic_primary"]
    primary_doctor = demo.users["doctor_primary"]
    assert all(
        patient.clinic_id == primary_clinic.id for patient in demo.patients.values()
    )
    assert all(
        patient.doctor_id == primary_doctor.id for patient in demo.patients.values()
    )
    assert all(exam.clinic_id == primary_clinic.id for exam in demo.exams.values())
    assert all(exam.doctor_id == primary_doctor.id for exam in demo.exams.values())
    assert all(exam.patient.clinic_id == exam.clinic_id for exam in demo.exams.values())

    # Alterações administrativas em registros demo também não são reconciliadas.
    original_hash = primary_doctor.password_hash
    primary_clinic.name = "Clínica Primária Personalizada"
    db_session.commit()

    for _ in range(3):
        bootstrap = bootstrap_reference_data(db_session)
        seed_academic_demo(db_session, bootstrap)
        db_session.commit()

    assert count(db_session, Clinic) == 8
    assert count(db_session, User) == 5
    assert count(db_session, Patient) == 8
    assert count(db_session, Exam) == 3
    assert count(db_session, AIAnalysis) == 2
    db_session.refresh(primary_clinic)
    db_session.refresh(primary_doctor)
    assert primary_clinic.name == "Clínica Primária Personalizada"
    assert primary_doctor.password_hash == original_hash


def test_demo_phase_can_be_rolled_back_without_partial_clinics(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.seeds as seeds_module

    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    def fail_users(*args, **kwargs):
        raise RuntimeError("falha simulada na massa demo")

    monkeypatch.setattr(seeds_module, "seed_users", fail_users)

    with pytest.raises(RuntimeError, match="falha simulada"):
        seed_academic_demo(db_session, bootstrap)
    db_session.rollback()

    assert count(db_session, Clinic) == 0
    assert count(db_session, User) == 0
