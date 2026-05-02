"""
Schemas do módulo de roles.

Este arquivo define os modelos usados para validar os dados recebidos pela API,
padronizar os dados enviados nas respostas e documentar automaticamente os endpoints no Swagger.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """
    Schema base com os campos compartilhados entre criação e resposta.
    """

    name: str = Field(..., min_length=2, max_length=50)
    display_name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class RoleCreate(RoleBase):
    """
    Schema usado para criação de role.
    Todos os campos principais são obrigatórios.
    """

    pass


class RoleUpdate(BaseModel):
    """
    Schema usado para atualização de role.
    Todos os campos são opcionais para permitir update parcial.
    """

    name: str | None = Field(default=None, min_length=2, max_length=50)
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)


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