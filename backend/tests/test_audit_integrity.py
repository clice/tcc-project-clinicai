"""CHK-11 — cobertura, privacidade e atomicidade dos logs de auditoria."""

from __future__ import annotations

import json
import struct
import zlib
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.core.security import get_password_hash
from app.modules.ai_analyses.model import AIAnalysis
from app.modules.ai_analyses.schema import (
    AIAnalysisCreate,
    AIAnalysisUpdate,
)
from app.modules.ai_analyses.service import (
    create_ai_analysis,
    update_ai_analysis,
)
from app.modules.audit_logs.model import AuditLog
from app.modules.audit_logs.service import sanitize_audit_data
from app.modules.auth.service import authenticate_user
from app.modules.clinics.model import Clinic
from app.modules.exams import file_storage
from app.modules.exams.model import Exam
from app.modules.exams.schema import ExamCreate, ExamMedicalReview
from app.modules.exams.service import (
    claim_exam_for_analysis,
    create_exam,
    download_exam_file,
    mark_exam_ai_failed,
    review_exam,
)
from app.modules.patients.model import Patient
from app.modules.patients.schema import PatientUpdate
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def make_png(width: int = 2, height: int = 2) -> bytes:
    """Gera uma imagem PNG pequena e estruturalmente válida."""

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    rows = b"".join(b"\x00" + (b"\x14\x1e\x28" * width) for _ in range(height))
    return (
        PNG_SIGNATURE
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(rows))
        + _png_chunk(b"IEND", b"")
    )


def upload(data: bytes, *, filename: str = "imagem.png") -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=filename,
        headers=Headers({"content-type": "image/png"}),
    )


def _audit_blob(log: AuditLog) -> str:
    return json.dumps(
        {
            "description": log.description,
            "old_data": log.old_data,
            "new_data": log.new_data,
        },
        ensure_ascii=False,
        default=str,
    ).lower()


def _seed_context(
    db_session,
    *,
    exam_status_name: str = "processing",
    with_ai_analysis: bool = False,
    password: str = "SenhaSegura123!",
):
    statuses = {
        ("active", "user"): Status(
            name="active", display_name="Ativo", applies_to="user"
        ),
        ("active", "clinic"): Status(
            name="active", display_name="Ativa", applies_to="clinic"
        ),
        ("active", "patient"): Status(
            name="active", display_name="Ativo", applies_to="patient"
        ),
        ("processing", "exam"): Status(
            name="processing", display_name="Processando", applies_to="exam"
        ),
        ("pending", "exam"): Status(
            name="pending", display_name="Pendente", applies_to="exam"
        ),
        ("failed", "exam"): Status(
            name="failed", display_name="Falhou", applies_to="exam"
        ),
        ("awaiting_review", "exam"): Status(
            name="awaiting_review", display_name="Aguardando revisão", applies_to="exam"
        ),
        ("completed", "exam"): Status(
            name="completed", display_name="Concluído", applies_to="exam"
        ),
        ("completed_with_divergence", "exam"): Status(
            name="completed_with_divergence",
            display_name="Concluído com divergência",
            applies_to="exam",
        ),
        ("completed", "ai_analysis"): Status(
            name="completed", display_name="Concluída", applies_to="ai_analysis"
        ),
    }
    roles = {
        "admin_master": Role(
            name="admin_master",
            display_name="Administrador Master",
            permissions_initialized=True,
        ),
        "clinic_manager": Role(
            name="clinic_manager",
            display_name="Gestor",
            permissions_initialized=True,
        ),
        "doctor": Role(
            name="doctor",
            display_name="Médico",
            permissions_initialized=True,
        ),
    }
    password_hash = get_password_hash(password)
    clinic = Clinic(
        name="Clínica Auditoria",
        cnpj="11222333000181",
        email="auditoria.clinica@example.com",
        status=statuses[("active", "clinic")],
    )
    doctor = User(
        name="Médico Auditor",
        email="medico.auditoria@example.com",
        cpf="52998224725",
        password_hash=password_hash,
        role=roles["doctor"],
        status=statuses[("active", "user")],
        clinic=clinic,
    )
    manager = User(
        name="Gestor Auditor",
        email="manager.auditoria@example.com",
        cpf="12345678909",
        password_hash=password_hash,
        role=roles["clinic_manager"],
        status=statuses[("active", "user")],
        clinic=clinic,
    )
    admin = User(
        name="Administrador Auditor",
        email="admin.auditoria@example.com",
        cpf="39053344705",
        password_hash=password_hash,
        role=roles["admin_master"],
        status=statuses[("active", "user")],
        clinic=None,
    )
    patient = Patient(
        name="Paciente Auditoria",
        cpf="16899535009",
        clinic=clinic,
        doctor=doctor,
        status=statuses[("active", "patient")],
    )
    exam = Exam(
        clinic=clinic,
        patient=patient,
        doctor=doctor,
        status=statuses[(exam_status_name, "exam")],
        exam_type="colonoscopy",
        description="Exame de auditoria",
        file_path="/tmp/exame-auditoria.png",
        file_name="exame-auditoria.png",
        file_mime_type="image/png",
    )

    db_session.add_all([*statuses.values(), *roles.values(), clinic, doctor, manager, admin, patient, exam])
    db_session.flush()

    if with_ai_analysis:
        db_session.add(
            AIAnalysis(
                exam=exam,
                status=statuses[("completed", "ai_analysis")],
                prediction_label="normal",
                prediction_class=0,
                confidence=0.95,
                model_name="clinicai_stacking",
                model_version="chk11",
            )
        )

    db_session.commit()
    return {
        "statuses": statuses,
        "roles": roles,
        "clinic": clinic,
        "doctor": doctor,
        "manager": manager,
        "admin": admin,
        "patient": patient,
        "exam": exam,
        "password": password,
    }


def test_sanitizer_removes_nested_credentials_tokens_paths_and_image_payloads() -> None:
    image_payload = "A" * 512
    sanitized = sanitize_audit_data(
        {
            "password": "segredo",
            "new_password": "novo-segredo",
            "token": "token-secreto",
            "token_version": 7,
            "nested": {
                "refresh_token": "refresh-secreto",
                "image_base64": image_payload,
                "raw_response": {"image": image_payload},
                "file_path": "/dados/privados/exame.png",
                "safe": "preservado",
            },
            "message": (
                "Bearer abc.def.ghi password=segredo "
                f"data:image/png;base64,{image_payload}"
            ),
        }
    )

    assert "password" not in sanitized
    assert "new_password" not in sanitized
    assert "token" not in sanitized
    assert sanitized["token_version"] == 7
    assert sanitized["nested"] == {"safe": "preservado"}
    assert "segredo" not in sanitized["message"].lower()
    assert "abc.def.ghi" not in sanitized["message"]
    assert image_payload not in sanitized["message"]
    assert "redacted" in sanitized["message"].lower()


def test_login_success_and_failure_are_audited_without_password_or_token(db_session) -> None:
    context = _seed_context(db_session)

    with pytest.raises(HTTPException) as failed:
        authenticate_user(
            db_session,
            email=context["admin"].email,
            password="senha-incorreta",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
    assert failed.value.status_code == 401

    authenticated = authenticate_user(
        db_session,
        email=context["admin"].email,
        password=context["password"],
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    assert authenticated.id == context["admin"].id

    logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.entity == "auth")
        .order_by(AuditLog.id.asc())
        .all()
    )
    assert [log.action for log in logs] == ["login_failed", "login_success"]
    for log in logs:
        blob = _audit_blob(log)
        assert context["password"].lower() not in blob
        assert "senha-incorreta" not in blob
        assert "access_token" not in blob
        assert "refresh_token" not in blob


def test_exam_creation_upload_and_download_have_distinct_safe_logs(
    db_session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _seed_context(db_session)
    upload_root = tmp_path / "uploads" / "exams"
    monkeypatch.setattr(file_storage, "UPLOAD_DIR", upload_root)

    created = create_exam(
        db_session,
        ExamCreate(
            clinic_id=context["clinic"].id,
            patient_id=context["patient"].id,
            doctor_id=context["doctor"].id,
            exam_type="colonoscopy",
            description="Exame com upload auditado",
        ),
        upload(make_png(3, 4), filename="nome-original.png"),
        context["doctor"],
    )

    logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.entity == "exam", AuditLog.entity_id == created["id"])
        .order_by(AuditLog.id.asc())
        .all()
    )
    assert [log.action for log in logs] == ["create", "upload"]
    assert logs[0].new_data["status_name"] == "pending"
    assert logs[1].new_data["file_mime_type"] == "image/png"
    assert logs[1].new_data["image_width"] == 3
    assert logs[1].new_data["image_height"] == 4

    response = download_exam_file(db_session, created["id"], context["doctor"])
    assert Path(response.path).is_file()

    download_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "exam",
            AuditLog.entity_id == created["id"],
            AuditLog.action == "download",
        )
        .one()
    )
    assert "file_path" not in (download_log.new_data or {})
    assert download_log.new_data["file_name"] == created["file_name"]

    for log in [*logs, download_log]:
        blob = _audit_blob(log)
        assert "data:image" not in blob
        assert "image_base64" not in blob
        assert str(response.path).lower() not in blob


def test_analysis_claim_and_its_log_rollback_together(
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _seed_context(db_session, exam_status_name="pending")
    exam_id = context["exam"].id

    from app.modules.exams import service as exams_service

    def fail_audit(*args, **kwargs):
        raise RuntimeError("falha de auditoria simulada")

    with monkeypatch.context() as patch:
        patch.setattr(exams_service, "create_audit_log", fail_audit)
        with pytest.raises(RuntimeError, match="falha de auditoria simulada"):
            claim_exam_for_analysis(
                db_session,
                exam_id,
                current_user=context["doctor"],
            )

    db_session.expire_all()
    exam = db_session.get(Exam, exam_id)
    assert exam is not None
    assert exam.status.name == "pending"
    assert exam.analysis_in_progress is False
    assert exam.analysis_started_at is None
    assert (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "exam",
            AuditLog.entity_id == exam_id,
            AuditLog.action == "run_ai_analysis",
        )
        .count()
        == 0
    )

    claim_exam_for_analysis(
        db_session,
        exam_id,
        current_user=context["doctor"],
    )
    db_session.expire_all()
    exam = db_session.get(Exam, exam_id)
    assert exam.status.name == "processing"
    assert exam.analysis_in_progress is True
    claim_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "exam",
            AuditLog.entity_id == exam_id,
            AuditLog.action == "run_ai_analysis",
        )
        .one()
    )
    assert claim_log.new_data["phase"] == "started"
    assert claim_log.new_data["analysis_in_progress"] is True


def test_ai_success_failure_and_update_logs_do_not_store_raw_or_gradcam_payloads(
    db_session,
) -> None:
    success = _seed_context(db_session)
    image_payload = "A" * 512

    created = create_ai_analysis(
        db_session,
        AIAnalysisCreate(
            exam_id=success["exam"].id,
            prediction_label="normal",
            prediction_class=0,
            confidence=0.97,
            model_name="clinicai_stacking",
            model_version="p2-seed-2024",
            gradcam_path="/dados/gradcam/sensivel.png",
            processing_time_ms=123,
            raw_response=f'{{"image_base64":"{image_payload}"}}',
        ),
        success["doctor"],
    )

    success_logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "run_ai_analysis")
        .order_by(AuditLog.id.asc())
        .all()
    )
    assert len(success_logs) == 2
    assert {log.entity for log in success_logs} == {"ai_analysis", "exam"}
    for log in success_logs:
        blob = _audit_blob(log)
        assert "gradcam/sensivel" not in blob
        assert image_payload.lower() not in blob
        assert "raw_response" not in blob

    update_ai_analysis(
        db_session,
        created["id"],
        AIAnalysisUpdate(
            gradcam_path="/dados/gradcam/novo-sensivel.png",
            raw_response=f'{{"token":"segredo","image":"{image_payload}"}}',
        ),
        success["doctor"],
    )
    update_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.action == "update",
            AuditLog.entity == "ai_analysis",
            AuditLog.entity_id == created["id"],
        )
        .one()
    )
    assert update_log.new_data["gradcam_updated"] is True
    assert update_log.new_data["gradcam_available"] is True
    assert update_log.new_data["raw_response_updated"] is True
    assert update_log.new_data["raw_response_available"] is True
    blob = _audit_blob(update_log)
    assert "novo-sensivel" not in blob
    assert image_payload.lower() not in blob
    assert "segredo" not in blob

    failure_exam = Exam(
        clinic=success["clinic"],
        patient=success["patient"],
        doctor=success["doctor"],
        status=success["statuses"][("processing", "exam")],
        exam_type="colonoscopy",
        description="Exame com falha de IA",
        file_path="/tmp/exame-falha-auditoria.png",
        file_name="exame-falha-auditoria.png",
        file_mime_type="image/png",
    )
    db_session.add(failure_exam)
    db_session.commit()
    failed_exam_id = failure_exam.id
    mark_exam_ai_failed(
        db_session,
        failed_exam_id,
        error_message=(
            "Bearer token.super.secreto password=nao-gravar "
            f"data:image/png;base64,{image_payload}"
        ),
    )
    failed_exam = db_session.get(Exam, failed_exam_id)
    db_session.refresh(failed_exam)
    assert failed_exam.status.name == "failed"
    failure_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.action == "ai_analysis_failed",
            AuditLog.entity == "exam",
            AuditLog.entity_id == failed_exam_id,
        )
        .one()
    )
    failure_blob = _audit_blob(failure_log)
    assert "token.super.secreto" not in failure_blob
    assert "nao-gravar" not in failure_blob
    assert image_payload.lower() not in failure_blob
    assert failure_log.old_data["status_name"] == "processing"
    assert failure_log.new_data["status_name"] == "failed"


def test_medical_review_records_old_and_new_values(db_session) -> None:
    context = _seed_context(
        db_session,
        exam_status_name="awaiting_review",
        with_ai_analysis=True,
    )

    result = review_exam(
        db_session,
        context["exam"].id,
        ExamMedicalReview(
            findings="Achado clínico revisado.",
            conclusion="Conclusão médica revisada.",
            has_discrepancy=True,
        ),
        context["doctor"],
    )
    assert result["status_name"] == "completed_with_divergence"

    log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.action == "review_exam",
            AuditLog.entity == "exam",
            AuditLog.entity_id == context["exam"].id,
        )
        .one()
    )
    assert log.old_data["findings"] is None
    assert log.old_data["conclusion"] is None
    assert log.new_data["findings"] == "Achado clínico revisado."
    assert log.new_data["conclusion"] == "Conclusão médica revisada."
    assert log.new_data["reviewed_by_id"] == context["doctor"].id
    assert log.new_data["reviewed_at"]
    assert log.new_data["status_name"] == "completed_with_divergence"


def test_patient_edit_and_log_are_not_partially_committed(
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _seed_context(db_session)
    patient_id = context["patient"].id

    from app.modules.patients import service as patients_service

    def fail_audit(*args, **kwargs):
        raise RuntimeError("falha de log simulada")

    with monkeypatch.context() as patch:
        patch.setattr(patients_service, "create_audit_log", fail_audit)
        with pytest.raises(RuntimeError, match="falha de log simulada"):
            patients_service.update_patient(
                db_session,
                patient_id,
                PatientUpdate(name="Paciente não persistido"),
                context["manager"],
            )

    db_session.rollback()
    db_session.expire_all()
    patient = db_session.get(Patient, patient_id)
    assert patient.name == "Paciente Auditoria"
    assert (
        db_session.query(AuditLog)
        .filter(AuditLog.entity == "patient", AuditLog.action == "update")
        .count()
        == 0
    )

    patients_service.update_patient(
        db_session,
        patient_id,
        PatientUpdate(name="Paciente persistido com log"),
        context["manager"],
    )
    db_session.expire_all()
    patient = db_session.get(Patient, patient_id)
    assert patient.name == "Paciente persistido com log"
    assert (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "patient",
            AuditLog.entity_id == patient_id,
            AuditLog.action == "update",
        )
        .count()
        == 1
    )


def test_rbac_sync_and_log_rollback_together(
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _seed_context(db_session)
    target_role = context["roles"]["clinic_manager"]
    read_permission = Permission(
        name="patients:read",
        display_name="Ler pacientes",
        module="patients",
    )
    update_permission = Permission(
        name="patients:update",
        display_name="Editar pacientes",
        module="patients",
    )
    db_session.add_all([read_permission, update_permission])
    db_session.flush()
    db_session.add(
        RolePermission(role_id=target_role.id, permission_id=read_permission.id)
    )
    db_session.commit()

    from app.modules.role_permissions import service as role_permissions_service

    def fail_audit(*args, **kwargs):
        raise RuntimeError("falha de auditoria RBAC simulada")

    with monkeypatch.context() as patch:
        patch.setattr(role_permissions_service, "create_audit_log", fail_audit)
        with pytest.raises(RuntimeError, match="falha de auditoria RBAC simulada"):
            role_permissions_service.sync_role_permissions(
                db_session,
                target_role.id,
                [update_permission.id],
                context["admin"],
            )

    db_session.expire_all()
    remaining_ids = {
        permission_id
        for (permission_id,) in db_session.query(RolePermission.permission_id)
        .filter(RolePermission.role_id == target_role.id)
        .all()
    }
    assert remaining_ids == {read_permission.id}
    assert (
        db_session.query(AuditLog)
        .filter(AuditLog.entity == "role_permission", AuditLog.action == "update")
        .count()
        == 0
    )

    role_permissions_service.sync_role_permissions(
        db_session,
        target_role.id,
        [update_permission.id],
        context["admin"],
    )
    log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "role_permission",
            AuditLog.entity_id == target_role.id,
            AuditLog.action == "update",
        )
        .one()
    )
    assert log.old_data == {"permission_ids": [read_permission.id]}
    assert log.new_data == {"permission_ids": [update_permission.id]}
