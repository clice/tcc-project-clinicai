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
