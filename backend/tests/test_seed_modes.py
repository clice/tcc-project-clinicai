"""Testes do bootstrap estrutural e da massa acadêmica."""

from collections import Counter, defaultdict
import json

import pytest
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.validators import is_valid_cpf
from app.core.config import settings
from app.core.security import verify_password
from app.modules.academic_demo_assets import (
    get_demo_manifest,
    verify_bundled_demo_assets,
)
from app.modules.ai_analyses import file_storage as attribution_file_storage
from app.modules.ai_analyses.file_storage import resolve_safe_gradcam_path
from app.modules.ai_analyses.model import AIAnalysis
from app.modules.ai_analyses.service import get_ai_metrics
from app.modules.clinics.model import Clinic
from app.modules.clinics.seed import ACADEMIC_DEMO_CLINICS
from app.modules.exams import file_storage as exam_file_storage
from app.modules.exams.file_storage import resolve_safe_exam_file_path
from app.modules.exams.model import Exam
from app.modules.patients.model import Patient
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.seeds import bootstrap_reference_data, seed_academic_demo
from app.modules.users.model import User
from app.modules.users.seed import ACADEMIC_DEMO_EMAILS


EXPECTED_CLINIC_KEYS = {
    "clinic_primary",
    "clinic_large",
    "clinic_specialized",
    "clinic_inactive",
}
EXPECTED_STATUS_COUNTS = {
    "awaiting_review": 22,
    "canceled": 6,
    "completed": 43,
    "completed_with_divergence": 7,
    "failed": 6,
    "pending": 6,
}
EXPECTED_ANALYSIS_EXAM_STATUS_COUNTS = {
    "awaiting_review": 22,
    "completed": 43,
    "completed_with_divergence": 7,
}
EXPECTED_ATTRIBUTION_KEYS = {
    "attribution_method",
    "attribution_target_layers",
    "attribution_local_evidence",
    "attribution_branch_weights",
    "attribution_branch_cam_raw_maxima",
    "attribution_unavailable_reason",
}


def count(db: Session, model: type) -> int:
    return int(db.query(func.count(model.id)).scalar())


@pytest.fixture
def isolated_demo_uploads(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    data_root = tmp_path / "data"
    exams_root = data_root / "exams"

    monkeypatch.setattr(
        exam_file_storage,
        "DATA_DIR",
        data_root,
    )
    monkeypatch.setattr(
        exam_file_storage,
        "UPLOAD_DIR",
        exams_root,
    )
    monkeypatch.setattr(
        attribution_file_storage,
        "DATA_DIR",
        data_root,
    )
    monkeypatch.setattr(
        attribution_file_storage,
        "EXAMS_DIR",
        exams_root,
    )

    return exams_root


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
    manifest = get_demo_manifest()
    assert manifest["schema_version"] == 2
    assert manifest["model"] == {
        "name": "ensemble_stacking",
        "operational_fold": 1,
        "release": "models-v0.1.2",
        "training_protocol": (
            "viana_codigo_kfold3_roi_sh_da"
        ),
        "version": "0.1.2",
    }
    assert manifest["dataset"][
        "real_source_prediction_divergences"
    ] == 1
    assert len(verify_bundled_demo_assets()) == 162

    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    demo = seed_academic_demo(db_session, bootstrap)
    db_session.commit()

    assert set(demo.clinics) == EXPECTED_CLINIC_KEYS
    assert len(demo.clinics) == 4
    assert len(demo.users) == 13
    assert len(demo.patients) == 30
    assert len(demo.exams) == 90
    assert len(demo.ai_analyses) == 72

    expected_emails = set(ACADEMIC_DEMO_EMAILS) | {
        settings.bootstrap_admin_email
    }
    assert {user.email for user in demo.users.values()} == expected_emails
    assert demo.users["admin_master"].id == bootstrap.admin_user.id

    manifest_clinic_names = {
        item["key"]: item["name"]
        for item in manifest["clinics"]
    }
    assert manifest_clinic_names["clinic_large"] == (
        "Hospital Regional do Cariri"
    )
    assert all(
        item["clinic_name"]
        == manifest_clinic_names[item["clinic_key"]]
        for item in manifest["exams"]
    )

    assert demo.clinics["clinic_large"].name == (
        "Hospital Regional do Cariri"
    )

    expected_functional_user_names = {
        "manager_large": "Gestor Hospital Cariri",
        "manager_specialized": "Gestão Centro Endoscópico",
        "manager_inactive_large": (
            "Gestor Inativo Hospital Cariri"
        ),
        "admin_master_inactive": (
            "Administrador Master Inativo"
        ),
    }
    assert {
        key: demo.users[key].name
        for key in expected_functional_user_names
    } == expected_functional_user_names

    invalid_demo_cpfs = {
        patient.name: patient.cpf
        for patient in demo.patients.values()
        if not is_valid_cpf(patient.cpf)
    }
    assert invalid_demo_cpfs == {}

    user_status_counts = Counter(
        user.status.name for user in demo.users.values()
    )
    assert user_status_counts == Counter({"active": 8, "inactive": 5})

    inactive_role_counts = Counter(
        user.role.name
        for user in demo.users.values()
        if user.status.name == "inactive"
    )
    assert inactive_role_counts == Counter(
        {"doctor": 2, "clinic_manager": 2, "admin_master": 1}
    )

    patient_status_counts = Counter(
        patient.status.name for patient in demo.patients.values()
    )
    assert patient_status_counts == Counter({"active": 24, "inactive": 6})

    patients_by_clinic = Counter(
        patient.clinic_id for patient in demo.patients.values()
    )
    exams_by_clinic = Counter(exam.clinic_id for exam in demo.exams.values())
    active_clinic_ids = {
        clinic.id
        for key, clinic in demo.clinics.items()
        if key != "clinic_inactive"
    }
    inactive_clinic_id = demo.clinics["clinic_inactive"].id

    assert patients_by_clinic == Counter(
        {clinic_id: 10 for clinic_id in active_clinic_ids}
    )
    assert exams_by_clinic == Counter(
        {clinic_id: 30 for clinic_id in active_clinic_ids}
    )
    assert patients_by_clinic[inactive_clinic_id] == 0
    assert exams_by_clinic[inactive_clinic_id] == 0

    exams_by_patient = Counter(exam.patient_id for exam in demo.exams.values())
    assert set(exams_by_patient.values()) == {3}
    assert all(
        patient.clinic_id == patient.doctor.clinic_id
        for patient in demo.patients.values()
    )
    assert all(
        exam.clinic_id == exam.patient.clinic_id == exam.doctor.clinic_id
        for exam in demo.exams.values()
    )

    status_counts = Counter(exam.status.name for exam in demo.exams.values())
    assert dict(sorted(status_counts.items())) == EXPECTED_STATUS_COUNTS

    for definition in manifest["exams"]:
        review = definition.get("review")

        if review is None:
            continue

        analysis_definition = definition.get(
            "analysis"
        )
        assert analysis_definition is not None

        expected_agreement = (
            review["reviewed_label"]
            == analysis_definition[
                "prediction_label"
            ]
        )
        expected_status = (
            "completed"
            if expected_agreement
            else "completed_with_divergence"
        )

        assert review["agrees_with_ai"] is (
            expected_agreement
        )
        assert definition["status"] == (
            expected_status
        )

    monthly_counts = Counter(
        exam.exam_date.strftime("%Y-%m")
        for exam in demo.exams.values()
    )
    assert monthly_counts == Counter(
        {
            "2026-02": 11,
            "2026-03": 16,
            "2026-04": 14,
            "2026-05": 18,
            "2026-06": 14,
            "2026-07": 17,
        }
    )

    for exam in demo.exams.values():
        assert exam.file_path
        assert resolve_safe_exam_file_path(exam.file_path).is_file()
        assert exam.file_name.endswith(".jpg")
        assert exam.file_mime_type == "image/jpeg"
        assert exam.analysis_in_progress is False
        assert exam.analysis_started_at is None

        reviewed = exam.status.name in {
            "completed",
            "completed_with_divergence",
        }
        if reviewed:
            assert exam.reviewed_by_id == exam.doctor_id
            assert exam.reviewed_at is not None
            assert exam.findings
            assert exam.conclusion
        else:
            assert exam.reviewed_by_id is None
            assert exam.reviewed_at is None

    assert sum(
        exam.status.name in {"completed", "completed_with_divergence"}
        for exam in demo.exams.values()
    ) == 50

    label_counts = Counter(
        analysis.prediction_label for analysis in demo.ai_analyses.values()
    )
    assert dict(sorted(label_counts.items())) == {"abnormal": 35, "normal": 37}

    metrics = get_ai_metrics(db_session)

    assert metrics["total_analyses"] == 72
    assert metrics["reviewed_analyses_count"] == 50
    assert metrics["false_positive_count"] == 2
    assert metrics["false_negative_count"] == 5
    assert metrics["confidence_mean"] is not None
    assert metrics["processing_time_mean_ms"] is not None

    analysis_exam_status_counts = Counter(
        analysis.exam.status.name for analysis in demo.ai_analyses.values()
    )
    assert (
        dict(sorted(analysis_exam_status_counts.items()))
        == EXPECTED_ANALYSIS_EXAM_STATUS_COUNTS
    )

    for analysis in demo.ai_analyses.values():
        assert analysis.status.name == "completed"
        assert analysis.model_name == "ensemble_stacking"
        assert analysis.model_version == "0.1.2"
        assert analysis.gradcam_path
        assert resolve_safe_gradcam_path(analysis.gradcam_path).is_file()

        metadata = json.loads(analysis.raw_response)
        assert EXPECTED_ATTRIBUTION_KEYS <= set(metadata)
        assert metadata["attribution_method"] == (
            "weighted_base_gradcam_oriented_by_ensemble_stacking_v1"
        )
        assert set(metadata["attribution_target_layers"]) == {
            "resnet50",
            "efficientnet_b4",
            "pvt_v2_b2",
        }
        assert metadata["attribution_unavailable_reason"] is None

    assert sum(exam.ai_analysis is None for exam in demo.exams.values()) == 18

    primary_clinic = demo.clinics["clinic_primary"]
    primary_doctor = demo.users["doctor_primary"]
    pending_exam = next(
        exam
        for exam in demo.exams.values()
        if exam.clinic_id == primary_clinic.id and exam.status.name == "pending"
    )
    analysis = next(iter(demo.ai_analyses.values()))
    expected_model_version = analysis.model_version
    expected_confidence = analysis.confidence
    original_hash = primary_doctor.password_hash
    primary_clinic.name = "Clínica Primária Personalizada"
    pending_exam.observations = "Descrição acadêmica personalizada"
    analysis.model_version = "versao-antiga"
    analysis.confidence = 0.01
    db_session.commit()

    for _ in range(3):
        bootstrap = bootstrap_reference_data(db_session)
        seed_academic_demo(db_session, bootstrap)
        db_session.commit()

    assert count(db_session, Clinic) == 4
    assert count(db_session, User) == 13
    assert count(db_session, Patient) == 30
    assert count(db_session, Exam) == 90
    assert count(db_session, AIAnalysis) == 72

    db_session.refresh(primary_clinic)
    db_session.refresh(primary_doctor)
    db_session.refresh(pending_exam)
    db_session.refresh(analysis)
    assert primary_clinic.name == ACADEMIC_DEMO_CLINICS["clinic_primary"]["name"]
    assert primary_doctor.password_hash == original_hash
    assert pending_exam.observations.startswith(
        "Exame fictício da massa acadêmica"
    )
    assert analysis.model_version == expected_model_version
    assert analysis.confidence == expected_confidence


def test_database_contract_accepts_academic_demo(
    db_session: Session,
    isolated_demo_uploads,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.maintenance import database_contract

    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    seed_academic_demo(db_session, bootstrap)
    db_session.commit()

    monkeypatch.setattr(
        database_contract,
        "SessionLocal",
        lambda: db_session,
    )

    database_contract.assert_demo_data()


def test_database_contract_accepts_external_records_with_demo(
    db_session: Session,
    isolated_demo_uploads,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.maintenance import database_contract

    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    db_session.add(
        Clinic(
            name="Clínica externa legítima",
            cnpj="99888777000166",
            email="externa@example.com",
            status_id=bootstrap.statuses["clinic_active"].id,
        )
    )
    db_session.commit()
    seed_academic_demo(db_session, bootstrap)
    db_session.commit()

    monkeypatch.setattr(database_contract, "SessionLocal", lambda: db_session)
    database_contract.assert_demo_data()


def test_demo_collision_rolls_back_without_partial_records(
    db_session: Session,
) -> None:
    bootstrap = bootstrap_reference_data(db_session)
    db_session.commit()

    db_session.add(
        Clinic(
            name="Clínica externa conflitante",
            cnpj="88777666000155",
            email=ACADEMIC_DEMO_CLINICS["clinic_large"]["email"],
            status_id=bootstrap.statuses["clinic_active"].id,
        )
    )
    db_session.commit()

    with pytest.raises(RuntimeError, match="Colisão da massa acadêmica"):
        seed_academic_demo(db_session, bootstrap)
    db_session.rollback()

    assert count(db_session, Clinic) == 1
    assert count(db_session, User) == 1
    assert count(db_session, Patient) == 0
    assert count(db_session, Exam) == 0
    assert count(db_session, AIAnalysis) == 0


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
