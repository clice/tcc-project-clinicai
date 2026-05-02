"""
Service do módulo de autenticação.

Aqui ficam as regras de negócio relacionadas ao login,
refresh token e usuário autenticado.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from app.modules.users.model import User


def authenticate_user(
    db: Session,
    *,
    email: str,
    password: str,
) -> User:
    """
    Autentica um usuário a partir de e-mail e senha.
    Retorna o usuário autenticado ou lança erro caso os dados sejam inválidos.
    """

    normalized_email = email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    validate_active_user(user)

    user.last_access_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    return user


def validate_active_user(user: User) -> None:
    """
    Valida se o usuário está ativo no sistema.
    """

    if (
        not user.status
        or user.status.applies_to != "user"
        or user.status.name != "active"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Entre em contato com o administrador.",
        )


def create_user_tokens(user: User) -> dict:
    """
    Cria access token e refresh token para o usuário autenticado.
    """

    token_data = {"sub": user.email}

    return {
        "access_token": create_access_token(data=token_data),
        "refresh_token": create_refresh_token(data=token_data),
        "token_type": "bearer",
    }


def refresh_user_tokens(db: Session, refresh_token: str) -> dict:
    """
    Valida o refresh token e gera novos tokens.
    """

    payload = decode_refresh_token(refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado.",
        )

    email = payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    validate_active_user(user)

    return create_user_tokens(user)


def build_current_user_response(user: User) -> dict:
    """
    Monta a resposta da rota /auth/me com dados do usuário autenticado.
    """

    permissions = []

    if user.role and user.role.role_permissions:
        permissions = [
            role_permission.permission.name
            for role_permission in user.role.role_permissions
            if role_permission.permission is not None
        ]

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role_id": user.role_id,
        "role_name": user.role.name,
        "role_display_name": user.role.display_name,
        "permissions": permissions,
        "status_id": user.status_id,
        "status_name": user.status.name,
        "status_display_name": user.status.display_name,
        "clinic_id": user.clinic_id,
        "clinic_name": user.clinic.name if user.clinic else None,
        "last_access_at": user.last_access_at,
    }
