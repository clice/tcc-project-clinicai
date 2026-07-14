"""
Schemas do módulo de exames.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.common.schemas import StrictRequestModel
from app.common.validators import normalize_optional_text, normalize_required_text


class ExamBase(StrictRequestModel):
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

    @field_validator("exam_type", "title")
    @classmethod
    def normalize_required_fields(cls, value: str) -> str:
        return normalize_required_text(value, "Campo obrigatório.")

    @field_validator(
        "description",
        "clinical_indication",
    )
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


class ExamCreate(ExamBase):
    """
    Schema usado para criação de exame.
    """

    pass


class ExamUpdate(StrictRequestModel):
    """
    Schema usado para atualização parcial de exame.
    """

    exam_type: str | None = Field(default=None, min_length=2, max_length=80)
    exam_date: date | None = None

    title: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = None
    clinical_indication: str | None = None
    findings: str | None = None
    conclusion: str | None = None

    @field_validator("exam_type", "title")
    @classmethod
    def normalize_required_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None

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


class ExamMedicalReview(StrictRequestModel):
    """
    Schema usado quando o médico realiza a revisão do resultado da IA.

    has_discrepancy indica o desfecho da revisão:
    - False (padrão): médico confirma a análise da IA -> exame vai para 'completed'.
    - True: médico identificou um problema/divergência na análise da IA
      -> exame vai para 'completed_with_divergence'.

    Em ambos os casos o exame é encerrado (nenhum dos dois reabre o exame
    para nova ação); a diferença é só a sinalização do resultado, para não
    misturar exames concluídos normalmente com os que tiveram divergência.
    """
    findings: str = Field(..., min_length=3)
    conclusion: str = Field(..., min_length=3)
    has_discrepancy: bool = False

    @field_validator("findings", "conclusion")
    @classmethod
    def normalize_required_fields(cls, value: str) -> str:
        return normalize_required_text(value, "Campo obrigatório.")
    

class ExamResponse(BaseModel):
    """
    Schema usado nas respostas da API.
    """

    id: int

    clinic_id: int
    clinic_name: str | None = None

    patient_id: int
    patient_name: str | None = None

    doctor_id: int | None = None
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

    reviewed_by_id: int | None = None
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None

    file_path: str | None = None
    file_name: str | None = None
    file_mime_type: str | None = None

    # Preenchidos apenas se o exame tiver análise de IA concluída e o
    # usuário tiver permissão de ver resultados diagnósticos (Funcionário
    # da Clínica nunca recebe esses dois campos preenchidos — ver
    # build_exam_response no service).
    ai_prediction_label: str | None = None
    ai_prediction_class: int | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
