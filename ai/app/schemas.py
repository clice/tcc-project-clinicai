"""Schemas públicos do serviço de inferência do ClinicAI."""

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    exam_type: str = Field(
        ...,
        description=(
            "Tipo de exame enviado pelo backend."
        ),
    )

    exam_domain: str = Field(
        ...,
        description=(
            "Domínio clínico selecionado."
        ),
    )

    prediction_class: int = Field(
        ...,
        ge=0,
        description=(
            "Índice da classe prevista."
        ),
    )

    label: str = Field(
        ...,
        description=(
            "Rótulo da classe prevista."
        ),
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    model_name: str
    model_version: str

    gradcam_available: bool = False
    gradcam_base64: str | None = None
    gradcam_mime_type: str | None = None
    gradcam_sha256: str | None = None

    attribution_method: str | None = None

    attribution_target_layers: (
        dict[str, str] | None
    ) = None

    attribution_local_evidence: (
        dict[str, float] | None
    ) = None

    attribution_branch_weights: (
        dict[str, float] | None
    ) = None

    attribution_branch_cam_raw_maxima: (
        dict[str, float] | None
    ) = None

    attribution_unavailable_reason: (
        str | None
    ) = None

    device: str
