"""
Schemas do módulo de análises de IA.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.validators import normalize_optional_text, normalize_required_text


class AIAnalysisBase(BaseModel):
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


class AIAnalysisUpdate(BaseModel):
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

    prediction_label: str
    prediction_class: int | None = None
    confidence: float

    model_name: str
    model_version: str

    gradcam_path: str | None = None
    processing_time_ms: int | None = None

    ai_notes: str | None = None
    raw_response: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
