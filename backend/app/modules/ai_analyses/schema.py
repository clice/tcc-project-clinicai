"""
Schemas do módulo de análises de IA.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.schemas import StrictRequestModel
from app.common.validators import normalize_optional_text, normalize_required_text


class AIAnalysisBase(StrictRequestModel):
    """
    Campos compartilhados entre criação e resposta.
    """

    exam_id: int

    prediction_label: str = Field(..., min_length=2, max_length=80)
    prediction_class: int | None = None
    confidence: float = Field(..., ge=0, le=1)

    model_name: str = Field(..., min_length=2, max_length=120)
    model_version: str = Field(..., min_length=1, max_length=50)

    gradcam_path: str | None = Field(default=None, max_length=255)
    processing_time_ms: int | None = Field(default=None, ge=0)

    ai_notes: str | None = None
    raw_response: str | None = None

    @field_validator("prediction_label", "model_name", "model_version")
    @classmethod
    def normalize_required_fields(cls, value: str) -> str:
        return normalize_required_text(value, "Campo obrigatório.")

    @field_validator("gradcam_path", "ai_notes", "raw_response")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


class AIAnalysisCreate(AIAnalysisBase):
    """
    Schema usado para criação de análise de IA.
    """

    pass


class AIAnalysisUpdate(StrictRequestModel):
    """
    Schema usado para atualização parcial de análise de IA.
    """

    prediction_label: str | None = Field(default=None, min_length=2, max_length=80)
    prediction_class: int | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)

    model_name: str | None = Field(default=None, min_length=2, max_length=120)
    model_version: str | None = Field(default=None, min_length=1, max_length=50)

    gradcam_path: str | None = Field(default=None, max_length=255)
    processing_time_ms: int | None = Field(default=None, ge=0)

    ai_notes: str | None = None
    raw_response: str | None = None

    @field_validator("prediction_label", "model_name", "model_version")
    @classmethod
    def normalize_required_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return normalize_required_text(value, "Campo obrigatório.")

    @field_validator("gradcam_path", "ai_notes", "raw_response")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


class AIAnalysisResponse(BaseModel):
    """
    Schema usado nas respostas da API.
    """

    id: int
    exam_id: int

    status_id: int
    status_name: str | None = None
    status_display_name: str | None = None

    prediction_label: str
    prediction_class: int | None = None
    confidence: float

    model_name: str
    model_version: str

    gradcam_available: bool = False

    attribution_method: str | None = None
    attribution_target_layers: dict[str, str] | None = None
    attribution_local_evidence: dict[str, float] | None = None
    attribution_branch_weights: dict[str, float] | None = None
    attribution_branch_cam_raw_maxima: dict[str, float] | None = None
    attribution_unavailable_reason: str | None = None

    processing_time_ms: int | None = None

    ai_notes: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class AIModelUsage(BaseModel):
    """
    Quantidade de análises realizadas por um modelo/versão específico.
    """

    model_name: str
    model_version: str
    domain: str | None = None
    count: int


class AIRecentFailure(BaseModel):
    """
    Uma falha recente de análise de IA (vinda do log de auditoria).
    """

    exam_id: int | None = None
    description: str | None = None
    created_at: datetime


class AIDailyVolume(BaseModel):
    """
    Volume de análises de IA em um dia específico (últimos 30 dias).
    """

    date: str
    count: int


class AIMetricsResponse(BaseModel):
    """
    Métricas agregadas do módulo de IA — exclusivas do Administrador
    Master (não é exposto a nenhum outro perfil). Reúne informações de
    governança/infraestrutura do modelo, distintas dos indicadores
    operacionais já disponíveis a todos os perfis no Dashboard (RF54-56).
    """

    total_analyses: int
    by_model: list[AIModelUsage]

    confidence_mean: float | None = None
    reviewed_confidence_mean: float | None = None
    reviewed_analyses_count: int = 0
    false_positive_count: int = 0
    false_negative_count: int = 0
    confidence_min: float | None = None
    confidence_max: float | None = None
    confidence_distribution: dict[str, int]

    processing_time_mean_ms: float | None = None
    processing_time_min_ms: int | None = None
    processing_time_max_ms: int | None = None

    divergence_rate: float

    failure_count: int
    recent_failures: list[AIRecentFailure]

    analyses_last_30_days: list[AIDailyVolume]
