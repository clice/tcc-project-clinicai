"""Auditoria da geração e do download do relatório PDF."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.common.constants import (
    AuditAction,
    AuditEntity,
)
from app.modules.exams import pdf_report
from app.modules.exams import service as exams_service


class FakeSession:
    """Sessão mínima para testar a fronteira transacional."""

    def __init__(self) -> None:
        self.commit_count = 0

    def commit(self) -> None:
        self.commit_count += 1


def build_user(
    *,
    role_name: str = "doctor",
):
    return SimpleNamespace(
        id=10,
        clinic_id=20,
        role=SimpleNamespace(name=role_name),
    )


def build_exam():
    return SimpleNamespace(
        id=30,
        clinic_id=20,
        status=SimpleNamespace(name="completed"),
        file_path=None,
        ai_analysis=SimpleNamespace(
            id=40,
            gradcam_path=None,
        ),
    )


def configure_successful_report(
    monkeypatch,
    *,
    audit_calls: list[dict],
    pdf_content: bytes = b"%PDF-audit-test",
):
    exam = build_exam()

    monkeypatch.setattr(
        exams_service,
        "get_printable_exam_model",
        lambda **kwargs: exam,
    )
    monkeypatch.setattr(
        pdf_report,
        "generate_exam_report_pdf",
        lambda *args, **kwargs: pdf_content,
    )
    monkeypatch.setattr(
        pdf_report,
        "build_exam_report_filename",
        lambda exam: "relatorio-exame-30.pdf",
    )
    monkeypatch.setattr(
        exams_service,
        "create_audit_log",
        lambda **kwargs: audit_calls.append(kwargs),
    )

    return exam


def test_successful_pdf_generation_is_audited_once(
    monkeypatch,
):
    audit_calls: list[dict] = []
    db = FakeSession()
    user = build_user()

    configure_successful_report(
        monkeypatch,
        audit_calls=audit_calls,
    )

    response = (
        exams_service
        .download_exam_print_report_pdf(
            db=db,
            exam_id=30,
            current_user=user,
        )
    )

    assert response.body == b"%PDF-audit-test"
    assert response.media_type == "application/pdf"
    assert db.commit_count == 1
    assert len(audit_calls) == 1

    log = audit_calls[0]

    assert log["user_id"] == user.id
    assert log["clinic_id"] == 20
    assert log["action"] == AuditAction.PRINT_REPORT
    assert log["entity"] == AuditEntity.EXAM
    assert log["entity_id"] == 30

    assert log["new_data"] == {
        "artifact_type": "exam_print_report_pdf",
        "media_type": "application/pdf",
        "delivery_mode": "attachment",
        "exam_status": "completed",
        "actor_role": "doctor",
        "original_image_included": False,
        "gradcam_included": False,
        "ai_analysis_id": 40,
        "report_size_bytes": len(
            b"%PDF-audit-test"
        ),
    }

    serialized = str(log).lower()

    assert "patient" not in serialized
    assert "file_path" not in serialized
    assert "gradcam_path" not in serialized
    assert "findings" not in serialized
    assert "conclusion" not in serialized


def test_unauthorized_print_does_not_create_audit_log(
    monkeypatch,
):
    audit_calls: list[dict] = []
    db = FakeSession()

    def deny_print(**kwargs):
        raise HTTPException(
            status_code=403,
            detail="Acesso negado.",
        )

    monkeypatch.setattr(
        exams_service,
        "get_printable_exam_model",
        deny_print,
    )
    monkeypatch.setattr(
        exams_service,
        "create_audit_log",
        lambda **kwargs: audit_calls.append(kwargs),
    )

    with pytest.raises(HTTPException) as exc_info:
        (
            exams_service
            .download_exam_print_report_pdf(
                db=db,
                exam_id=30,
                current_user=build_user(),
            )
        )

    assert exc_info.value.status_code == 403
    assert audit_calls == []
    assert db.commit_count == 0


def test_pdf_generation_failure_does_not_create_audit_log(
    monkeypatch,
):
    audit_calls: list[dict] = []
    db = FakeSession()

    configure_successful_report(
        monkeypatch,
        audit_calls=audit_calls,
    )

    def fail_generation(*args, **kwargs):
        raise RuntimeError(
            "Falha simulada na geração do PDF."
        )

    monkeypatch.setattr(
        pdf_report,
        "generate_exam_report_pdf",
        fail_generation,
    )

    with pytest.raises(
        RuntimeError,
        match="Falha simulada",
    ):
        (
            exams_service
            .download_exam_print_report_pdf(
                db=db,
                exam_id=30,
                current_user=build_user(),
            )
        )

    assert audit_calls == []
    assert db.commit_count == 0


def test_each_explicit_pdf_request_creates_one_event(
    monkeypatch,
):
    audit_calls: list[dict] = []
    db = FakeSession()

    configure_successful_report(
        monkeypatch,
        audit_calls=audit_calls,
    )

    for _ in range(2):
        (
            exams_service
            .download_exam_print_report_pdf(
                db=db,
                exam_id=30,
                current_user=build_user(),
            )
        )

    assert len(audit_calls) == 2
    assert db.commit_count == 2
