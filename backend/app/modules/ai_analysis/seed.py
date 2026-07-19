"""Análises reais da massa acadêmica demonstrativa."""

import json

from sqlalchemy.orm import Session

from app.common.constants import (
    StatusName,
    StatusScope,
)
from app.modules.academic_demo_assets import (
    bundled_gradcam_path,
    get_demo_exam_definitions,
)
from app.modules.ai_analysis.model import AIAnalysis
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
    """Cria uma análise sem alterar registro existente."""

    existing = (
        db.query(AIAnalysis)
        .filter(
            AIAnalysis.exam_id == exam.id
        )
        .first()
    )

    if existing:
        return existing

    analysis = definition["analysis"]
    source = definition["source_asset"]
    gradcam_path = bundled_gradcam_path(
        analysis["gradcam_asset"]
    )

    attribution_payload = {
        field: analysis.get(field)
        for field in ATTRIBUTION_FIELDS
    }

    ai_analysis = AIAnalysis(
        exam_id=exam.id,
        status_id=status_id,
        prediction_label=str(
            analysis["prediction_label"]
        ),
        prediction_class=int(
            analysis["prediction_class"]
        ),
        confidence=float(
            analysis["confidence"]
        ),
        model_name=str(
            analysis["model_name"]
        ),
        model_version=str(
            analysis["model_version"]
        ),
        gradcam_path=str(gradcam_path),
        processing_time_ms=int(
            analysis["processing_time_ms"]
        ),
        ai_notes=(
            "Predição real do Ensemble Stacking "
            "sobre ativo acadêmico de referência "
            f"{source['label']}; sem finalidade clínica."
        ),
        raw_response=json.dumps(
            attribution_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ),
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
        if definition.get("analysis") is None:
            continue

        exam_key = definition["exam_key"]
        exam = exams.get(exam_key)

        if exam is None:
            raise RuntimeError(
                "Exame acadêmico ausente para análise: "
                f"{exam_key}."
            )

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
