"""
Service do módulo de análises de IA.

Concentra as regras de negócio relacionadas aos resultados gerados por IA.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.modules.ai_analysis.model import AIAnalysis
from app.modules.ai_analysis.schema import AIAnalysisCreate, AIAnalysisUpdate
from app.modules.exams.model import Exam


def build_ai_analysis_response(ai_analysis: AIAnalysis) -> dict:
    """
    Monta a resposta da análise de IA.
    """

    return {
        "id": ai_analysis.id,
        "exam_id": ai_analysis.exam_id,
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


def validate_exam_exists(db: Session, exam_id: int) -> Exam:
    """
    Valida se o exame existe.
    """

    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    return exam


def get_ai_analysis_model_by_id(
    db: Session,
    ai_analysis_id: int,
) -> AIAnalysis:
    """
    Busca o model de análise de IA pelo ID.
    """

    ai_analysis = (
        db.query(AIAnalysis)
        .options(joinedload(AIAnalysis.exam))
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
) -> dict:
    """
    Busca uma análise de IA pelo ID.
    """

    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis_id,
    )

    return build_ai_analysis_response(ai_analysis)


def get_ai_analysis_by_exam_id(
    db: Session,
    exam_id: int,
) -> dict:
    """
    Busca uma análise de IA pelo ID do exame.
    """

    validate_exam_exists(db=db, exam_id=exam_id)

    ai_analysis = (
        db.query(AIAnalysis)
        .options(joinedload(AIAnalysis.exam))
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
    exam_id: int | None = None,
    model_name: str | None = None,
    model_version: str | None = None,
    prediction_label: str | None = None,
) -> list[dict]:
    """
    Lista análises de IA com filtros opcionais.
    """

    query = db.query(AIAnalysis).options(joinedload(AIAnalysis.exam))

    if exam_id:
        query = query.filter(AIAnalysis.exam_id == exam_id)

    if model_name:
        query = query.filter(AIAnalysis.model_name.ilike(f"%{model_name.strip()}%"))

    if model_version:
        query = query.filter(AIAnalysis.model_version == model_version)

    if prediction_label:
        query = query.filter(
            AIAnalysis.prediction_label.ilike(f"%{prediction_label.strip()}%")
        )

    ai_analysis = query.order_by(AIAnalysis.created_at.desc()).all()

    return [
        build_ai_analysis_response(ai_analysis)
        for ai_analysis in ai_analysis
    ]


def create_ai_analysis(
    db: Session,
    payload: AIAnalysisCreate,
) -> dict:
    """
    Cria uma análise de IA para um exame.
    Cada exame pode ter apenas uma análise.
    """

    validate_exam_exists(db=db, exam_id=payload.exam_id)

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

    ai_analysis = AIAnalysis(**payload.model_dump())

    db.add(ai_analysis)
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
) -> dict:
    """
    Atualiza parcialmente uma análise de IA.
    """

    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis_id,
    )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return build_ai_analysis_response(ai_analysis)

    for field, value in update_data.items():
        setattr(ai_analysis, field, value)

    db.commit()
    db.refresh(ai_analysis)

    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis.id,
    )

    return build_ai_analysis_response(ai_analysis)


def review_ai_analysis(
    db: Session,
    ai_analysis_id: int,
    payload: AIAnalysisUpdate,
) -> dict:
    """
    Registra ou atualiza a revisão médica de uma análise de IA.

    Por enquanto, usa os campos já existentes:
    - ai_notes
    - raw_response
    - gradcam_path, se necessário

    No futuro, pode ser separado em campos próprios:
    - reviewed_by_id
    - reviewed_at
    - medical_review
    - review_status
    """
    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis_id,
    )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return build_ai_analysis_response(ai_analysis)

    allowed_review_fields = {
        "ai_notes",
        "raw_response",
        "gradcam_path",
    }

    for field, value in update_data.items():
        if field in allowed_review_fields:
            setattr(ai_analysis, field, value)

    db.commit()
    db.refresh(ai_analysis)

    ai_analysis = get_ai_analysis_model_by_id(
        db=db,
        ai_analysis_id=ai_analysis.id,
    )

    return build_ai_analysis_response(ai_analysis)