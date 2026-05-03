"""
Schemas do módulo de permissions.

Este arquivo define os modelos usados para validar os dados recebidos pela API,
padronizar os dados enviados nas respostas e documentar automaticamente os endpoints no Swagger.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.constants import PermissionAction, SystemModule
from app.common.validators import (
    normalize_lower_text,
    normalize_optional_text,
    normalize_required_text,
)


def validate_permission_name(value: str) -> str:
    """
    Valida o nome interno da permissão no formato modulo:acao.

    Exemplo:
    users:create
    patients:read
    exams:change_status
    """
    value = normalize_lower_text(value, "Nome da permissão é obrigatório.")

    parts = value.split(":")

    if len(parts) != 2:
        raise ValueError("Use o padrão modulo:acao. Exemplo: users:create.")

    module, action = parts

    valid_modules = {item.value for item in SystemModule}
    valid_actions = {item.value for item in PermissionAction}

    if module not in valid_modules:
        raise ValueError("Módulo da permissão inválido.")

    if action not in valid_actions:
        raise ValueError("Ação da permissão inválida.")

    return value


class PermissionBase(BaseModel):
    """
    Schema base com os campos compartilhados entre criação e resposta.
    """

    name: str = Field(..., min_length=5, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    module: SystemModule

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return validate_permission_name(value)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        return normalize_required_text(value, "Nome de exibição é obrigatório.")

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


class PermissionCreate(PermissionBase):
    """
    Schema usado para criação de permission.
    Todos os campos principais são obrigatórios.
    """

    pass


class PermissionUpdate(BaseModel):
    """
    Schema usado para atualização de permission.
    Todos os campos são opcionais para permitir update parcial com PATCH.
    """

    name: str | None = Field(default=None, min_length=5, max_length=100)
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    module: SystemModule | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return validate_permission_name(value)

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


class PermissionResponse(BaseModel):
    """
    Schema usado para retorno de permissions nas respostas da API.
    """

    id: int
    name: str
    display_name: str
    description: str | None = None
    module: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
