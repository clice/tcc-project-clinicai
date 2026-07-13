"""
Schemas do módulo de role_permissions.

Define os modelos usados para validar criação, atualização e resposta
dos vínculos entre perfis e permissões.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class RolePermissionBase(BaseModel):
    """
    Schema base com os campos compartilhados.
    """

    role_id: int = Field(..., gt=0)
    permission_id: int = Field(..., gt=0)


class RolePermissionCreate(RolePermissionBase):
    """
    Schema usado para criar vínculo entre role e permission.
    """

    pass


class RolePermissionUpdate(BaseModel):
    """
    Schema usado para atualização parcial do vínculo.
    Embora esse tipo de vínculo normalmente seja removido e recriado,
    o PATCH pode ser útil no painel administrativo.
    """

    role_id: int | None = Field(default=None, gt=0)
    permission_id: int | None = Field(default=None, gt=0)


class RolePermissionSyncRequest(BaseModel):
    """
    Schema usado para sincronizar, de uma vez só, todas as permissões de
    uma role (substitui o padrão anterior do frontend de múltiplos
    POST/DELETE sem transação).
    """

    permission_ids: list[int] = Field(default_factory=list)


class RolePermissionResponse(BaseModel):
    """
    Schema usado para retorno da API.
    """

    id: int
    role_id: int
    permission_id: int

    role_name: str | None = None
    role_display_name: str | None = None
    permission_name: str | None = None
    permission_display_name: str | None = None
    permission_module: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
    