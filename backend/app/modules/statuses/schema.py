"""
Schemas do módulo de status.

Este arquivo define os modelos usados para validar os dados recebidos pela API,
padronizar os dados enviados nas respostas e documentar automaticamente os endpoints no Swagger.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.constants import ALLOWED_STATUS_BY_SCOPE, StatusName, StatusScope
from app.common.validators import (
    normalize_optional_text,
    normalize_required_text,
)


class StatusBase(BaseModel):
    """
    Schema base com os campos compartilhados entre criação e resposta.
    """

    name: StatusName
    display_name: str = Field(..., min_length=2, max_length=100)
    applies_to: StatusScope
    description: str | None = Field(default=None, max_length=255)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        return normalize_required_text(value, "Nome de exibição é obrigatório.")

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_name_applies_to_pair(self) -> "StatusBase":
        """
        Confere que a combinação (name, applies_to) é uma das oficialmente
        previstas — sem isso, name e applies_to eram validados como enums
        independentes, aceitando pares sem sentido como completed/user.
        """
        permitidos = ALLOWED_STATUS_BY_SCOPE.get(self.applies_to.value, set())
        if self.name.value not in permitidos:
            permitidos_str = ", ".join(sorted(permitidos)) or "(nenhum)"
            raise ValueError(
                f"Status '{self.name.value}' não é válido para o escopo "
                f"'{self.applies_to.value}'. Válidos para esse escopo: {permitidos_str}."
            )
        return self


class StatusCreate(StatusBase):
    """
    Schema usado para criação de statuses.
    Todos os campos principais são obrigatórios.
    """

    pass


class StatusUpdate(BaseModel):
    """
    Schema usado para atualização de status.
    Todos os campos são opcionais para permitir update parcial com PATCH.

    'name' e 'applies_to' propositalmente NÃO estão aqui: praticamente toda
    regra de negócio do sistema (incluindo o bloqueio de login em
    get_current_user, que verifica status.name == "active" diretamente)
    depende desses dois campos para identificar um status específico.
    Alterá-los numa linha já existente reatribuiria silenciosamente o
    significado daquele status para todo mundo que o usa, sem nenhuma
    trava que impeça isso além da checagem de duplicidade. 'name' e
    'applies_to' só são definidos na criação do status.
    """

    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return normalize_required_text(value, "Nome de exibição é obrigatório.")

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


class StatusResponse(BaseModel):
    """
    Schema usado para retorno de status nas respostas da API.
    """

    id: int
    name: str
    display_name: str
    applies_to: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
    