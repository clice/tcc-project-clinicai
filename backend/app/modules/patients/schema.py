"""
Schemas do módulo de pacientes.

Este arquivo define os modelos Pydantic usados para validação de entrada,
atualização parcial e resposta da API.
"""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class PatientBase(BaseModel):
    """
    Campos compartilhados entre criação e resposta.
    """

    clinic_id: int
    doctor_id: int | None = None

    name: str = Field(..., min_length=3, max_length=180)
    cpf: str = Field(..., min_length=11, max_length=14)
    birth_date: date | None = None
    sex: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None

    zip_code: str | None = Field(default=None, max_length=10)
    address: str | None = Field(default=None, max_length=255)
    number: str | None = Field(default=None, max_length=20)
    complement: str | None = Field(default=None, max_length=100)
    neighborhood: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=2)


class PatientCreate(PatientBase):
    """
    Schema usado para criação de paciente.
    O status inicial será definido automaticamente como active no service.
    """

    pass


class PatientUpdate(BaseModel):
    """
    Schema usado para atualização parcial de paciente.
    """

    clinic_id: int | None = None
    doctor_id: int | None = None

    name: str | None = Field(default=None, min_length=3, max_length=180)
    cpf: str | None = Field(default=None, min_length=11, max_length=14)
    birth_date: date | None = None
    sex: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None

    zip_code: str | None = Field(default=None, max_length=10)
    address: str | None = Field(default=None, max_length=255)
    number: str | None = Field(default=None, max_length=20)
    complement: str | None = Field(default=None, max_length=100)
    neighborhood: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=2)


class PatientResponse(BaseModel):
    """
    Schema usado nas respostas da API.
    """

    id: int

    clinic_id: int
    clinic_name: str | None = None

    doctor_id: int | None = None
    doctor_name: str | None = None

    status_id: int
    status_name: str | None = None
    status_display_name: str | None = None

    name: str
    cpf: str
    birth_date: date | None = None
    sex: str | None = None
    phone: str | None = None
    email: EmailStr | None = None

    zip_code: str | None = None
    address: str | None = None
    number: str | None = None
    complement: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }