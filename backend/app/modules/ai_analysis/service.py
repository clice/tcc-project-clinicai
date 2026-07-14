"""
Service do módulo de análises de IA.

Concentra as regras de negócio relacionadas aos resultados gerados por IA.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.common.access_control import (
    ensure_user_can_access_exam,
    filter_query_by_user_scope,
)
from app.common.constants import AuditAction, AuditEntity, StatusName, StatusScope
from app.common.services import apply_update_data, model_dump_update
from app.modules.ai_analysis.model import AIAnalysis
from app.modules.ai_analysis.schema import AIAnalysisCreate, AIAnalysisUpdate
from app.modules.audit_logs.service import create_audit_log
from app.modules.exams.model import Exam
from app.modules.statuses.service import get_status_by_name_and_applies_to
from app.modules.users.model import User


def build_ai_analysis_response(ai_analysis: AIAnalysis) -> dict:
    """
    Monta a resposta da análise de IA.
    """
    return {
        "id": ai_analysis.id,
        "exam_id": ai_analysis.exam_id,
        "status_id": ai_analysis.status_id,
        "status_name": ai_analysis.status.name if ai_analysis.status else None,
        "status_display_name": ai_analysis.status.display_name if ai_analysis.status else None,
        "prediction_label": ai_analysis.prediction_label,
        "prediction_class": ai_analysis.prediction_class,
        "confidence": ai_analysis.confidence,
        "model_name": ai_analysis.model_name,
        "model_version": ai_analysis.model_version,
        "gradcam_path": ai_analysis.gradcam_path,
        "processing_time_ms": ai_analysis.processing_time_ms,
        "ai_notes": ai_analysis.ai_notes,
        "raw_response": ai_analysis.raw_response,
        "created_at": ai_analysis.created_at,
        "updated_at": ai_analysis.updated_at,
    }


def validate_user_can_access_exam(
    *,
    current_user: User,
    exam: Exam,
) -> None:
    """
    Garante que o usuário autenticado pode acessar o exame/análise.
    """
    ensure_user_can_access_exam(
        current_user=current_user,
        exam=exam,
        detail="Você não tem permissão para acessar esta análise de IA.",
    )


def validate_exam_exists(
    db: Session,
    exam_id: int,
    current_user: User,
) -> Exam:
    """
    Valida se o exame existe e se o usuário pode acessá-lo.
    """
    exam = (
        db.query(Exam)
        .options(
            joinedload(Exam.clinic),
            joinedload(Exam.patient),
            joinedload(Exam.doctor),
            joinedload(Exam.status),
        )
        .filter(Exam.id == exam_id)
        .first()
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )

    return exam


def validate_exam_can_receive_ai_analysis(exam: Exam) -> None:
    """
    Valida se o exame está apto para receber resultado de IA.
    """
    if exam.status and exam.status.name == StatusName.CANCELED.value:
        raise HTTPException(
            status_code=400,
            detail="Não é possível criar análise de IA para exame cancelado.",
        )

    if not exam.file_path:
        raise HTTPException(
            status_code=400,
            detail="O exame precisa ter um arquivo enviado antes da análise de IA.",
        )


def get_ai_analysis_model_by_id(
    db: Session,
    ai_analysis_id: int,
) -> AIAnalysis:
    """
    Busca o model de análise de IA pelo ID.
    """
    ai_analysis = (
        db.query(AIAnalysis)
        .options(
            joinedload(AIAnalysis.status),
            joinedload(AIAnalysis.exam).joinedload(Exam.clinic),
            joinedload(AIAnalysis.exam).joinedload(Exam.patient),
            joinedload(AIAnalysis.exam).joinedload(Exam.doctor),
            joinedload(AIAnalysis.exam).joinedload(Exam.status),
        )
        .filter(AIAnalysis.id == ai_analysis_id)
        .first()
    )

    if not ai_analysis:
        raise HTTPException(
            status_code=404,
            detail="Análise de IA não encontrada.",
        )

    return ai_analysis


# ========================================
# MAIN METHODS
# ========================================


def get_ai_analysis_by_id(
    db: Session,
    ai_analysis_id: int,
    current_user: User,
) -> dict:
    """
    Busca uma análise de IA pelo ID.
    """
    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis_id,
    )

    validate_user_can_access_exam(
        current_user=current_user,
        exam=ai_analysis.exam,
    )

    return build_ai_analysis_response(ai_analysis)


def get_ai_analysis_by_exam_id(
    db: Session,
    exam_id: int,
    current_user: User,
) -> dict:
    """
    Busca uma análise de IA pelo ID do exame.
    """
    validate_exam_exists(
        db=db,
        exam_id=exam_id,
        current_user=current_user,
    )

    ai_analysis = (
        db.query(AIAnalysis)
        .options(
            joinedload(AIAnalysis.status),
            joinedload(AIAnalysis.exam).joinedload(Exam.clinic),
            joinedload(AIAnalysis.exam).joinedload(Exam.patient),
            joinedload(AIAnalysis.exam).joinedload(Exam.doctor),
            joinedload(AIAnalysis.exam).joinedload(Exam.status),
        )
        .filter(AIAnalysis.exam_id == exam_id)
        .first()
    )

    if not ai_analysis:
        raise HTTPException(
            status_code=404,
            detail="Este exame ainda não possui análise de IA.",
        )

    return build_ai_analysis_response(ai_analysis)


def list_ai_analysis(
    db: Session,
    current_user: User,
    exam_id: int | None = None,
    model_name: str | None = None,
    model_version: str | None = None,
    prediction_label: str | None = None,
    status_id: int | None = None,
) -> list[dict]:
    """
    Lista análises de IA com filtros opcionais e escopo por usuário.
    """
    query = (
        db.query(AIAnalysis)
        .join(Exam, AIAnalysis.exam_id == Exam.id)
        .options(
            joinedload(AIAnalysis.status),
            joinedload(AIAnalysis.exam).joinedload(Exam.clinic),
            joinedload(AIAnalysis.exam).joinedload(Exam.patient),
            joinedload(AIAnalysis.exam).joinedload(Exam.doctor),
            joinedload(AIAnalysis.exam).joinedload(Exam.status),
        )
    )

    query = filter_query_by_user_scope(
        query=query,
        model=Exam,
        current_user=current_user,
    )

    if exam_id:
        query = query.filter(AIAnalysis.exam_id == exam_id)

    if status_id:
        query = query.filter(AIAnalysis.status_id == status_id)

    if model_name:
        query = query.filter(AIAnalysis.model_name.ilike(f"%{model_name.strip()}%"))

    if model_version:
        query = query.filter(AIAnalysis.model_version == model_version)

    if prediction_label:
        query = query.filter(
            AIAnalysis.prediction_label.ilike(f"%{prediction_label.strip()}%")
        )

    analyses = query.order_by(AIAnalysis.created_at.desc()).all()

    return [build_ai_analysis_response(analysis) for analysis in analyses]


def create_ai_analysis(
    db: Session,
    payload: AIAnalysisCreate,
    current_user: User,
) -> dict:
    """
    Cria uma análise de IA para um exame.
    Cada exame pode ter apenas uma análise.
    """
    exam = validate_exam_exists(
        db=db,
        exam_id=payload.exam_id,
        current_user=current_user,
    )

    validate_exam_can_receive_ai_analysis(exam)

    existing_analysis = (
        db.query(AIAnalysis)
        .filter(AIAnalysis.exam_id == payload.exam_id)
        .first()
    )

    if existing_analysis:
        raise HTTPException(
            status_code=400,
            detail="Este exame já possui uma análise de IA.",
        )

    completed_ai_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.COMPLETED.value,
        applies_to=StatusScope.AI_ANALYSIS.value,
    )

    awaiting_review_exam_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.AWAITING_REVIEW.value,
        applies_to=StatusScope.EXAM.value,
    )

    ai_analysis = AIAnalysis(
        **payload.model_dump(),
        status_id=completed_ai_status.id,
    )

    db.add(ai_analysis)
    db.flush()

    old_exam_status = {
        "status_id": exam.status_id,
        "status_name": exam.status.name if exam.status else None,
    }

    exam.status_id = awaiting_review_exam_status.id

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.RUN_AI_ANALYSIS,
        entity=AuditEntity.AI_ANALYSIS,
        entity_id=ai_analysis.id,
        description="Análise de IA criada para exame. Exame movido para aguardando revisão médica.",
        new_data={
            "id": ai_analysis.id,
            "exam_id": ai_analysis.exam_id,
            "status_id": ai_analysis.status_id,
            "prediction_label": ai_analysis.prediction_label,
            "prediction_class": ai_analysis.prediction_class,
            "confidence": ai_analysis.confidence,
            "model_name": ai_analysis.model_name,
            "model_version": ai_analysis.model_version,
            "gradcam_path": ai_analysis.gradcam_path,
            "processing_time_ms": ai_analysis.processing_time_ms,
            "old_exam_status": old_exam_status,
            "new_exam_status": {
                "status_id": awaiting_review_exam_status.id,
                "status_name": StatusName.AWAITING_REVIEW.value,
            },
        },
    )

    # RF36 consulta eventos pelo próprio exame. O registro da análise continua
    # existindo como entidade AI_ANALYSIS, enquanto este segundo evento torna a
    # mudança de estado do exame visível em seu histórico autorizado.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.RUN_AI_ANALYSIS,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Análise de IA concluída. Exame movido para aguardando revisão médica.",
        old_data=old_exam_status,
        new_data={
            "status_id": awaiting_review_exam_status.id,
            "status_name": StatusName.AWAITING_REVIEW.value,
            "ai_analysis_id": ai_analysis.id,
        },
    )

    db.commit()
    db.refresh(ai_analysis)

    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis.id,
    )

    return build_ai_analysis_response(ai_analysis)


def get_ai_metrics(db: Session) -> dict:
    """
    Métricas agregadas do módulo de IA, exclusivas do Administrador
    Master (a rota que chama esta função é protegida por `require_admin`,
    não por uma permissão compartilhada com o Médico).

    Reúne informações de governança/infraestrutura do modelo — distintas
    dos indicadores operacionais (RF54-56) já disponíveis a todos os
    perfis no Dashboard do frontend.
    """
    from collections import Counter
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func as sa_func

    from app.modules.audit_logs.model import AuditLog

    total_analyses = db.query(AIAnalysis).count()

    # --- Uso por modelo/versão ---
    model_usage_rows = (
        db.query(
            AIAnalysis.model_name,
            AIAnalysis.model_version,
            sa_func.count(AIAnalysis.id).label("count"),
        )
        .group_by(AIAnalysis.model_name, AIAnalysis.model_version)
        .all()
    )
    by_model = [
        {
            "model_name": row.model_name,
            "model_version": row.model_version,
            "domain": None,  # todos os modelos hoje são do domínio gastrointestinal
            "count": row.count,
        }
        for row in model_usage_rows
    ]

    # --- Confiança: estatísticas + distribuição em faixas de 10% ---
    confidences = [value for (value,) in db.query(AIAnalysis.confidence).all()]

    confidence_mean = sum(confidences) / len(confidences) if confidences else None
    confidence_min = min(confidences) if confidences else None
    confidence_max = max(confidences) if confidences else None

    confidence_distribution: dict[str, int] = {
        f"{i * 10}-{i * 10 + 10}%": 0 for i in range(10)
    }
    for value in confidences:
        bucket_index = min(int(value * 10), 9)  # 1.0 exato cai no último bucket
        bucket_key = f"{bucket_index * 10}-{bucket_index * 10 + 10}%"
        confidence_distribution[bucket_key] += 1

    # --- Tempo de processamento ---
    processing_times = [
        value
        for (value,) in db.query(AIAnalysis.processing_time_ms).all()
        if value is not None
    ]
    processing_time_mean_ms = (
        sum(processing_times) / len(processing_times) if processing_times else None
    )
    processing_time_min_ms = min(processing_times) if processing_times else None
    processing_time_max_ms = max(processing_times) if processing_times else None

    # --- Taxa de divergência (exames concluídos, com ou sem divergência) ---
    completed_status = get_status_by_name_and_applies_to(
        db=db, name=StatusName.COMPLETED.value, applies_to=StatusScope.EXAM.value,
    )
    completed_with_divergence_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.COMPLETED_WITH_DIVERGENCE.value,
        applies_to=StatusScope.EXAM.value,
    )
    completed_count = (
        db.query(Exam).filter(Exam.status_id == completed_status.id).count()
    )
    divergence_count = (
        db.query(Exam).filter(Exam.status_id == completed_with_divergence_status.id).count()
    )
    total_concluded = completed_count + divergence_count
    divergence_rate = (divergence_count / total_concluded) if total_concluded > 0 else 0.0

    # --- Falhas: contagem + últimas ocorrências (via log de auditoria) ---
    failed_status = get_status_by_name_and_applies_to(
        db=db, name=StatusName.FAILED.value, applies_to=StatusScope.EXAM.value,
    )
    failure_count = db.query(Exam).filter(Exam.status_id == failed_status.id).count()

    recent_failure_logs = (
        db.query(AuditLog)
        .filter(AuditLog.action == AuditAction.AI_ANALYSIS_FAILED.value)
        .order_by(AuditLog.created_at.desc())
        .limit(5)
        .all()
    )
    recent_failures = [
        {
            "exam_id": log.entity_id,
            "description": log.description,
            "created_at": log.created_at,
        }
        for log in recent_failure_logs
    ]

    # --- Volume diário nos últimos 30 dias ---
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_dates = [
        value
        for (value,) in db.query(AIAnalysis.created_at)
        .filter(AIAnalysis.created_at >= thirty_days_ago)
        .all()
    ]
    day_counts = Counter(date.strftime("%Y-%m-%d") for date in recent_dates)
    analyses_last_30_days = [
        {"date": day, "count": count} for day, count in sorted(day_counts.items())
    ]

    return {
        "total_analyses": total_analyses,
        "by_model": by_model,
        "confidence_mean": confidence_mean,
        "confidence_min": confidence_min,
        "confidence_max": confidence_max,
        "confidence_distribution": confidence_distribution,
        "processing_time_mean_ms": processing_time_mean_ms,
        "processing_time_min_ms": processing_time_min_ms,
        "processing_time_max_ms": processing_time_max_ms,
        "divergence_rate": round(divergence_rate, 4),
        "failure_count": failure_count,
        "recent_failures": recent_failures,
        "analyses_last_30_days": analyses_last_30_days,
    }


def update_ai_analysis(
    db: Session,
    ai_analysis_id: int,
    payload: AIAnalysisUpdate,
    current_user: User,
) -> dict:
    """
    Atualiza parcialmente uma análise de IA.
    """
    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis_id,
    )

    validate_user_can_access_exam(
        current_user=current_user,
        exam=ai_analysis.exam,
    )

    update_data = model_dump_update(payload)

    if not update_data:
        return build_ai_analysis_response(ai_analysis)

    old_data = {
        "prediction_label": ai_analysis.prediction_label,
        "prediction_class": ai_analysis.prediction_class,
        "confidence": ai_analysis.confidence,
        "model_name": ai_analysis.model_name,
        "model_version": ai_analysis.model_version,
        "gradcam_path": ai_analysis.gradcam_path,
        "processing_time_ms": ai_analysis.processing_time_ms,
        "ai_notes": ai_analysis.ai_notes,
        "raw_response": ai_analysis.raw_response,
    }

    apply_update_data(ai_analysis, update_data)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=ai_analysis.exam.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.AI_ANALYSIS,
        entity_id=ai_analysis.id,
        description="Análise de IA atualizada.",
        old_data=old_data,
        new_data=update_data,
    )

    db.commit()
    db.refresh(ai_analysis)

    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis.id,
    )

    return build_ai_analysis_response(ai_analysis)
