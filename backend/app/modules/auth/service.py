"""Regras de negócio de autenticação e gerenciamento de sessão."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.common.constants import AuditAction, AuditEntity
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from app.modules.audit_logs.service import create_audit_log
from app.modules.auth.policies import validate_active_session_context
from app.modules.clinics.model import Clinic
from app.modules.users.model import User

# Hash isca executado quando o e-mail não existe. Assim, os caminhos
# "usuário inexistente" e "senha incorreta" também realizam bcrypt e não
# expõem facilmente a existência da conta por diferença grosseira de tempo.
_DUMMY_PASSWORD_HASH = get_password_hash("senha-isca-nao-usada-para-login-real")


def _query_user_for_session(db: Session, user_id: int) -> User | None:
    """Carrega os relacionamentos usados pelas políticas de sessão."""

    return (
        db.query(User)
        .options(
            joinedload(User.role),
            joinedload(User.status),
            joinedload(User.clinic).joinedload(Clinic.status),
        )
        .filter(User.id == user_id)
        .first()
    )


def _parse_token_user_id(raw_user_id: object, *, token_name: str) -> int:
    """Converte o ``sub`` do JWT sem transformar token malformado em erro 500."""

    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{token_name} inválido.",
        ) from None


def authenticate_user(
    db: Session,
    *,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> User:
    """Autentica e registra tentativas de login sem armazenar senhas ou tokens."""

    normalized_email = email.strip().lower()

    user = (
        db.query(User)
        .options(
            joinedload(User.role),
            joinedload(User.status),
            joinedload(User.clinic).joinedload(Clinic.status),
        )
        .filter(User.email == normalized_email)
        .first()
    )

    if user is None:
        verify_password(password, _DUMMY_PASSWORD_HASH)

        create_audit_log(
            db=db,
            user_id=None,
            clinic_id=None,
            action=AuditAction.LOGIN_FAILED,
            entity=AuditEntity.AUTH,
            entity_id=None,
            description="Tentativa de login com credenciais inválidas.",
            new_data={"email": normalized_email},
            ip_address=ip_address,
            user_agent=user_agent,
            commit=True,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    if not verify_password(password, user.password_hash):
        create_audit_log(
            db=db,
            user_id=user.id,
            clinic_id=user.clinic_id,
            action=AuditAction.LOGIN_FAILED,
            entity=AuditEntity.AUTH,
            entity_id=user.id,
            description="Tentativa de login com credenciais inválidas.",
            new_data={"email": normalized_email},
            ip_address=ip_address,
            user_agent=user_agent,
            commit=True,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    try:
        validate_active_session_context(user)
    except HTTPException:
        create_audit_log(
            db=db,
            user_id=user.id,
            clinic_id=user.clinic_id,
            action=AuditAction.LOGIN_FAILED,
            entity=AuditEntity.AUTH,
            entity_id=user.id,
            description="Tentativa de login em conta ou clínica inativa.",
            new_data={"email": normalized_email},
            ip_address=ip_address,
            user_agent=user_agent,
            commit=True,
        )
        raise

    user.last_access_at = datetime.now(timezone.utc)

    create_audit_log(
        db=db,
        user_id=user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.LOGIN_SUCCESS,
        entity=AuditEntity.AUTH,
        entity_id=user.id,
        description="Login realizado com sucesso.",
        new_data={
            "email": user.email,
            "last_access_at": user.last_access_at.isoformat(),
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.commit()
    db.refresh(user)

    return user


def validate_active_user(user: User) -> None:
    """Compatibilidade interna para chamadas antigas da política de sessão."""

    validate_active_session_context(user)


def create_user_tokens(user: User) -> dict[str, str]:
    """Cria um par de access/refresh token para a versão atual da sessão."""

    token_data = {
        "sub": str(user.id),
        "token_version": user.token_version,
    }

    return {
        "access_token": create_access_token(data=token_data),
        "refresh_token": create_refresh_token(data=token_data),
        "token_type": "bearer",
    }


def refresh_user_tokens(
    db: Session,
    refresh_token: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, str]:
    """Rotaciona o refresh token e invalida o par utilizado anteriormente."""

    payload = decode_refresh_token(refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado.",
        )

    user_id = payload.get("sub")
    token_version = payload.get("token_version")

    if user_id is None or token_version is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
        )

    parsed_user_id = _parse_token_user_id(user_id, token_name="Refresh token")
    user = _query_user_for_session(db, parsed_user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    if user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada. Faça login novamente.",
        )

    validate_active_session_context(user)

    # Rotação simples e adequada ao protótipo acadêmico: a versão é alterada
    # antes da emissão, de modo que o refresh token apresentado não possa ser
    # reutilizado. Também invalida o access token antigo.
    user.token_version += 1

    create_audit_log(
        db=db,
        user_id=user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.REFRESH_TOKEN,
        entity=AuditEntity.AUTH,
        entity_id=user.id,
        description="Tokens de sessão renovados.",
        new_data={"token_version": user.token_version},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.commit()
    db.refresh(user)

    return create_user_tokens(user)


def logout_user(
    db: Session,
    *,
    user: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, str]:
    """Encerra a sessão ao invalidar access e refresh tokens já emitidos."""

    user.token_version += 1

    create_audit_log(
        db=db,
        user_id=user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.LOGOUT,
        entity=AuditEntity.AUTH,
        entity_id=user.id,
        description="Logout realizado com sucesso.",
        new_data={"token_version": user.token_version},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.commit()

    return {"message": "Logout realizado com sucesso."}


def build_current_user_response(user: User) -> dict:
    """Monta a resposta pública de ``/auth/me`` sem campos de credencial."""

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
