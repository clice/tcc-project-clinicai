"""
Schemas do módulo de clínicas.

Este arquivo define os modelos Pydantic usados para validação de entrada,
atualização parcial e resposta da API.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.validators import (
    normalize_optional_text,
    normalize_phone,
    normalize_required_text,
    normalize_state,
    normalize_zip_code,
    validate_cnpj,
)


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
    
    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """
        Remove espaços extras do nome.
        """
        return normalize_required_text(value, "Nome da clínica é obrigatório.")

    @field_validator(
        "address",
        "number",
        "complement",
        "neighborhood",
        "city",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @field_validator("state")
    @classmethod
    def normalize_state_field(cls, value: str | None) -> str | None:
        return normalize_state(value)

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj_field(cls, value: str) -> str:
        """
        Valida CNPJ removendo espaços em branco.
        """
        cleaned = validate_cnpj(value)
        assert cleaned is not None
        return cleaned

    @field_validator("zip_code")
    @classmethod
    def normalize_zip_code_field(cls, value: str | None) -> str | None:
        return normalize_zip_code(value)

    @field_validator("phone", "mobile_phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        return normalize_phone(value)


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

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return normalize_required_text(value, "Nome da clínica é obrigatório.")

    @field_validator(
        "address",
        "number",
        "complement",
        "neighborhood",
        "city",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @field_validator("state")
    @classmethod
    def normalize_state_field(cls, value: str | None) -> str | None:
        return normalize_state(value)

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj_field(cls, value: str | None) -> str | None:
        return validate_cnpj(value, required=False)

    @field_validator("zip_code")
    @classmethod
    def normalize_zip_code_field(cls, value: str | None) -> str | None:
        return normalize_zip_code(value)

    @field_validator("phone", "mobile_phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        return normalize_phone(value)
    

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
