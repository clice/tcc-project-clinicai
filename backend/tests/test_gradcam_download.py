"""Download autenticado do Grad-CAM e ausência de caminhos físicos nas APIs."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.modules.ai_analysis import file_storage as ai_file_storage
from app.modules.ai_analysis.model import AIAnalysis
from app.modules.ai_analysis.schema import AIAnalysisResponse
from app.modules.audit_logs.model import AuditLog
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.exams.schema import ExamResponse
from app.modules.exams.service import (
    download_exam_ai_file,
    preview_exam_ai_file,
)
from app.modules.patients.model import Patient
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


def assert_http_error(expected_status: int, call) -> HTTPException:
    with pytest.raises(HTTPException) as error:
        call()
    assert error.value.status_code == expected_status
    return error.value


@pytest.fixture
def isolated_ai_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "storage"
    monkeypatch.setattr(ai_file_storage, "AI_STORAGE_DIR", root)
    monkeypatch.setattr(ai_file_storage, "GRADCAM_DIR", root / "gradcam")
    return root


def seed_context(db_session, gradcam_path: Path):
    active_user = Status(name="active", display_name="Ativo", applies_to="user")
    active_clinic = Status(name="active", display_name="Ativa", applies_to="clinic")
    active_patient = Status(name="active", display_name="Ativo", applies_to="patient")
    awaiting_review = Status(
        name="awaiting_review",
        display_name="Aguardando revisão",
        applies_to="exam",
    )
    completed_ai = Status(
        name="completed",
        display_name="Concluída",
        applies_to="ai_analysis",
    )

    doctor_role = Role(
        name="doctor",
        display_name="Médico",
        permissions_initialized=True,
    )
    staff_role = Role(
        name="clinic_manager",
        display_name="Funcionário",
        permissions_initialized=True,
    )

    clinic_a = Clinic(name="Clínica Grad-CAM A", cnpj="11222333000181", status=active_clinic)
    clinic_b = Clinic(name="Clínica Grad-CAM B", cnpj="11444777000161", status=active_clinic)

    doctor_a = User(
        name="Médico Grad-CAM A",
        email="medico.gradcam.a@example.com",
        cpf="52998224725",
        password_hash="hash",
        role=doctor_role,
        status=active_user,
        clinic=clinic_a,
    )
    doctor_b = User(
        name="Médico Grad-CAM B",
        email="medico.gradcam.b@example.com",
        cpf="11144477735",
        password_hash="hash",
        role=doctor_role,
        status=active_user,
        clinic=clinic_b,
    )
    staff_a = User(
        name="Funcionário Grad-CAM A",
        email="staff.gradcam.a@example.com",
        cpf="12345678909",
        password_hash="hash",
        role=staff_role,
        status=active_user,
        clinic=clinic_a,
    )

    patient = Patient(
        name="Paciente Grad-CAM",
        cpf="16899535009",
        clinic=clinic_a,
        doctor=doctor_a,
        status=active_patient,
    )
    exam = Exam(
        clinic=clinic_a,
        patient=patient,
        doctor=doctor_a,
        status=awaiting_review,
        exam_type="colonoscopy",
        description="Exame com Grad-CAM",
        file_name="exame.png",
        file_mime_type="image/png",
    )
    analysis = AIAnalysis(
        exam=exam,
        status=completed_ai,
        prediction_label="abnormal",
        prediction_class=1,
        confidence=0.91,
        model_name="ensemble_stacking",
        model_version="0.1.0",
        gradcam_path=str(gradcam_path),
        processing_time_ms=250,
    )

    db_session.add_all(
        [
            active_user,
            active_clinic,
            active_patient,
            awaiting_review,
            completed_ai,
            doctor_role,
            staff_role,
            clinic_a,
            clinic_b,
            doctor_a,
            doctor_b,
            staff_a,
            patient,
            exam,
            analysis,
        ]
    )
    db_session.commit()
    return exam, analysis, doctor_a, doctor_b, staff_a


def test_gradcam_preview_and_download_are_scoped_private_and_audited(
    db_session,
    isolated_ai_storage: Path,
) -> None:
    gradcam = (
        isolated_ai_storage
        / "gradcam"
        / "mapa.jpg"
    )
    gradcam.parent.mkdir(parents=True)
    gradcam.write_bytes(b"gradcam-academico")

    (
        exam,
        analysis,
        doctor_a,
        doctor_b,
        staff_a,
    ) = seed_context(
        db_session,
        gradcam,
    )

    assert_http_error(
        403,
        lambda: preview_exam_ai_file(
            db_session,
            exam.id,
            doctor_b,
        ),
    )

    assert_http_error(
        403,
        lambda: download_exam_ai_file(
            db_session,
            exam.id,
            staff_a,
        ),
    )

    assert (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "download")
        .count()
        == 0
    )

    preview_response = preview_exam_ai_file(
        db_session,
        exam.id,
        doctor_a,
    )

    assert Path(preview_response.path) == gradcam
    assert preview_response.media_type == "image/jpeg"

    preview_disposition = preview_response.headers[
        "content-disposition"
    ]

    assert preview_disposition.startswith("inline;")
    assert (
        preview_response.headers["cache-control"]
        == "private, no-store"
    )

    assert (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "download")
        .count()
        == 0
    )

    response = download_exam_ai_file(
        db_session,
        exam.id,
        doctor_a,
    )

    assert Path(response.path) == gradcam
    assert response.media_type == "image/jpeg"

    disposition = response.headers[
        "content-disposition"
    ]

    expected_name = (
        f"mapa-grad-cam-exame-{exam.id}-"
        "paciente-grad-cam-sem-data.jpg"
    )

    assert disposition.startswith("attachment;")
    assert response.headers["cache-control"] == "no-store"
    assert expected_name in disposition

    logs = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.action == "download",
            AuditLog.entity == "ai_analysis",
            AuditLog.entity_id == analysis.id,
        )
        .all()
    )

    assert len(logs) == 1
    assert (
        logs[0].description
        == "Download do Mapa Grad-CAM autorizado."
    )
    assert (
        logs[0].new_data["artifact_type"]
        == "ai_attribution_map"
    )
    assert "gradcam_path" not in str(logs[0].new_data)
    assert (
        logs[0].new_data["download_name"]
        == expected_name
    )
    assert (
        logs[0].new_data["delivery_mode"]
        == "attachment"
    )


def test_gradcam_path_outside_shared_storage_is_rejected(
    db_session,
    isolated_ai_storage: Path,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"fora")
    exam, _, doctor_a, _, _ = seed_context(db_session, outside)

    assert_http_error(403, lambda: download_exam_ai_file(db_session, exam.id, doctor_a))


def test_missing_gradcam_returns_404(
    db_session,
    isolated_ai_storage: Path,
) -> None:
    missing = isolated_ai_storage / "gradcam" / "ausente.jpg"
    exam, _, doctor_a, _, _ = seed_context(db_session, missing)

    assert_http_error(404, lambda: download_exam_ai_file(db_session, exam.id, doctor_a))


def test_public_schemas_do_not_expose_physical_paths() -> None:
    assert "file_path" not in ExamResponse.model_fields
    assert "gradcam_path" not in AIAnalysisResponse.model_fields
    assert "gradcam_available" in AIAnalysisResponse.model_fields
    assert "raw_response" not in AIAnalysisResponse.model_fields
