"""Massa acadêmica fictícia do módulo de análises de IA."""

from sqlalchemy.orm import Session

from app.common.constants import StatusName, StatusScope
from app.modules.ai_analysis.model import AIAnalysis
from app.modules.exams.model import Exam
from app.modules.statuses.model import Status


def get_ai_analysis_status(
    db: Session,
    name: StatusName,
) -> Status | None:
    """
    Busca uma análise pelo status.
    """
    return (
        db.query(Status)
        .filter(
            Status.name == name.value,
            Status.applies_to == StatusScope.AI_ANALYSIS.value,
        )
        .first()
    )


def get_or_create_ai_analysis(
    db: Session,
    *,
    exam_id: int,
    status_id: int,
    prediction_label: str,
    prediction_class: int | None,
    confidence: float,
    model_name: str,
    model_version: str,
    gradcam_path: str | None = None,
    processing_time_ms: int | None = None,
    ai_notes: str | None = None,
    raw_response: str | None = None,
) -> AIAnalysis:
    """
    Busca uma análise pelo exame ou cria uma nova.
    """
    ai_analysis = db.query(AIAnalysis).filter(AIAnalysis.exam_id == exam_id).first()

    if ai_analysis:
        return ai_analysis

    ai_analysis = AIAnalysis(
        exam_id=exam_id,
        status_id=status_id,
        prediction_label=prediction_label,
        prediction_class=prediction_class,
        confidence=confidence,
        model_name=model_name,
        model_version=model_version,
        gradcam_path=gradcam_path,
        processing_time_ms=processing_time_ms,
        ai_notes=ai_notes,
        raw_response=raw_response,
    )

    db.add(ai_analysis)
    db.flush()
    db.refresh(ai_analysis)

    return ai_analysis


def seed_ai_analysis(
    db: Session,
    exams: dict[str, Exam],
    statuses: dict[str, Status] | None = None,
) -> dict[str, AIAnalysis]:
    """
    Cria análises simuladas, sem alegação de validade clínica.
    """
    completed_exam = exams.get("exam_colonoscopy_completed")
    processing_exam = exams.get("exam_endoscopy_processing")

    completed_status = None
    processing_status = None

    if statuses:
        completed_status = statuses.get("ai_analysis_completed")
        processing_status = statuses.get("ai_analysis_processing")

    completed_status = completed_status or get_ai_analysis_status(
        db, StatusName.COMPLETED
    )
    processing_status = processing_status or get_ai_analysis_status(
        db, StatusName.PROCESSING
    )

    if (
        not completed_exam
        or not processing_exam
        or not completed_status
        or not processing_status
    ):
        return {}

    return {
        "ai_analysis_colonoscopy_completed": get_or_create_ai_analysis(
            db=db,
            exam_id=completed_exam.id,
            status_id=completed_status.id,
            prediction_label="normal",
            prediction_class=0,
            confidence=0.94,
            model_name="clinicai-gastrointestinal-stacking-demo",
            model_version="demo-0.1.0",
            gradcam_path="uploads/gradcam/colonoscopy_completed_gradcam.jpg",
            processing_time_ms=1240,
            ai_notes="Análise simulada para ambiente de desenvolvimento.",
            raw_response='{"prediction_label": "normal", "confidence": 0.94}',
        ),
        "ai_analysis_endoscopy_processing": get_or_create_ai_analysis(
            db=db,
            exam_id=processing_exam.id,
            status_id=processing_status.id,
            prediction_label="anormal",
            prediction_class=1,
            confidence=0.87,
            model_name="clinicai-gastrointestinal-stacking-demo",
            model_version="demo-0.1.0",
            gradcam_path="uploads/gradcam/endoscopy_ai_processing_gradcam.jpg",
            processing_time_ms=1580,
            ai_notes="Resultado acadêmico preliminar e inteiramente simulado.",
            raw_response='{"prediction_label": "anormal", "status": "processing", "confidence": 0.87}',
        ),
    }
