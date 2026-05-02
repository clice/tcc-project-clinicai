"""
Schemas do módulo de permissions.

Este arquivo define os modelos usados para validar os dados recebidos pela API,
padronizar os dados enviados nas respostas e documentar automaticamente os endpoints no Swagger.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    """
    Schema base com os campos compartilhados entre criação e resposta.
    """

    name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    module: str = Field(..., min_length=2, max_length=50)


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

    name: str | None = Field(default=None, min_length=2, max_length=100)
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    module: str | None = Field(default=None, min_length=2, max_length=50)


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