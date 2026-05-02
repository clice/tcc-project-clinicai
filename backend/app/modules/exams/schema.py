"""
Schemas do módulo de exames.

Define os modelos Pydantic usados para criação, atualização parcial
e resposta da API.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class ExamBase(BaseModel):
    """
    Campos compartilhados entre criação e resposta.
    """

    clinic_id: int
    patient_id: int
    doctor_id: int | None = None
    status_id: int

    exam_type: str = Field(..., min_length=2, max_length=80)
    exam_date: date | None = None

    title: str = Field(..., min_length=3, max_length=180)
    description: str | None = None
    clinical_indication: str | None = None
    findings: str | None = None
    conclusion: str | None = None

    ai_analysis_status: str | None = Field(default=None, max_length=50)
    ai_summary: str | None = None

    file_path: str | None = Field(default=None, max_length=255)
    file_name: str | None = Field(default=None, max_length=180)
    file_mime_type: str | None = Field(default=None, max_length=100)


class ExamCreate(ExamBase):
    """
    Schema usado para criação de exame.
    """

    pass


class ExamUpdate(BaseModel):
    """
    Schema usado para atualização parcial de exame.
    """

    clinic_id: int | None = None
    patient_id: int | None = None
    doctor_id: int | None = None
    status_id: int | None = None

    exam_type: str | None = Field(default=None, min_length=2, max_length=80)
    exam_date: date | None = None

    title: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = None
    clinical_indication: str | None = None
    findings: str | None = None
    conclusion: str | None = None

    ai_analysis_status: str | None = Field(default=None, max_length=50)
    ai_summary: str | None = None

    file_path: str | None = Field(default=None, max_length=255)
    file_name: str | None = Field(default=None, max_length=180)
    file_mime_type: str | None = Field(default=None, max_length=100)


class ExamResponse(BaseModel):
    """
    Schema usado nas respostas da API.
    """

    id: int

    clinic_id: int
    patient_id: int
    doctor_id: int | None = None
    status_id: int

    exam_type: str
    exam_date: date | None = None

    title: str
    description: str | None = None
    clinical_indication: str | None = None
    findings: str | None = None
    conclusion: str | None = None

    ai_analysis_status: str | None = None
    ai_summary: str | None = None

    file_path: str | None = None
    file_name: str | None = None
    file_mime_type: str | None = None

    status_name: str | None = None
    status_display_name: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }