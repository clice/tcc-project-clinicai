"""CHK-09 — testes de concorrência real usando PostgreSQL."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import joinedload, sessionmaker

from app.modules.ai_analyses.model import AIAnalysis
from app.modules.audit_logs.model import AuditLog
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.exams.schema import ExamMedicalReview
from app.modules.exams.service import claim_exam_for_analysis, review_exam
from app.modules.patients.model import Patient
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL não informado; teste exclusivo do PostgreSQL.",
)


@pytest.fixture(scope="module")
def pg_session_factory():
    """Cria sessões independentes para o banco temporário da CHK-09."""

    assert TEST_DATABASE_URL is not None

    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
    )

    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=True,
    )

    try:
        yield factory
    finally:
        engine.dispose()


def _unique_digits(length: int) -> str:
    """Gera uma sequência numérica para campos únicos do cenário."""

    return str(uuid4().int % (10**length)).zfill(length)


def _get_or_create_status(
    db,
    *,
    name: str,
    applies_to: str,
) -> Status:
    status = (
        db.query(Status)
        .filter(
            Status.name == name,
            Status.applies_to == applies_to,
        )
        .one_or_none()
    )

    if status:
        return status

    status = Status(
        name=name,
        display_name=name.replace("_", " ").title(),
        applies_to=applies_to,
    )

    db.add(status)
    db.flush()

    return status


def _get_or_create_doctor_role(db) -> Role:
    role = db.query(Role).filter(Role.name == "doctor").one_or_none()

    if role:
        return role

    role = Role(
        name="doctor",
        display_name="Médico",
        permissions_initialized=True,
    )

    db.add(role)
    db.flush()

    return role


def _seed_exam(
    session_factory,
    *,
    status_name: str,
    with_ai_analysis: bool = False,
) -> tuple[int, int]:
    """Cria um exame independente para cada cenário concorrente."""

    suffix = uuid4().hex[:12]

    with session_factory() as db:
        active_user = _get_or_create_status(
            db,
            name="active",
            applies_to="user",
        )
        active_clinic = _get_or_create_status(
            db,
            name="active",
            applies_to="clinic",
        )
        active_patient = _get_or_create_status(
            db,
            name="active",
            applies_to="patient",
        )

        pending = _get_or_create_status(
            db,
            name="pending",
            applies_to="exam",
        )
        processing = _get_or_create_status(
            db,
            name="processing",
            applies_to="exam",
        )
        awaiting_review = _get_or_create_status(
            db,
            name="awaiting_review",
            applies_to="exam",
        )
        _get_or_create_status(
            db,
            name="completed",
            applies_to="exam",
        )
        _get_or_create_status(
            db,
            name="completed_with_divergence",
            applies_to="exam",
        )

        completed_ai = _get_or_create_status(
            db,
            name="completed",
            applies_to="ai_analysis",
        )

        doctor_role = _get_or_create_doctor_role(db)

        exam_statuses = {
            "pending": pending,
            "processing": processing,
            "awaiting_review": awaiting_review,
        }

        clinic = Clinic(
            name=f"Clínica concorrência {suffix}",
            cnpj=_unique_digits(14),
            email=f"clinica-{suffix}@example.com",
            status=active_clinic,
        )

        doctor = User(
            name=f"Médico concorrência {suffix}",
            email=f"medico-{suffix}@example.com",
            cpf=_unique_digits(11),
            password_hash="hash-nao-utilizado-no-teste",
            role=doctor_role,
            status=active_user,
            clinic=clinic,
        )

        patient = Patient(
            name=f"Paciente concorrência {suffix}",
            cpf=_unique_digits(11),
            clinic=clinic,
            doctor=doctor,
            status=active_patient,
        )

        exam = Exam(
            clinic=clinic,
            patient=patient,
            doctor=doctor,
            status=exam_statuses[status_name],
            exam_type="colonoscopy",
            description=f"Exame concorrência {suffix}",
            file_path=f"/tmp/exam-{suffix}.jpg",
            file_name=f"exam-{suffix}.jpg",
            file_mime_type="image/jpeg",
        )

        db.add_all([clinic, doctor, patient, exam])
        db.flush()

        if with_ai_analysis:
            db.add(
                AIAnalysis(
                    exam=exam,
                    status=completed_ai,
                    prediction_label="normal",
                    prediction_class=0,
                    confidence=0.95,
                    model_name="clinicai_stacking",
                    model_version="chk09",
                )
            )

        db.commit()

        return exam.id, doctor.id


def test_only_one_postgresql_session_claims_analysis(
    pg_session_factory,
) -> None:
    """Duas sessões simultâneas não podem adquirir o mesmo claim."""

    exam_id, _ = _seed_exam(
        pg_session_factory,
        status_name="pending",
    )

    barrier = Barrier(2)

    def attempt_claim() -> tuple[str, int | None]:
        with pg_session_factory() as db:
            barrier.wait(timeout=10)

            try:
                claim_exam_for_analysis(db=db, exam_id=exam_id)
                return "claimed", None
            except HTTPException as exc:
                return "rejected", exc.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(attempt_claim) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]

    assert results.count(("claimed", None)) == 1
    assert results.count(("rejected", 409)) == 1

    with pg_session_factory() as db:
        exam = db.get(Exam, exam_id)

        assert exam is not None
        assert exam.status.name == "processing"
        assert exam.analysis_in_progress is True
        assert exam.analysis_started_at is not None


def test_only_one_postgresql_session_reviews_exam(
    pg_session_factory,
) -> None:
    """FOR UPDATE deve permitir uma única revisão médica."""

    exam_id, doctor_id = _seed_exam(
        pg_session_factory,
        status_name="awaiting_review",
        with_ai_analysis=True,
    )

    barrier = Barrier(2)

    def attempt_review() -> tuple[str, str | int]:
        with pg_session_factory() as db:
            doctor = (
                db.query(User)
                .options(
                    joinedload(User.role),
                    joinedload(User.status),
                )
                .filter(User.id == doctor_id)
                .one()
            )

            payload = ExamMedicalReview(
                findings="Achados clínicos concorrentes.",
                conclusion="Conclusão clínica concorrente.",
                has_discrepancy=False,
            )

            barrier.wait(timeout=10)

            try:
                result = review_exam(
                    db=db,
                    exam_id=exam_id,
                    payload=payload,
                    current_user=doctor,
                )
                return "reviewed", result["status_name"]
            except HTTPException as exc:
                return "rejected", exc.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(attempt_review) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]

    assert results.count(("reviewed", "completed")) == 1
    assert results.count(("rejected", 409)) == 1

    with pg_session_factory() as db:
        exam = (
            db.query(Exam)
            .options(joinedload(Exam.status))
            .filter(Exam.id == exam_id)
            .one()
        )

        review_logs = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity == "exam",
                AuditLog.entity_id == exam_id,
                AuditLog.action == "review_exam",
            )
            .count()
        )

        assert exam.status.name == "completed"
        assert exam.reviewed_by_id == doctor_id
        assert review_logs == 1
