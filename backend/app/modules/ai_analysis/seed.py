"""
Seed do módulo de análises de IA.

Cria análises iniciais para testes e desenvolvimento.
"""

from sqlalchemy.orm import Session

from app.modules.ai_analysis.model import AIAnalysis
from app.modules.exams.model import Exam


def get_or_create_ai_analysis(
    db: Session,
    *,
    exam_id: int,
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
    Evita duplicidade porque exam_id é único.
    """

    ai_analysis = (
        db.query(AIAnalysis)
        .filter(AIAnalysis.exam_id == exam_id)
        .first()
    )

    if ai_analysis:
        return ai_analysis

    ai_analysis = AIAnalysis(
        exam_id=exam_id,
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
    db.commit()
    db.refresh(ai_analysis)

    return ai_analysis


def seed_ai_analysis(
    db: Session,
    exams: dict[str, Exam],
) -> dict[str, AIAnalysis]:
    """
    Cria análises de IA iniciais do sistema.
    """

    return {
        "ai_analysis_colonoscopy_completed": get_or_create_ai_analysis(
            db=db,
            exam_id=exams["exam_colonoscopy_completed"].id,
            prediction_label="normal",
            prediction_class=0,
            confidence=0.94,
            model_name="clinicai-endoscopy-cnn",
            model_version="0.1.0",
            gradcam_path="uploads/gradcam/colonoscopy_completed_gradcam.jpg",
            processing_time_ms=1240,
            ai_notes="Análise simulada para ambiente de desenvolvimento.",
            raw_response='{"prediction_label": "normal", "confidence": 0.94}',
        ),
        "ai_analysis_endoscopy_processing": get_or_create_ai_analysis(
            db=db,
            exam_id=exams["exam_endoscopy_in_analysis"].id,
            prediction_label="suspected_gastritis",
            prediction_class=1,
            confidence=0.87,
            model_name="clinicai-endoscopy-cnn",
            model_version="0.1.0",
            gradcam_path="uploads/gradcam/endoscopy_ai_processing_gradcam.jpg",
            processing_time_ms=1580,
            ai_notes="Resultado preliminar gerado por modelo simulado.",
            raw_response='{"prediction_label": "suspected_gastritis", "confidence": 0.87}',
        ),
    }