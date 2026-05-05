"""
Service do módulo de análises de IA.

Concentra as regras de negócio relacionadas aos resultados gerados por IA.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.common.constants import AuditAction, AuditEntity, RoleName, StatusName, StatusScope
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
    role_name = current_user.role.name if current_user.role else None

    if role_name == RoleName.ADMIN_MASTER.value:
        return

    if role_name == RoleName.CLINIC_STAFF.value and exam.clinic_id == current_user.clinic_id:
        return

    if role_name == RoleName.DOCTOR.value and exam.doctor_id == current_user.id:
        return

    raise HTTPException(
        status_code=403,
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

    role_name = current_user.role.name if current_user.role else None

    if role_name == RoleName.ADMIN_MASTER.value:
        pass

    elif role_name == RoleName.CLINIC_STAFF.value:
        if current_user.clinic_id is None:
            raise HTTPException(
                status_code=403,
                detail="Usuário não está vinculado a uma clínica.",
            )

        query = query.filter(Exam.clinic_id == current_user.clinic_id)

    elif role_name == RoleName.DOCTOR.value:
        query = query.filter(Exam.doctor_id == current_user.id)

    else:
        raise HTTPException(
            status_code=403,
            detail="Usuário sem permissão para listar análises de IA.",
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

    completed_exam_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.COMPLETED.value,
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

    exam.status_id = completed_exam_status.id

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.RUN_AI_ANALYSIS,
        entity=AuditEntity.AI_ANALYSIS,
        entity_id=ai_analysis.id,
        description="Análise de IA criada para exame.",
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
                "status_id": completed_exam_status.id,
                "status_name": StatusName.COMPLETED.value,
            },
        },
    )

    db.commit()
    db.refresh(ai_analysis)

    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis.id,
    )

    return build_ai_analysis_response(ai_analysis)


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

    update_data = payload.model_dump(exclude_unset=True)

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

    for field, value in update_data.items():
        setattr(ai_analysis, field, value)

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
