"""
Utilitários comuns para services.

Este arquivo concentra funções pequenas e reutilizáveis
para evitar repetição nos módulos do sistema.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Query

from app.common.constants import RoleName
from app.modules.users.model import User


def enum_to_value(value: Any) -> Any:
    """
    Converte Enum para seu valor primitivo.
    """
    if isinstance(value, Enum):
        return value.value

    return value


def normalize_update_data(data: dict) -> dict:
    """
    Normaliza dados vindos de schemas antes de aplicar update.
    """
    return {
        key: enum_to_value(value)
        for key, value in data.items()
    }


def model_dump_update(payload: Any) -> dict:
    """
    Extrai apenas campos enviados no payload.
    """
    return payload.model_dump(exclude_unset=True)


def apply_update_data(instance: Any, update_data: dict) -> None:
    """
    Aplica os dados de update em um model SQLAlchemy.
    """
    for field, value in update_data.items():
        setattr(instance, field, value)


def serialize_for_json(data: dict) -> dict:
    """
    Converte dados para formatos seguros em JSON.
    Útil para audit logs.
    """
    serialized = {}

    for key, value in data.items():
        value = enum_to_value(value)

        if isinstance(value, (date, datetime)):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value

    return serialized


def get_user_role_name(user: User) -> str | None:
    """
    Retorna o nome da role do usuário autenticado.
    """
    return user.role.name if user.role else None
    

def is_admin_master(user: User) -> bool:
    """
    Verifica se o usuário autenticado é admin_master.
    """
    return get_user_role_name(user) == RoleName.ADMIN_MASTER.value


def ensure_user_has_clinic(user: User) -> int:
    """
    Garante que o usuário está vinculado a uma clínica.
    """
    if user.clinic_id is None:
        raise HTTPException(
            status_code=403,
            detail="Usuário não está vinculado a uma clínica.",
        )

    return user.clinic_id


def get_or_404(query: Query, detail: str):
    """
    Executa query.first() e retorna 404 se não encontrar.
    """
    result = query.first()

    if not result:
        raise HTTPException(status_code=404, detail=detail)

    return result


def check_duplicate_or_400(query: Query, detail: str) -> None:
    """
    Retorna erro 400 se a query encontrar registro duplicado.
    """
    if query.first():
        raise HTTPException(status_code=400, detail=detail)