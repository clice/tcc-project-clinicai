"""
Schemas do módulo de exames.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.common.validators import normalize_optional_text, normalize_required_text


class ExamBase(BaseModel):
    """
    Campos compartilhados entre criação e resposta.
    """

    clinic_id: int
    patient_id: int
    doctor_id: int | None = None

    exam_type: str = Field(..., min_length=2, max_length=80)
    exam_date: date | None = None

    title: str = Field(..., min_length=3, max_length=180)
    description: str | None = None
    clinical_indication: str | None = None
    findings: str | None = None
    conclusion: str | None = None

    @field_validator("exam_type", "title")
    @classmethod
    def normalize_required_fields(cls, value: str) -> str:
        return normalize_required_text(value, "Campo obrigatório.")

    @field_validator(
        "description",
        "clinical_indication",
        "findings",
        "conclusion",
    )
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


class ExamCreate(ExamBase):
    """
    Schema usado para criação de exame.
    """

    pass


class ExamUpdate(BaseModel):
    """
    Schema usado para atualização parcial de exame.
    """

    clinic_id: int
    patient_id: int
    doctor_id: int | None = None

    exam_type: str = Field(..., min_length=2, max_length=80)
    exam_date: date | None = None

    title: str = Field(..., min_length=3, max_length=180)
    description: str | None = None
    clinical_indication: str | None = None
    findings: str | None = None
    conclusion: str | None = None

    @field_validator("exam_type", "title")
    @classmethod
    def normalize_required_fields(cls, value: str) -> str:
        return normalize_required_text(value, "Campo obrigatório.")

    @field_validator(
        "description",
        "clinical_indication",
        "findings",
        "conclusion",
    )
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


class ExamResponse(BaseModel):
    """
    Schema usado nas respostas da API.
    """

    id: int

    clinic_id: int
    clinic_name: str | None = None

    patient_id: int
    patient_name: str | None = None

    doctor_id: int
    doctor_name: str | None = None

    status_id: int
    status_name: str | None = None
    status_display_name: str | None = None

    exam_type: str
    exam_date: date | None = None

    title: str
    description: str | None = None
    clinical_indication: str | None = None
    findings: str | None = None
    conclusion: str | None = None

    file_path: str | None = None
    file_name: str | None = None
    file_mime_type: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
