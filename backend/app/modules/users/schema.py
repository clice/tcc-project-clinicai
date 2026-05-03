"""
Schemas do módulo de usuários.

Este arquivo define os modelos Pydantic usados para validar entradas,
padronizar respostas e proteger dados sensíveis como password_hash.
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
        """
        Remove espaços extras do nome completo.
        """
        return normalize_required_text(value, "Nome completo é obrigatório.")

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        """
        Normaliza o e-mail para evitar duplicidade por caixa alta/baixa.
        """
        return normalize_email(value)

    @field_validator("cpf")
    @classmethod
    def normalize_cpf(cls, value: str | None) -> str | None:
        """
        Salva CPF apenas com números.
        """
        return validate_cpf(value, required=True)

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        """
        Salva telefone apenas com números.
        """
        return normalize_phone(value)


class UserCreate(UserBase):
    """
    Schema usado para criação de usuário.
    A senha chega como password, mas nunca é salva diretamente.
    Ela será convertida para hash no service.
    """
    
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(BaseModel):
    """
    Schema usado para atualização parcial de usuário.
    Todos os campos são opcionais porque o endpoint usa PATCH.
    """
    
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    cpf: str = Field(..., max_length=14)
    phone: str | None = Field(default=None, max_length=20)
    role_id: int | None = None
    status_id: int | None = None
    clinic_id: int | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        """
        Remove espaços extras do nome completo.
        """
        if value is None:
            return None

        return normalize_required_text(value, "Nome completo é obrigatório.")

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str | None) -> str | None:
        """
        Normaliza o e-mail para evitar duplicidade por caixa alta/baixa.
        """
        return normalize_optional_email(value)

    @field_validator("cpf")
    @classmethod
    def normalize_cpf(cls, value: str | None) -> str | None:
        """
        Salva CPF apenas com números.
        """
        return validate_cpf(value, required=True)

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        """
        Salva telefone apenas com números.
        """
        return normalize_phone(value)


class UserPasswordUpdate(BaseModel):
    """
    Schema exclusivo para troca de senha.
    """
    
    password: str = Field(..., min_length=6, max_length=128)


class UserResponse(BaseModel):
    """
    Schema usado para resposta da API.
    Nunca retorna password_hash.
    """
    
    id: int
    name: str
    email: str
    cpf: str | None = None
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
    Inclui nomes amigáveis de relacionamentos para facilitar o frontend.
    """
    
    role_name: str | None = None
    status_name: str | None = None
    status_display_name: str | None = None
    clinic_name: str | None = None
