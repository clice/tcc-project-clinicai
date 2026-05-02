"""
Schemas do módulo de clínicas.

Este arquivo define os modelos Pydantic usados para validação de entrada,
atualização parcial e resposta da API.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ClinicBase(BaseModel):
    """
    Campos compartilhados entre criação e resposta.
    """
    
    name: str = Field(..., min_length=3, max_length=180)
    cnpj: str = Field(..., min_length=14, max_length=18)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    mobile_phone: str | None = Field(default=None, max_length=20)

    zip_code: str | None = Field(default=None, max_length=10)
    address: str | None = Field(default=None, max_length=255)
    number: str | None = Field(default=None, max_length=20)
    complement: str | None = Field(default=None, max_length=100)
    neighborhood: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=2)

    status_id: int
    


class ClinicCreate(ClinicBase):
    """
    Schema usado para criação de clínica.
    """
    
    pass


class ClinicUpdate(BaseModel):
    """
    Schema usado para atualização parcial de clínica.
    Todos os campos são opcionais porque o endpoint usa PATCH.
    """
    
    name: str | None = Field(default=None, min_length=3, max_length=180)
    cnpj: str | None = Field(default=None, min_length=14, max_length=18)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    mobile_phone: str | None = Field(default=None, max_length=20)

    zip_code: str | None = Field(default=None, max_length=10)
    address: str | None = Field(default=None, max_length=255)
    number: str | None = Field(default=None, max_length=20)
    complement: str | None = Field(default=None, max_length=100)
    neighborhood: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=2)

    status_id: int | None = None
    

class ClinicResponse(BaseModel):
    """
    Schema usado nas respostas da API.
    """
    
    id: int

    name: str
    cnpj: str
    email: EmailStr | None = None
    phone: str | None = None
    mobile_phone: str | None = None

    zip_code: str | None = None
    address: str | None = None
    number: str | None = None
    complement: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None

    status_id: int
    status_name: str | None = None
    status_display_name: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }