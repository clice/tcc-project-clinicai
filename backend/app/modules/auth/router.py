"""
Rotas do módulo de autenticação.

Este arquivo expõe os endpoints de login, refresh token
e dados do usuário autenticado.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.schema import (
    CurrentUserResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.modules.auth.service import (
    authenticate_user,
    build_current_user_response,
    create_user_tokens,
    logout_user,
    refresh_user_tokens,
)
from app.modules.users.model import User


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login_route(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Realiza login do usuário.
    O campo username do OAuth2PasswordRequestForm será usado como e-mail.
    """
    user = authenticate_user(
        db=db,
        email=form_data.username,
        password=form_data.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return create_user_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_route(
    request: Request,
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Gera novos tokens usando um refresh token válido.
    """
    return refresh_user_tokens(
        db=db,
        refresh_token=data.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/logout")
def logout_route(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Realiza logout do usuário.
    """
    return logout_user(
        db=db,
        user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    

@router.get("/me", response_model=CurrentUserResponse)
def get_me_route(
    current_user: User = Depends(get_current_user),
):
    """
    Retorna os dados do usuário autenticado.
    """
    return build_current_user_response(current_user)
