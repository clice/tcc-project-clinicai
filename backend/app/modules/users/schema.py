"""
Schemas do módulo de usuários.

Este arquivo define os modelos Pydantic usados para validar entradas,
padronizar respostas e proteger dados sensíveis como password_hash.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Schema base com campos compartilhados.
    """
    
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr = Field(...)
    cpf: str | None = Field(default=None, max_length=14)
    phone: str | None = Field(default=None, max_length=20)
    role_id: int
    status_id: int
    clinic_id: int | None = None


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
    cpf: str | None = Field(default=None, max_length=14)
    phone: str | None = Field(default=None, max_length=20)
    role_id: int | None = None
    status_id: int | None = None
    clinic_id: int | None = None


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