"""
Centraliza funções relacionadas à segurança da aplicação.

Este arquivo contém geração de hash de senha, verificação de senha,
criação de tokens JWT e decodificação de tokens JWT.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# Contexto usado para criar e verificar hashes de senha.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Gera o hash seguro de uma senha antes de salvá-la no banco.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto puro corresponde ao hash salvo no banco.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Cria um access token JWT com prazo de expiração curto.
    """
    to_encode = data.copy()

    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "type": "access",
    })

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Cria um refresh token JWT com prazo de expiração maior.
    """
    to_encode = data.copy()

    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.refresh_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "type": "refresh",
    })

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_token(token: str) -> dict | None:
    """
    Decodifica um token JWT genérico.
    """
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        return None


def decode_access_token(token: str) -> dict | None:
    """
    Decodifica e valida apenas access tokens.
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != "access":
        return None

    return payload


def decode_refresh_token(token: str) -> dict | None:
    """
    Decodifica e valida apenas refresh tokens.
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != "refresh":
        return None

    return payload
