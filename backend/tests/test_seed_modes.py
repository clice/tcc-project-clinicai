"""Testes do bootstrap estrutural e da massa acadêmica."""

from collections import Counter

import pytest
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.modules import academic_demo_assets
from app.modules.academic_demo_assets import verify_bundled_demo_assets
from app.modules.ai_analysis.file_storage import resolve_safe_gradcam_path
from app.modules.ai_analysis.model import AIAnalysis
from app.modules.clinics.model import Clinic
from app.modules.exams import file_storage as exam_file_storage
from app.modules.exams.file_storage import resolve_safe_exam_file_path
from app.modules.exams.model import Exam
from app.modules.patients.model import Patient
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.seeds import bootstrap_reference_data, seed_academic_demo
from app.modules.users.model import User
from app.modules.users.seed import ACADEMIC_DEMO_EMAILS


def count(db: Session, model: type) -> int:
    return int(db.query(func.count(model.id)).scalar())


@pytest.fixture
def isolated_demo_uploads(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    upload_root = tmp_path / "uploads" / "exams"
    monkeypatch.setattr(exam_file_storage, "UPLOAD_DIR", upload_root)
    return upload_root


def test_bootstrap_creates_only_initial_admin_and_no_demo_records(
    db_session: Session,
) -> None:
    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    assert len(bootstrap.statuses) == 17
    assert len(bootstrap.roles) == 3
    assert count(db_session, Permission) == len(bootstrap.permissions)
    assert count(db_session, Clinic) == 0
    assert count(db_session, User) == 1
    assert count(db_session, Patient) == 0
    assert count(db_session, Exam) == 0
    assert count(db_session, AIAnalysis) == 0

    admin = bootstrap.admin_user
    assert admin.email == settings.bootstrap_admin_email
    assert admin.name == settings.bootstrap_admin_name
    assert admin.cpf == settings.bootstrap_admin_cpf
    assert admin.clinic_id is None
    assert admin.role.name == "admin_master"
    assert admin.status.name == "active"
    assert verify_password(settings.bootstrap_admin_password, admin.password_hash)


def test_three_bootstraps_preserve_existing_configuration(
    db_session: Session,
) -> None:
    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    doctor = bootstrap.roles["doctor"]
    exam_pending = bootstrap.statuses["exam_pending"]
    download = bootstrap.permissions["exams:download"]
    audit_read = bootstrap.permissions["audit_logs:read"]
    admin = bootstrap.admin_user
    original_admin_hash = admin.password_hash

    doctor.display_name = "Médico personalizado"
    exam_pending.display_name = "Fila personalizada"
    admin.name = "Administrador personalizado"
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
    db_session.refresh(admin)
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
    assert admin.name == "Administrador personalizado"
    assert admin.password_hash == original_admin_hash
    assert "exams:download" not in permission_names
    assert "audit_logs:read" in permission_names


def test_academic_demo_is_predictable_and_idempotent(
    db_session: Session,
    isolated_demo_uploads,
) -> None:
    assert len(verify_bundled_demo_assets()) == 4

    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    demo = seed_academic_demo(db_session, bootstrap)
    db_session.commit()

    assert len(demo.clinics) == 8
    assert len(demo.users) == 5
    assert len(demo.patients) == 8
    assert len(demo.exams) == 7
    assert len(demo.ai_analyses) == 4

    expected_emails = set(ACADEMIC_DEMO_EMAILS) | {
        settings.bootstrap_admin_email
    }
    assert {user.email for user in demo.users.values()} == expected_emails
    assert demo.users["admin_master"].id == bootstrap.admin_user.id

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

    status_counts = Counter(exam.status.name for exam in demo.exams.values())
    assert dict(status_counts) == {
        "pending": 1,
        "awaiting_review": 2,
        "completed": 1,
        "completed_with_divergence": 1,
        "failed": 1,
        "canceled": 1,
    }

    for exam in demo.exams.values():
        assert exam.file_path
        assert resolve_safe_exam_file_path(exam.file_path).is_file()
        assert exam.file_name.endswith(".jpg")
        assert exam.file_mime_type == "image/jpeg"
        assert exam.analysis_in_progress is False
        assert exam.analysis_started_at is None

    for exam in (
        demo.exams["exam_completed_confirmed"],
        demo.exams["exam_completed_with_divergence"],
    ):
        assert exam.reviewed_by_id == primary_doctor.id
        assert exam.reviewed_at is not None
        assert exam.findings
        assert exam.conclusion

    label_counts = Counter(
        analysis.prediction_label for analysis in demo.ai_analyses.values()
    )
    assert dict(label_counts) == {"normal": 2, "abnormal": 2}

    for analysis in demo.ai_analyses.values():
        assert analysis.status.name == "completed"
        assert analysis.model_name == "ensemble_stacking"
        assert analysis.model_version == "0.1.0"
        assert analysis.gradcam_path
        assert resolve_safe_gradcam_path(analysis.gradcam_path).is_file()
        assert analysis.raw_response is None

    assert demo.exams["exam_pending"].ai_analysis is None
    assert demo.exams["exam_failed"].ai_analysis is None
    assert demo.exams["exam_canceled"].ai_analysis is None

    original_hash = primary_doctor.password_hash
    primary_clinic.name = "Clínica Primária Personalizada"
    pending_exam = demo.exams["exam_pending"]
    pending_exam.description = "Descrição acadêmica personalizada"
    db_session.commit()

    for _ in range(3):
        bootstrap = bootstrap_reference_data(db_session)
        seed_academic_demo(db_session, bootstrap)
        db_session.commit()

    assert count(db_session, Clinic) == 8
    assert count(db_session, User) == 5
    assert count(db_session, Patient) == 8
    assert count(db_session, Exam) == 7
    assert count(db_session, AIAnalysis) == 4

    db_session.refresh(primary_clinic)
    db_session.refresh(primary_doctor)
    db_session.refresh(pending_exam)
    assert primary_clinic.name == "Clínica Primária Personalizada"
    assert primary_doctor.password_hash == original_hash
    assert pending_exam.description == "Descrição acadêmica personalizada"


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
    assert count(db_session, User) == 1
