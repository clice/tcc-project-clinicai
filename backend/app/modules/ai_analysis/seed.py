"""Massa acadêmica coerente do módulo de análises de IA."""

from sqlalchemy.orm import Session

from app.common.constants import StatusName, StatusScope
from app.modules.academic_demo_assets import (
    bundled_gradcam_path,
    get_demo_asset_entry,
    get_demo_manifest,
)
from app.modules.ai_analysis.model import AIAnalysis
from app.modules.exams.model import Exam
from app.modules.statuses.model import Status


def get_ai_analysis_status(
    db: Session,
    name: StatusName,
) -> Status | None:
    """Busca uma análise pelo status."""

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
    image_asset_key: str,
    gradcam_asset_key: str,
) -> AIAnalysis:
    """Cria uma análise do demo sem alterar registros já existentes."""

    ai_analysis = db.query(AIAnalysis).filter(AIAnalysis.exam_id == exam_id).first()

    if ai_analysis:
        return ai_analysis

    image_entry = get_demo_asset_entry(image_asset_key)
    prediction = image_entry["prediction"]
    model = get_demo_manifest()["model"]
    gradcam_path = bundled_gradcam_path(gradcam_asset_key)

    ai_analysis = AIAnalysis(
        exam_id=exam_id,
        status_id=status_id,
        prediction_label=str(prediction["label"]),
        prediction_class=int(prediction["class"]),
        confidence=float(prediction["confidence"]),
        model_name=str(model["name"]),
        model_version=str(model["version"]),
        gradcam_path=str(gradcam_path),
        processing_time_ms=None,
        ai_notes=(
            "Predição do Ensemble Stacking sobre imagem acadêmica do "
            f"Kvasir ({image_entry['source_class']}); sem finalidade clínica."
        ),
        raw_response=None,
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
    """Cria quatro análises concluídas e coerentes com os exames."""

    completed_status = None
    if statuses:
        completed_status = statuses.get("ai_analysis_completed")

    completed_status = completed_status or get_ai_analysis_status(
        db,
        StatusName.COMPLETED,
    )

    definitions = {
        "ai_awaiting_review_normal": {
            "exam": exams.get("exam_awaiting_review_normal"),
            "image_asset_key": "normal_image",
            "gradcam_asset_key": "normal_gradcam",
        },
        "ai_awaiting_review_abnormal": {
            "exam": exams.get("exam_awaiting_review_abnormal"),
            "image_asset_key": "abnormal_image",
            "gradcam_asset_key": "abnormal_gradcam",
        },
        "ai_completed_confirmed": {
            "exam": exams.get("exam_completed_confirmed"),
            "image_asset_key": "normal_image",
            "gradcam_asset_key": "normal_gradcam",
        },
        "ai_completed_with_divergence": {
            "exam": exams.get("exam_completed_with_divergence"),
            "image_asset_key": "abnormal_image",
            "gradcam_asset_key": "abnormal_gradcam",
        },
    }

    if not completed_status or not all(
        definition["exam"] for definition in definitions.values()
    ):
        return {}

    return {
        key: get_or_create_ai_analysis(
            db=db,
            exam_id=definition["exam"].id,
            status_id=completed_status.id,
            image_asset_key=definition["image_asset_key"],
            gradcam_asset_key=definition["gradcam_asset_key"],
        )
        for key, definition in definitions.items()
    }
