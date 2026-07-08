"""
Schemas do módulo de usuários.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.validators import (
    normalize_email,
    normalize_optional_email,
    normalize_phone,
    normalize_required_text,
    validate_cpf,
)


class UserBase(BaseModel):
    """
    Schema base com campos compartilhados.
    """

    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr = Field(...)
    cpf: str = Field(..., max_length=14)
    phone: str | None = Field(default=None, max_length=20)
    role_id: int
    status_id: int
    clinic_id: int | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return normalize_required_text(value, "Nome completo é obrigatório.")

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("cpf")
    @classmethod
    def validate_cpf_field(cls, value: str) -> str:
        return validate_cpf(value, required=True)

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        return normalize_phone(value)


class UserCreate(UserBase):
    """
    Schema usado para criação de usuário.
    """

    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """
    Schema usado para atualização parcial de usuário.
    Todos os campos são opcionais porque o endpoint usa PATCH.
    """

    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    cpf: str | None = Field(default=None, max_length=14)
    phone: str | None = Field(default=None, max_length=20)
    role_id: int | None = None
    status_id: int | None = None
    clinic_id: int | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return normalize_required_text(value, "Nome completo é obrigatório.")

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str | None) -> str | None:
        return normalize_optional_email(value)

    @field_validator("cpf")
    @classmethod
    def validate_cpf_field(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return validate_cpf(value, required=True)

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        return normalize_phone(value)


class UserPasswordUpdate(BaseModel):
    """
    Schema exclusivo para troca de senha.

    current_password é obrigatório quando o próprio usuário troca a própria
    senha (validado no service). Não é exigido quando um admin_master
    reseta a senha de outro usuário.
    """

    password: str = Field(..., min_length=8, max_length=128)
    current_password: str | None = Field(default=None, max_length=128)


class UserResponse(BaseModel):
    """
    Schema usado para resposta da API.
    Nunca retorna password_hash.
    """

    id: int
    name: str
    email: str
    cpf: str
    phone: str | None = None
    role_id: int
    status_id: int
    clinic_id: int | None = None
    last_access_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class UserListResponse(UserResponse):
    """
    Schema usado na listagem.
    """

    role_name: str | None = None
    status_name: str | None = None
    status_display_name: str | None = None
    clinic_name: str | None = None
