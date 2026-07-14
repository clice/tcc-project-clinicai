"""
Schemas do módulo de roles.

Este arquivo define os modelos usados para validar os dados recebidos pela API,
padronizar os dados enviados nas respostas e documentar automaticamente os endpoints no Swagger.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.constants import RoleName
from app.common.schemas import StrictRequestModel
from app.common.validators import (
    normalize_optional_text,
    normalize_required_text,
)


class RoleBase(StrictRequestModel):
    """
    Schema base com os campos compartilhados entre criação e resposta.
    """

    name: RoleName
    display_name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        return normalize_required_text(value, "Nome de exibição é obrigatório.")

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


class RoleCreate(RoleBase):
    """
    Schema usado para criação de role.
    Todos os campos principais são obrigatórios.
    """

    pass


class RoleUpdate(StrictRequestModel):
    """
    Schema usado para atualização de role.
    Todos os campos são opcionais para permitir update parcial.

    'name' propositalmente NÃO está aqui: é o campo do qual toda a lógica
    de autorização do sistema depende (ex: role.name == "admin_master").
    Permitir renomear um perfil já existente para outro valor do enum
    poderia, na prática, transformar um perfil comum em admin_master (ou
    vice-versa) sem passar por nenhuma validação de negócio adicional.
    'name' só é definido na criação do perfil.
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


class RoleResponse(BaseModel):
    """
    Schema usado para retorno de roles nas respostas da API.
    """

    id: int
    name: str
    display_name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
