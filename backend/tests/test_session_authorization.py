"""Testes de usuário ativo e versionamento de sessão JWT."""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token
from app.modules.auth.service import logout_user, refresh_user_tokens
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


def add_user_catalog(db: Session) -> tuple[User, Status]:
    role = Role(
        name="doctor",
        display_name="Médico",
        permissions_initialized=True,
    )
    active = Status(name="active", display_name="Ativo", applies_to="user")
    inactive = Status(name="inactive", display_name="Inativo", applies_to="user")
    user = User(
        name="Médico de Teste",
        email="medico.teste@clinicai.local",
        cpf="12345678901",
        password_hash="hash-nao-utilizado",
        token_version=0,
        role=role,
        status=active,
    )
    db.add_all([role, active, inactive, user])
    db.commit()
    return user, inactive


def token_data(user: User) -> dict[str, str | int]:
    return {"sub": str(user.id), "token_version": user.token_version}


def test_active_user_with_current_token_is_authenticated(db_session: Session) -> None:
    user, _ = add_user_catalog(db_session)
    access_token = create_access_token(token_data(user))

    authenticated = get_current_user(token=access_token, db=db_session)

    assert authenticated.id == user.id


def test_inactive_user_is_forbidden_even_with_valid_token(db_session: Session) -> None:
    user, inactive = add_user_catalog(db_session)
    access_token = create_access_token(token_data(user))
    user.status_id = inactive.id
    db_session.commit()
    db_session.expire_all()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=access_token, db=db_session)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Usuário inativo ou bloqueado."


def test_logout_invalidates_old_access_and_refresh_tokens(db_session: Session) -> None:
    user, _ = add_user_catalog(db_session)
    access_token = create_access_token(token_data(user))
    refresh_token = create_refresh_token(token_data(user))

    logout_user(db_session, user=user)
    db_session.expire_all()

    with pytest.raises(HTTPException) as access_error:
        get_current_user(token=access_token, db=db_session)
    assert access_error.value.status_code == 401
    assert access_error.value.detail == "Sessão expirada. Faça login novamente."

    with pytest.raises(HTTPException) as refresh_error:
        refresh_user_tokens(db_session, refresh_token)
    assert refresh_error.value.status_code == 401
    assert refresh_error.value.detail == "Sessão expirada. Faça login novamente."
