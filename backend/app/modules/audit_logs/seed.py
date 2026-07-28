"""Histórico cronológico da massa acadêmica demonstrativa."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)

from sqlalchemy.orm import Session

from app.common.constants import (
    AuditAction,
    AuditEntity,
    StatusName,
)
from app.common.services import enum_to_value
from app.modules.academic_demo_assets import (
    get_demo_exam_definitions,
)
from app.modules.ai_analyses.model import AIAnalysis
from app.modules.audit_logs.model import AuditLog
from app.modules.audit_logs.service import (
    create_audit_log,
    sanitize_audit_data,
)
from app.modules.exams.model import Exam
from app.modules.exams.state_machine import (
    ExamTransitionAction,
    transition_audit_payload,
)
from app.modules.statuses.model import Status
from app.modules.users.model import User


DEMO_AUDIT_USER_AGENT = (
    "ClinicAI academic_demo seed/v1"
)
DEMO_AUDIT_SOURCE = "academic_demo"
EXPECTED_DEMO_AUDIT_LOG_COUNT = 464

ACADEMIC_DEMO_TIMEZONE = timezone(
    timedelta(hours=-3)
)


@dataclass(frozen=True)
class DemoAuditEvent:
    """Definição determinística de um evento demonstrativo."""

    key: str
    created_at: datetime
    user_id: int
    clinic_id: int
    action: AuditAction
    entity: AuditEntity
    entity_id: int
    description: str
    old_data: dict | None = None
    new_data: dict | None = None


def academic_demo_datetime(
    exam_date: date,
    *,
    hour: int,
    minute: int,
    second: int = 0,
) -> datetime:
    """Converte o horário demonstrativo brasileiro para UTC."""

    local_value = datetime.combine(
        exam_date,
        time(
            hour=hour,
            minute=minute,
            second=second,
            tzinfo=ACADEMIC_DEMO_TIMEZONE,
        ),
    )

    return local_value.astimezone(timezone.utc)


def event_data(
    event_key: str,
    **values: object,
) -> dict[str, object]:
    """Inclui a identidade reservada do evento acadêmico."""

    return {
        "academic_demo": True,
        "demo_event_key": event_key,
        "source": DEMO_AUDIT_SOURCE,
        **values,
    }


def exam_status(
    statuses: dict[str, Status],
    name: str,
) -> Status:
    """Resolve um status de exame pela chave da seed."""

    key = f"exam_{name}"
    status = statuses.get(key)

    if status is None:
        raise RuntimeError(
            f"Status acadêmico ausente: {key}."
        )

    return status


def transition_payload(
    statuses: dict[str, Status],
    *,
    old_name: str,
    new_name: str,
    action: ExamTransitionAction,
    event_key: str,
    **extra: object,
) -> tuple[dict[str, object], dict[str, object]]:
    """Monta o mesmo contrato usado pela máquina de estados."""

    old_status = exam_status(
        statuses,
        old_name,
    )
    new_status = exam_status(
        statuses,
        new_name,
    )

    old_data, new_data = transition_audit_payload(
        old_status_id=old_status.id,
        old_status_name=old_name,
        new_status_id=new_status.id,
        new_status_name=new_name,
        action=action,
        **extra,
    )

    new_data.update(
        event_data(event_key)
    )

    return old_data, new_data


def build_demo_audit_events(
    *,
    exams: dict[str, Exam],
    ai_analyses: dict[str, AIAnalysis],
    users: dict[str, User],
    statuses: dict[str, Status],
) -> list[DemoAuditEvent]:
    """Constrói o ciclo de vida determinístico dos 90 exames."""

    events: list[DemoAuditEvent] = []

    for definition in get_demo_exam_definitions():
        exam_key = str(definition["exam_key"])
        exam = exams[exam_key]
        doctor = users[definition["doctor_key"]]
        final_status = str(definition["status"])
        definition_date = date.fromisoformat(
            definition["exam_date"]
        )

        if exam.doctor_id != doctor.id:
            raise RuntimeError(
                f"{exam_key}: médico divergente."
            )

        if not exam.status:
            raise RuntimeError(
                f"{exam_key}: status não carregado."
            )

        if exam.status.name != final_status:
            raise RuntimeError(
                f"{exam_key}: estado {exam.status.name!r}, "
                f"esperado {final_status!r}."
            )

        created_at = academic_demo_datetime(
            definition_date,
            hour=8,
            minute=45,
        )
        uploaded_at = created_at + timedelta(
            minutes=2
        )

        create_key = f"{exam_key}:exam:create"
        upload_key = f"{exam_key}:exam:upload"

        events.append(
            DemoAuditEvent(
                key=create_key,
                created_at=created_at,
                user_id=doctor.id,
                clinic_id=exam.clinic_id,
                action=AuditAction.CREATE,
                entity=AuditEntity.EXAM,
                entity_id=exam.id,
                description=(
                    "Exame demonstrativo cadastrado."
                ),
                new_data=event_data(
                    create_key,
                    id=exam.id,
                    clinic_id=exam.clinic_id,
                    patient_id=exam.patient_id,
                    doctor_id=exam.doctor_id,
                    status_name=StatusName.PENDING.value,
                    transition_action=(
                        ExamTransitionAction.CREATE.value
                    ),
                    exam_type=exam.exam_type,
                    exam_date=(
                        exam.exam_date.isoformat()
                        if exam.exam_date
                        else None
                    ),
                    description=exam.description,
                ),
            )
        )

        source_asset = definition["source_asset"]

        events.append(
            DemoAuditEvent(
                key=upload_key,
                created_at=uploaded_at,
                user_id=doctor.id,
                clinic_id=exam.clinic_id,
                action=AuditAction.UPLOAD,
                entity=AuditEntity.EXAM,
                entity_id=exam.id,
                description=(
                    "Imagem inicial do exame "
                    "demonstrativo armazenada."
                ),
                new_data=event_data(
                    upload_key,
                    file_name=exam.file_name,
                    file_mime_type=(
                        exam.file_mime_type
                    ),
                    file_size_bytes=int(
                        source_asset["size_bytes"]
                    ),
                    sha256=str(
                        source_asset["sha256"]
                    ),
                ),
            )
        )

        exam.created_at = created_at
        exam.analysis_in_progress = False
        exam.analysis_started_at = None
        final_event_at = uploaded_at

        if final_status == StatusName.PENDING.value:
            if exam_key in ai_analyses:
                raise RuntimeError(
                    f"{exam_key}: exame pendente "
                    "não pode possuir análise."
                )

            exam.reviewed_by_id = None
            exam.reviewed_at = None

        elif final_status == StatusName.CANCELED.value:
            cancel_at = created_at + timedelta(
                minutes=20
            )
            cancel_key = (
                f"{exam_key}:exam:canceled"
            )

            old_data, new_data = transition_payload(
                statuses,
                old_name=StatusName.PENDING.value,
                new_name=StatusName.CANCELED.value,
                action=ExamTransitionAction.CANCEL,
                event_key=cancel_key,
            )

            events.append(
                DemoAuditEvent(
                    key=cancel_key,
                    created_at=cancel_at,
                    user_id=doctor.id,
                    clinic_id=exam.clinic_id,
                    action=AuditAction.CANCEL_EXAM,
                    entity=AuditEntity.EXAM,
                    entity_id=exam.id,
                    description=(
                        "Exame demonstrativo cancelado."
                    ),
                    old_data=old_data,
                    new_data=new_data,
                )
            )

            exam.reviewed_by_id = None
            exam.reviewed_at = None
            final_event_at = cancel_at

        elif final_status == StatusName.FAILED.value:
            started_at = created_at + timedelta(
                minutes=15
            )
            failed_at = started_at + timedelta(
                seconds=12
            )

            start_key = (
                f"{exam_key}:exam:analysis_started"
            )
            failure_key = (
                f"{exam_key}:exam:analysis_failed"
            )

            old_data, new_data = transition_payload(
                statuses,
                old_name=StatusName.PENDING.value,
                new_name=StatusName.PROCESSING.value,
                action=(
                    ExamTransitionAction
                    .START_PROCESSING
                ),
                event_key=start_key,
                phase="started",
                analysis_in_progress=True,
                analysis_started_at=(
                    started_at.isoformat()
                ),
            )

            events.append(
                DemoAuditEvent(
                    key=start_key,
                    created_at=started_at,
                    user_id=doctor.id,
                    clinic_id=exam.clinic_id,
                    action=(
                        AuditAction.RUN_AI_ANALYSIS
                    ),
                    entity=AuditEntity.EXAM,
                    entity_id=exam.id,
                    description=(
                        "Execução demonstrativa da "
                        "análise de IA iniciada."
                    ),
                    old_data=old_data,
                    new_data=new_data,
                )
            )

            old_data, new_data = transition_payload(
                statuses,
                old_name=StatusName.PROCESSING.value,
                new_name=StatusName.FAILED.value,
                action=(
                    ExamTransitionAction
                    .ANALYSIS_FAILED
                ),
                event_key=failure_key,
                failure_category=(
                    "academic_demo_simulated_failure"
                ),
            )

            events.append(
                DemoAuditEvent(
                    key=failure_key,
                    created_at=failed_at,
                    user_id=doctor.id,
                    clinic_id=exam.clinic_id,
                    action=(
                        AuditAction.AI_ANALYSIS_FAILED
                    ),
                    entity=AuditEntity.EXAM,
                    entity_id=exam.id,
                    description=(
                        "Análise de IA demonstrativa "
                        "finalizada com falha simulada."
                    ),
                    old_data=old_data,
                    new_data=new_data,
                )
            )

            exam.reviewed_by_id = None
            exam.reviewed_at = None
            final_event_at = failed_at

        else:
            analysis = ai_analyses.get(exam_key)

            if analysis is None:
                raise RuntimeError(
                    f"{exam_key}: análise acadêmica ausente."
                )

            started_at = created_at + timedelta(
                minutes=15
            )
            completed_at = started_at + timedelta(
                milliseconds=max(
                    1,
                    int(
                        analysis.processing_time_ms
                        or 1
                    ),
                )
            )

            start_key = (
                f"{exam_key}:exam:analysis_started"
            )
            analysis_key = (
                f"{exam_key}:ai_analysis:created"
            )
            completion_key = (
                f"{exam_key}:exam:analysis_completed"
            )

            old_data, new_data = transition_payload(
                statuses,
                old_name=StatusName.PENDING.value,
                new_name=StatusName.PROCESSING.value,
                action=(
                    ExamTransitionAction
                    .START_PROCESSING
                ),
                event_key=start_key,
                phase="started",
                analysis_in_progress=True,
                analysis_started_at=(
                    started_at.isoformat()
                ),
            )

            events.append(
                DemoAuditEvent(
                    key=start_key,
                    created_at=started_at,
                    user_id=doctor.id,
                    clinic_id=exam.clinic_id,
                    action=(
                        AuditAction.RUN_AI_ANALYSIS
                    ),
                    entity=AuditEntity.EXAM,
                    entity_id=exam.id,
                    description=(
                        "Execução demonstrativa da "
                        "análise de IA iniciada."
                    ),
                    old_data=old_data,
                    new_data=new_data,
                )
            )

            events.append(
                DemoAuditEvent(
                    key=analysis_key,
                    created_at=completed_at,
                    user_id=doctor.id,
                    clinic_id=exam.clinic_id,
                    action=(
                        AuditAction.RUN_AI_ANALYSIS
                    ),
                    entity=AuditEntity.AI_ANALYSIS,
                    entity_id=analysis.id,
                    description=(
                        "Análise de IA demonstrativa "
                        "criada para exame."
                    ),
                    new_data=event_data(
                        analysis_key,
                        id=analysis.id,
                        exam_id=exam.id,
                        prediction_label=(
                            analysis.prediction_label
                        ),
                        prediction_class=(
                            analysis.prediction_class
                        ),
                        confidence=analysis.confidence,
                        model_name=analysis.model_name,
                        model_version=(
                            analysis.model_version
                        ),
                        gradcam_available=bool(
                            analysis.gradcam_path
                        ),
                        processing_time_ms=(
                            analysis.processing_time_ms
                        ),
                    ),
                )
            )

            old_data, new_data = transition_payload(
                statuses,
                old_name=StatusName.PROCESSING.value,
                new_name=(
                    StatusName.AWAITING_REVIEW.value
                ),
                action=(
                    ExamTransitionAction
                    .ANALYSIS_SUCCEEDED
                ),
                event_key=completion_key,
                ai_analysis_id=analysis.id,
            )

            events.append(
                DemoAuditEvent(
                    key=completion_key,
                    created_at=completed_at,
                    user_id=doctor.id,
                    clinic_id=exam.clinic_id,
                    action=(
                        AuditAction.RUN_AI_ANALYSIS
                    ),
                    entity=AuditEntity.EXAM,
                    entity_id=exam.id,
                    description=(
                        "Análise de IA demonstrativa "
                        "concluída. Exame movido para "
                        "aguardando revisão médica."
                    ),
                    old_data=old_data,
                    new_data=new_data,
                )
            )

            analysis.created_at = completed_at
            analysis.updated_at = completed_at
            final_event_at = completed_at

            review = definition.get("review")

            if review is None:
                if final_status != (
                    StatusName.AWAITING_REVIEW.value
                ):
                    raise RuntimeError(
                        f"{exam_key}: estado final "
                        "incompatível com ausência "
                        "de revisão."
                    )

                exam.reviewed_by_id = None
                exam.reviewed_at = None

            else:
                reviewed_at = academic_demo_datetime(
                    definition_date,
                    hour=14,
                    minute=30,
                )

                if final_status == (
                    StatusName.COMPLETED.value
                ):
                    review_action = (
                        ExamTransitionAction
                        .REVIEW_CONFIRM
                    )
                elif final_status == (
                    StatusName
                    .COMPLETED_WITH_DIVERGENCE
                    .value
                ):
                    review_action = (
                        ExamTransitionAction
                        .REVIEW_DIVERGENCE
                    )
                else:
                    raise RuntimeError(
                        f"{exam_key}: estado revisado "
                        f"inválido: {final_status}."
                    )

                review_key = (
                    f"{exam_key}:exam:review"
                )

                old_data, new_data = (
                    transition_payload(
                        statuses,
                        old_name=(
                            StatusName
                            .AWAITING_REVIEW
                            .value
                        ),
                        new_name=final_status,
                        action=review_action,
                        event_key=review_key,
                        reviewed_label=str(
                            review[
                                "reviewed_label"
                            ]
                        ),
                        agrees_with_ai=bool(
                            review[
                                "agrees_with_ai"
                            ]
                        ),
                    )
                )

                agrees = bool(
                    review["agrees_with_ai"]
                )

                events.append(
                    DemoAuditEvent(
                        key=review_key,
                        created_at=reviewed_at,
                        user_id=doctor.id,
                        clinic_id=exam.clinic_id,
                        action=(
                            AuditAction.REVIEW_EXAM
                        ),
                        entity=AuditEntity.EXAM,
                        entity_id=exam.id,
                        description=(
                            "Revisão médica demonstrativa "
                            "concluída com concordância."
                            if agrees
                            else
                            "Revisão médica demonstrativa "
                            "concluída com divergência."
                        ),
                        old_data=old_data,
                        new_data=new_data,
                    )
                )

                exam.reviewed_by_id = doctor.id
                exam.reviewed_at = reviewed_at
                final_event_at = reviewed_at

        exam.updated_at = final_event_at

    keys = [event.key for event in events]

    if len(keys) != len(set(keys)):
        raise RuntimeError(
            "A seed produziu chaves de auditoria duplicadas."
        )

    if len(events) != EXPECTED_DEMO_AUDIT_LOG_COUNT:
        raise RuntimeError(
            "Quantidade inesperada de eventos "
            f"acadêmicos: {len(events)}."
        )

    return events


def seed_academic_demo_audit_logs(
    db: Session,
    *,
    exams: dict[str, Exam],
    ai_analyses: dict[str, AIAnalysis],
    users: dict[str, User],
    statuses: dict[str, Status],
) -> dict[str, AuditLog]:
    """Reconcilia somente os logs reservados da massa acadêmica."""

    events = build_demo_audit_events(
        exams=exams,
        ai_analyses=ai_analyses,
        users=users,
        statuses=statuses,
    )

    existing_logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.user_agent
            == DEMO_AUDIT_USER_AGENT
        )
        .all()
    )

    existing_by_key: dict[str, AuditLog] = {}

    for audit_log in existing_logs:
        payload = audit_log.new_data

        if not isinstance(payload, dict):
            raise RuntimeError(
                "Log acadêmico existente sem "
                "metadados estruturados."
            )

        key = payload.get("demo_event_key")

        if not isinstance(key, str) or not key:
            raise RuntimeError(
                "Log acadêmico existente sem "
                "demo_event_key."
            )

        if key in existing_by_key:
            raise RuntimeError(
                "Colisão de eventos acadêmicos: "
                f"{key}."
            )

        existing_by_key[key] = audit_log

    result: dict[str, AuditLog] = {}

    for event in events:
        audit_log = existing_by_key.get(
            event.key
        )

        if audit_log is None:
            audit_log = create_audit_log(
                db=db,
                user_id=event.user_id,
                clinic_id=event.clinic_id,
                action=event.action,
                entity=event.entity,
                entity_id=event.entity_id,
                description=event.description,
                old_data=event.old_data,
                new_data=event.new_data,
                ip_address=None,
                user_agent=(
                    DEMO_AUDIT_USER_AGENT
                ),
            )
        else:
            audit_log.user_id = event.user_id
            audit_log.clinic_id = event.clinic_id
            audit_log.action = enum_to_value(
                event.action
            )
            audit_log.entity = enum_to_value(
                event.entity
            )
            audit_log.entity_id = event.entity_id
            audit_log.description = (
                sanitize_audit_data(
                    event.description
                )
            )
            audit_log.old_data = (
                sanitize_audit_data(
                    event.old_data
                )
            )
            audit_log.new_data = (
                sanitize_audit_data(
                    event.new_data
                )
            )
            audit_log.ip_address = None
            audit_log.user_agent = (
                DEMO_AUDIT_USER_AGENT
            )

        audit_log.created_at = event.created_at
        result[event.key] = audit_log

    expected_keys = set(result)

    for key, audit_log in existing_by_key.items():
        if key not in expected_keys:
            db.delete(audit_log)

    db.flush()

    if len(result) != EXPECTED_DEMO_AUDIT_LOG_COUNT:
        raise RuntimeError(
            "A massa acadêmica deve produzir "
            f"{EXPECTED_DEMO_AUDIT_LOG_COUNT} "
            "logs de auditoria."
        )

    return result
