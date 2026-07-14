"""
Schemas do módulo de pacientes.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.schemas import StrictRequestModel
from app.common.validators import (
    normalize_optional_email,
    normalize_optional_text,
    normalize_phone,
    normalize_required_text,
    normalize_state,
    normalize_zip_code,
    validate_birth_date,
    validate_cpf,
)


PatientSex = Literal["male", "female", "other", "not_informed"]


class PatientBase(StrictRequestModel):
    """
    Campos compartilhados entre criação e resposta.
    """

    clinic_id: int
    doctor_id: int

    name: str = Field(..., min_length=3, max_length=180)
    cpf: str = Field(..., min_length=11, max_length=14)
    birth_date: date | None = None
    sex: PatientSex | None = None
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None

    zip_code: str | None = Field(default=None, max_length=10)
    address: str | None = Field(default=None, max_length=255)
    number: str | None = Field(default=None, max_length=20)
    complement: str | None = Field(default=None, max_length=100)
    neighborhood: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=2)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return normalize_required_text(value, "Nome do paciente é obrigatório.")

    @field_validator(
        "address",
        "number",
        "complement",
        "neighborhood",
        "city",
    )
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @field_validator("state")
    @classmethod
    def normalize_state_field(cls, value: str | None) -> str | None:
        return normalize_state(value)

    @field_validator("cpf")
    @classmethod
    def validate_cpf_field(cls, value: str) -> str:
        cleaned = validate_cpf(value, required=True)
        assert cleaned is not None
        return cleaned

    @field_validator("zip_code")
    @classmethod
    def normalize_zip_code_field(cls, value: str | None) -> str | None:
        return normalize_zip_code(value)

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str | None) -> str | None:
        return normalize_optional_email(value)

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date_field(cls, value: date | None) -> date | None:
        return validate_birth_date(value)


class PatientCreate(PatientBase):
    """
    Schema usado para criação de paciente.
    O status inicial será definido automaticamente como active no service.
    """

    pass


class PatientUpdate(StrictRequestModel):
    """
    Schema usado para atualização parcial de paciente.
    Todos os campos são opcionais porque o endpoint usa PATCH.
    """

    clinic_id: int | None = None
    doctor_id: int | None = None

    name: str | None = Field(default=None, min_length=3, max_length=180)
    cpf: str | None = Field(default=None, min_length=11, max_length=14)
    birth_date: date | None = None
    sex: PatientSex | None = None
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None

    zip_code: str | None = Field(default=None, max_length=10)
    address: str | None = Field(default=None, max_length=255)
    number: str | None = Field(default=None, max_length=20)
    complement: str | None = Field(default=None, max_length=100)
    neighborhood: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=2)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return normalize_required_text(value, "Nome do paciente é obrigatório.")

    @field_validator(
        "address",
        "number",
        "complement",
        "neighborhood",
        "city",
    )
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @field_validator("state")
    @classmethod
    def normalize_state_field(cls, value: str | None) -> str | None:
        return normalize_state(value)

    @field_validator("cpf")
    @classmethod
    def validate_cpf_field(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return validate_cpf(value, required=True)

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date_field(cls, value: date | None) -> date | None:
        return validate_birth_date(value)

    @field_validator("zip_code")
    @classmethod
    def normalize_zip_code_field(cls, value: str | None) -> str | None:
        return normalize_zip_code(value)

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str | None) -> str | None:
        return normalize_optional_email(value)


class PatientResponse(BaseModel):
    """
    Schema usado nas respostas da API.
    """

    id: int

    clinic_id: int
    clinic_name: str | None = None

    doctor_id: int
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
