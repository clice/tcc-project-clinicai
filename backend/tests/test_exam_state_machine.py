"""CHK-09 — tabela de transições, repetição, concorrência e revisão única."""

from __future__ import annotations
from datetime import date

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.common.constants import StatusName
from app.modules.ai_analyses.model import AIAnalysis
from app.modules.ai_analyses.schema import AIAnalysisCreate
from app.modules.ai_analyses.service import create_ai_analysis
from app.modules.audit_logs.model import AuditLog
from app.modules.clinics.model import Clinic
from app.modules.exams import file_storage
from app.modules.exams.model import Exam
from app.modules.exams.schema import ExamMedicalReview, ExamUpdate
from app.modules.exams.service import (
    cancel_exam,
    claim_exam_for_analysis,
    restore_exam,
    review_exam,
    update_exam,
)
from app.modules.exams.state_machine import (
    EXAM_STATUS_NAMES,
    EXAM_TRANSITION_TABLE,
    ExamTransitionAction,
    FINAL_EXAM_STATUSES,
    get_transition_target,
)
from app.modules.patients.model import Patient
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


EXPECTED_TRANSITIONS = {
    (None, "create", "pending"),
    ("pending", "start_processing", "processing"),
    ("pending", "cancel", "canceled"),
    ("pending", "replace_file", "pending"),
    ("processing", "cancel", "canceled"),
    ("processing", "analysis_succeeded", "awaiting_review"),
    ("processing", "analysis_failed", "failed"),
    ("failed", "restore", "pending"),
    ("canceled", "restore", "pending"),
    ("awaiting_review", "review_confirm", "completed"),
    ("awaiting_review", "review_divergence", "completed_with_divergence"),
}

RN07_RN25_COVERAGE = {
    7: "backend/tests/test_patients_api.py::CPF único por clínica",
    8: "test_transition_table_is_complete",
    9: "test_ai_success_is_atomic_and_idempotent",
    10: "test_review_is_unique_and_final",
    11: "test_final_states_are_terminal",
    12: "test_cancel_and_restore_are_idempotent",
    13: "test_cancel_and_restore_are_idempotent",
    14: "test_every_unspecified_transition_is_rejected",
    15: "test_review_is_unique_and_final",
    16: "test_ai_success_is_atomic_and_idempotent",
    17: "test_ai_success_is_atomic_and_idempotent",
    18: "test_ai_success_is_atomic_and_idempotent",
    19: "test_ai_success_is_atomic_and_idempotent",
    20: "test_ai_success_is_atomic_and_idempotent",
    21: "test_status_changes_are_audited_once",
    22: "backend/tests/test_users_api.py::usuário inativo",
    23: "backend/tests/test_rbac_route_matrix.py::matriz protegida",
    24: "test_status_changes_are_audited_once",
    25: "test_cancel_and_restore_are_idempotent",
}


def _seed_exam_context(db_session, *, status_name: str = "pending"):
    status_names = [
        "pending",
        "processing",
        "awaiting_review",
        "completed",
        "completed_with_divergence",
        "failed",
        "canceled",
    ]
    exam_statuses = {
        name: Status(name=name, display_name=name, applies_to="exam") for name in status_names
    }
    active_user = Status(name="active", display_name="Ativo", applies_to="user")
    active_clinic = Status(name="active", display_name="Ativa", applies_to="clinic")
    active_patient = Status(name="active", display_name="Ativo", applies_to="patient")
    completed_ai = Status(name="completed", display_name="Concluída", applies_to="ai_analysis")
    doctor_role = Role(name="doctor", display_name="Médico", permissions_initialized=True)
    clinic = Clinic(name="Clínica CHK09", cnpj="11222333000181", status=active_clinic)
    doctor = User(
        name="Médico CHK09",
        email="medico.chk09@example.com",
        cpf="52998224725",
        password_hash="not-used-in-this-test",
        role=doctor_role,
        status=active_user,
        clinic=clinic,
    )
    patient = Patient(
        name="Paciente CHK09",
        cpf="16899535009",
        clinic=clinic,
        doctor=doctor,
        status=active_patient,
        birth_date=date(1992, 9, 9),
        sex="not_informed",
        phone="88999991004",
    )
    db_session.add_all(
        [
            *exam_statuses.values(),
            active_user,
            active_clinic,
            active_patient,
            completed_ai,
            doctor_role,
            clinic,
            doctor,
            patient,
        ]
    )
    db_session.flush()
    exam = Exam(
        clinic=clinic,
        patient=patient,
        doctor=doctor,
        status=exam_statuses[status_name],
        exam_type="colonoscopy",
        description="Exame CHK09",
        file_path="placeholder.jpg",
        file_name="placeholder.jpg",
        file_mime_type="image/jpeg",
    )
    db_session.add(exam)
    db_session.commit()
    db_session.refresh(exam)
    return SimpleNamespace(
        exam=exam,
        doctor=doctor,
        statuses=exam_statuses,
        completed_ai=completed_ai,
    )


def test_transition_table_is_complete() -> None:
    assert EXAM_STATUS_NAMES == {
        "pending",
        "processing",
        "awaiting_review",
        "completed",
        "completed_with_divergence",
        "failed",
        "canceled",
    }
    rendered = {
        (source, action.value, target)
        for (source, action), target in EXAM_TRANSITION_TABLE.items()
    }
    assert rendered == EXPECTED_TRANSITIONS
    assert set(RN07_RN25_COVERAGE) == set(range(7, 26))


def test_every_unspecified_transition_is_rejected() -> None:
    sources = [None, *sorted(EXAM_STATUS_NAMES)]
    for source in sources:
        for action in ExamTransitionAction:
            key = (source, action)
            if key in EXAM_TRANSITION_TABLE:
                assert get_transition_target(source, action) == EXAM_TRANSITION_TABLE[key]
            else:
                with pytest.raises(HTTPException) as error:
                    get_transition_target(source, action)
                assert error.value.status_code == 409


def test_final_states_are_terminal() -> None:
    assert FINAL_EXAM_STATUSES == {"completed", "completed_with_divergence"}
    for state in FINAL_EXAM_STATUSES:
        for action in ExamTransitionAction:
            with pytest.raises(HTTPException) as error:
                get_transition_target(state, action)
            assert error.value.status_code == 409


def test_analysis_claim_rejects_duplicate_request(db_session) -> None:
    context = _seed_exam_context(db_session)
    claim_exam_for_analysis(db_session, context.exam.id)
    with pytest.raises(HTTPException) as error:
        claim_exam_for_analysis(db_session, context.exam.id)
    assert error.value.status_code == 409
    assert "andamento" in error.value.detail


def test_cancel_and_restore_are_idempotent(db_session, tmp_path, monkeypatch) -> None:
    context = _seed_exam_context(db_session)
    data_root = tmp_path / "data"
    upload_root = data_root / "exams"
    monkeypatch.setattr(file_storage, "DATA_DIR", data_root)
    monkeypatch.setattr(file_storage, "UPLOAD_DIR", upload_root)

    image = (
        upload_root
        / str(context.exam.clinic_id)
        / str(context.exam.patient_id)
        / str(context.exam.id)
        / "original"
        / "exam.jpg"
    )
    image.parent.mkdir(parents=True)
    image.write_bytes(b"fake-image")

    context.exam.file_path = file_storage.serialize_exam_file_path(image)
    db_session.commit()

    first_cancel = cancel_exam(db_session, context.exam.id, context.doctor)
    second_cancel = cancel_exam(db_session, context.exam.id, context.doctor)
    assert first_cancel["status_name"] == second_cancel["status_name"] == "canceled"
    assert db_session.query(AuditLog).filter(AuditLog.action == "cancel_exam").count() == 1

    first_restore = restore_exam(db_session, context.exam.id, context.doctor)
    second_restore = restore_exam(db_session, context.exam.id, context.doctor)
    assert first_restore["status_name"] == second_restore["status_name"] == "pending"
    assert db_session.query(AuditLog).filter(AuditLog.action == "restore_exam").count() == 1


def test_ai_success_is_atomic_and_idempotent(db_session) -> None:
    context = _seed_exam_context(db_session, status_name="processing")
    context.exam.analysis_in_progress = True
    context.exam.analysis_started_at = datetime.now(timezone.utc)
    db_session.commit()
    payload = AIAnalysisCreate(
        exam_id=context.exam.id,
        prediction_label="abnormal",
        prediction_class=1,
        confidence=0.94,
        model_name="clinicai_stacking",
        model_version="p2-seed2024",
        gradcam_path="gradcam.png",
        processing_time_ms=25,
    )
    result = create_ai_analysis(db_session, payload, context.doctor)
    assert result["exam_id"] == context.exam.id
    db_session.expire_all()
    exam = db_session.get(Exam, context.exam.id)
    assert exam.status.name == "awaiting_review"
    assert exam.analysis_in_progress is False
    assert exam.analysis_started_at is None
    assert db_session.query(AIAnalysis).filter_by(exam_id=exam.id).count() == 1

    with pytest.raises(HTTPException) as error:
        create_ai_analysis(db_session, payload, context.doctor)
    assert error.value.status_code == 409
    assert db_session.query(AIAnalysis).filter_by(exam_id=exam.id).count() == 1


def test_cancel_wins_over_late_ai_result(db_session) -> None:
    context = _seed_exam_context(db_session, status_name="processing")
    cancel_exam(db_session, context.exam.id, context.doctor)
    payload = AIAnalysisCreate(
        exam_id=context.exam.id,
        prediction_label="normal",
        prediction_class=0,
        confidence=0.9,
        model_name="clinicai_stacking",
        model_version="p2-seed2024",
    )
    with pytest.raises(HTTPException) as error:
        create_ai_analysis(db_session, payload, context.doctor)
    assert error.value.status_code == 409
    assert db_session.query(AIAnalysis).filter_by(exam_id=context.exam.id).count() == 0


def test_review_is_unique_and_final(db_session) -> None:
    context = _seed_exam_context(db_session, status_name="awaiting_review")
    analysis = AIAnalysis(
        exam=context.exam,
        status=context.completed_ai,
        prediction_label="abnormal",
        prediction_class=1,
        confidence=0.9,
        model_name="clinicai_stacking",
        model_version="p2-seed2024",
    )
    db_session.add(analysis)
    db_session.commit()
    payload = ExamMedicalReview(
        findings="Achados compatíveis.",
        conclusion="Conclusão médica.",
        has_discrepancy=False,
    )
    first = review_exam(db_session, context.exam.id, payload, context.doctor)
    assert first["status_name"] == "completed"
    with pytest.raises(HTTPException) as error:
        review_exam(db_session, context.exam.id, payload, context.doctor)
    assert error.value.status_code == 409
    assert db_session.query(AuditLog).filter(AuditLog.action == "review_exam").count() == 1


def test_final_exam_metadata_cannot_be_edited(db_session) -> None:
    context = _seed_exam_context(db_session, status_name="completed")
    with pytest.raises(HTTPException) as error:
        update_exam(
            db_session,
            context.exam.id,
            ExamUpdate(description="Tentativa tardia"),
            context.doctor,
        )
    assert error.value.status_code == 409


def test_status_changes_are_audited_once(db_session, tmp_path, monkeypatch) -> None:
    context = _seed_exam_context(db_session)
    data_root = tmp_path / "data"
    upload_root = data_root / "exams"
    monkeypatch.setattr(file_storage, "DATA_DIR", data_root)
    monkeypatch.setattr(file_storage, "UPLOAD_DIR", upload_root)

    image = (
        upload_root
        / str(context.exam.clinic_id)
        / str(context.exam.patient_id)
        / str(context.exam.id)
        / "original"
        / "exam.jpg"
    )
    image.parent.mkdir(parents=True)
    image.write_bytes(b"fake-image")

    context.exam.file_path = file_storage.serialize_exam_file_path(image)
    db_session.commit()

    cancel_exam(db_session, context.exam.id, context.doctor)
    restore_exam(db_session, context.exam.id, context.doctor)
    events = (
        db_session.query(AuditLog)
        .filter(AuditLog.entity == "exam", AuditLog.entity_id == context.exam.id)
        .order_by(AuditLog.id)
        .all()
    )
    assert [event.action for event in events] == ["cancel_exam", "restore_exam"]
    for event in events:
        assert event.old_data["status_name"]
        assert event.new_data["status_name"]
        assert event.new_data["transition_action"]


def test_processing_exam_metadata_cannot_be_edited(db_session) -> None:
    context = _seed_exam_context(db_session, status_name="processing")
    context.exam.analysis_in_progress = True
    context.exam.analysis_started_at = datetime.now(timezone.utc)
    db_session.commit()

    with pytest.raises(HTTPException) as error:
        update_exam(
            db_session,
            context.exam.id,
            ExamUpdate(description="Tentativa durante processamento"),
            context.doctor,
        )

    assert error.value.status_code == 409


def test_pending_exam_metadata_can_be_edited(
    db_session,
) -> None:
    context = _seed_exam_context(
        db_session,
        status_name="pending",
    )

    result = update_exam(
        db_session,
        context.exam.id,
        ExamUpdate(description="Exame pendente editado"),
        context.doctor,
    )

    assert result["description"] == "Exame pendente editado"


def test_failed_exam_metadata_cannot_be_edited(
    db_session,
) -> None:
    context = _seed_exam_context(
        db_session,
        status_name="failed",
    )

    with pytest.raises(HTTPException) as error:
        update_exam(
            db_session,
            context.exam.id,
            ExamUpdate(description="Tentativa após falha"),
            context.doctor,
        )

    assert error.value.status_code == 409
