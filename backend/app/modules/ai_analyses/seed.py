"""Análises reais da massa acadêmica demonstrativa."""

import json

from sqlalchemy.orm import Session

from app.common.constants import (
    StatusName,
    StatusScope,
)
from app.modules.academic_demo_assets import (
    install_gradcam_asset,
    get_demo_exam_definitions,
)
from app.modules.ai_analyses.file_storage import (
    serialize_gradcam_path,
)
from app.modules.ai_analyses.model import AIAnalysis
from app.modules.exams.model import Exam
from app.modules.statuses.model import Status


ATTRIBUTION_FIELDS = (
    "attribution_method",
    "attribution_target_layers",
    "attribution_local_evidence",
    "attribution_branch_weights",
    "attribution_branch_cam_raw_maxima",
    "attribution_unavailable_reason",
)


def get_ai_analysis_status(
    db: Session,
    name: StatusName,
) -> Status | None:
    """Busca status de análise pelo nome oficial."""

    return (
        db.query(Status)
        .filter(
            Status.name == name.value,
            Status.applies_to
            == StatusScope.AI_ANALYSIS.value,
        )
        .first()
    )


def get_or_create_ai_analysis(
    db: Session,
    *,
    exam: Exam,
    status_id: int,
    definition: dict,
) -> AIAnalysis:
    """Reconcilia a análise acadêmica vinculada ao exame."""

    existing = (
        db.query(AIAnalysis)
        .filter(
            AIAnalysis.exam_id == exam.id
        )
        .first()
    )

    analysis = definition["analysis"]
    source = definition["source_asset"]
    gradcam_path = install_gradcam_asset(
        exam,
        analysis["gradcam_asset"],
    )

    attribution_payload = {
        field: analysis.get(field)
        for field in ATTRIBUTION_FIELDS
    }

    ai_analysis = existing or AIAnalysis(exam_id=exam.id)
    if existing is None:
        db.add(ai_analysis)

    ai_analysis.status_id = status_id
    ai_analysis.prediction_label = str(analysis["prediction_label"])
    ai_analysis.prediction_class = int(analysis["prediction_class"])
    ai_analysis.confidence = float(analysis["confidence"])
    ai_analysis.model_name = str(analysis["model_name"])
    ai_analysis.model_version = str(analysis["model_version"])
    ai_analysis.gradcam_path = (
        serialize_gradcam_path(
            gradcam_path
        )
    )
    ai_analysis.processing_time_ms = int(analysis["processing_time_ms"])
    ai_analysis.ai_notes = (
        "Predição real do Ensemble Stacking sobre ativo acadêmico de "
        f"referência {source['label']}; sem finalidade clínica."
    )
    ai_analysis.raw_response = json.dumps(
        attribution_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    db.flush()
    db.refresh(ai_analysis)

    return ai_analysis


def seed_ai_analysis(
    db: Session,
    exams: dict[str, Exam],
    statuses: dict[str, Status] | None = None,
) -> dict[str, AIAnalysis]:
    """Cria as 72 análises registradas no manifesto."""

    completed_status = (
        statuses.get(
            "ai_analysis_completed"
        )
        if statuses
        else None
    )

    completed_status = (
        completed_status
        or get_ai_analysis_status(
            db,
            StatusName.COMPLETED,
        )
    )

    if completed_status is None:
        return {}

    result: dict[str, AIAnalysis] = {}

    for definition in get_demo_exam_definitions():
        exam_key = definition["exam_key"]
        exam = exams.get(exam_key)

        if exam is None:
            raise RuntimeError(
                "Exame acadêmico ausente para análise: "
                f"{exam_key}."
            )

        if definition.get("analysis") is None:
            stale_analysis = (
                db.query(AIAnalysis)
                .filter(
                    AIAnalysis.exam_id == exam.id
                )
                .one_or_none()
            )

            if stale_analysis is not None:
                db.delete(stale_analysis)
                db.flush()
                db.expire(
                    exam,
                    ["ai_analysis"],
                )

            continue

        result[exam_key] = (
            get_or_create_ai_analysis(
                db,
                exam=exam,
                status_id=completed_status.id,
                definition=definition,
            )
        )

    if len(result) != 72:
        raise RuntimeError(
            "O seed acadêmico deve produzir "
            "72 análises."
        )

    return result
