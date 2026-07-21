"""
Schemas do módulo de autenticação.

Define os modelos usados nas respostas de login, refresh token
e na rota /auth/me.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.schemas import StrictRequestModel


class TokenResponse(BaseModel):
    """
    Schema retornado após login ou renovação de token.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(StrictRequestModel):
    """
    Schema usado para solicitar um novo access token.
    """
    refresh_token: str


class CurrentUserResponse(BaseModel):
    """
    Schema retornado com os dados do usuário autenticado.
    """
    id: int
    name: str
    email: str

    role_id: int
    role_name: str
    role_display_name: str

    permissions: list[str] = Field(default_factory=list)

    status_id: int
    status_name: str
    status_display_name: str

    clinic_id: int | None = None
    clinic_name: str | None = None

    last_access_at: datetime | None = None
