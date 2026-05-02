"""
Schemas do módulo de status.

Este arquivo define os modelos usados para validar os dados recebidos pela API,
padronizar os dados enviados nas respostas e documentar automaticamente os endpoints no Swagger.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class StatusBase(BaseModel):
    """
    Schema base com os campos compartilhados entre criação e resposta.
    """
    
    name: str = Field(..., min_length=2, max_length=50)
    display_name: str = Field(..., min_length=2, max_length=100)
    applies_to: str = Field(..., min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)


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

    name: str | None = Field(default=None, min_length=2, max_length=50)
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    applies_to: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)


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