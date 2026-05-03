"""
Schemas do módulo de status.

Este arquivo define os modelos usados para validar os dados recebidos pela API,
padronizar os dados enviados nas respostas e documentar automaticamente os endpoints no Swagger.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.constants import StatusName, StatusScope
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
    """

    name: StatusName | None = None
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    applies_to: StatusScope | None = None
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
    