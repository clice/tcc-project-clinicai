"""Schemas do módulo de usuários."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.schemas import StrictRequestModel
from app.common.validators import (
    normalize_email,
    normalize_optional_email,
    normalize_crm_number,
    normalize_crm_uf,
    normalize_phone,
    normalize_required_text,
    validate_cpf,
    validate_password_length,
)


class UserBase(StrictRequestModel):
    """Campos obrigatórios usados na criação de usuários."""

    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr = Field(...)
    cpf: str = Field(..., max_length=14)
    phone: str | None = Field(default=None, max_length=20)
    crm_number: str | None = Field(default=None, max_length=10)
    crm_uf: str | None = Field(default=None, max_length=2)
    role_id: int
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
        cleaned = validate_cpf(value, required=True)
        assert cleaned is not None
        return cleaned

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("crm_number")
    @classmethod
    def normalize_crm_number_field(cls, value: str | None) -> str | None:
        return normalize_crm_number(value)

    @field_validator("crm_uf")
    @classmethod
    def normalize_crm_uf_field(cls, value: str | None) -> str | None:
        return normalize_crm_uf(value)


class UserCreate(UserBase):
    """Payload administrativo para criação de usuário."""

    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_field(cls, value: str) -> str:
        return validate_password_length(value)


class UserProfileUpdate(StrictRequestModel):
    """Campos cadastrais compartilhados pelas atualizações de usuário."""

    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    cpf: str | None = Field(default=None, max_length=14)
    phone: str | None = Field(default=None, max_length=20)
    crm_number: str | None = Field(default=None, max_length=10)
    crm_uf: str | None = Field(default=None, max_length=2)

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

    @field_validator("crm_number")
    @classmethod
    def normalize_crm_number_field(cls, value: str | None) -> str | None:
        return normalize_crm_number(value)

    @field_validator("crm_uf")
    @classmethod
    def normalize_crm_uf_field(cls, value: str | None) -> str | None:
        return normalize_crm_uf(value)


class UserAdminUpdate(UserProfileUpdate):
    """Atualização administrativa de dados, role e vínculo de clínica.

    ``status_id`` não pertence a este payload. Ativação e inativação usam
    endpoints dedicados para garantir auditoria e revogação de sessão.
    """

    role_id: int | None = None
    clinic_id: int | None = None


class UserSelfUpdate(UserProfileUpdate):
    """Autoedição limitada aos próprios dados cadastrais."""

    pass


# Alias de compatibilidade para importações anteriores. Novas rotas devem usar
# explicitamente UserAdminUpdate ou UserSelfUpdate.
UserUpdate = UserAdminUpdate


class UserPasswordUpdate(StrictRequestModel):
    """Payload exclusivo para troca ou redefinição de senha."""

    password: str = Field(..., min_length=8, max_length=128)
    current_password: str | None = Field(default=None, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_field(cls, value: str) -> str:
        return validate_password_length(value)


class UserResponse(BaseModel):
    """Resposta administrativa ou do próprio usuário, sem credenciais."""

    id: int
    name: str
    email: str
    cpf: str
    phone: str | None = None
    crm_number: str | None = None
    crm_uf: str | None = None
    role_id: int
    status_id: int
    clinic_id: int | None = None
    last_access_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(UserResponse):
    """Resposta enriquecida para gestão administrativa e perfil próprio."""

    role_name: str | None = None
    role_display_name: str | None = None
    status_name: str | None = None
    status_display_name: str | None = None
    clinic_name: str | None = None


class UserOptionResponse(BaseModel):
    """Opção mínima para seletores de médico, sem CPF ou contato."""

    id: int
    name: str


class UserManagementRoleOption(BaseModel):
    """Único papel que o gestor pode atribuir."""

    id: int
    name: str
    display_name: str


class UserManagementClinicOption(BaseModel):
    """Clínica ativa vinculada ao gestor."""

    id: int
    name: str
    status_name: str


class DoctorManagementOptionsResponse(BaseModel):
    """Catálogos mínimos necessários à gestão de médicos."""

    role: UserManagementRoleOption
    clinic: UserManagementClinicOption
