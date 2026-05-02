"""
Service do módulo de statuses.

Responsável pelas regras de negócio do módulo.
O acesso direto ao banco fica concentrado no repository.py.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.statuses.model import Status
from app.modules.statuses.repository import (
    create_status as repository_create_status,
    exists_status,
    get_status_by_id as repository_get_status_by_id,
    get_status_by_name_and_applies_to as repository_get_status_by_name_and_applies_to,
    list_statuses as repository_list_statuses,
    save_status,
)
from app.modules.statuses.schema import StatusCreate, StatusUpdate


# ========================================
# UTILITARIAS
# ========================================

def get_status_by_id(db: Session, status_id: int) -> Status:
    """
    Busca um status pelo ID.
    Lança erro 404 caso não exista.
    """
    status = repository_get_status_by_id(db=db, status_id=status_id)

    if not status:
        raise HTTPException(status_code=404, detail="Status não encontrado.")

    return status


def get_status_by_id_and_applies_to(
    db: Session,
    status_id: int,
    applies_to: str,
) -> Status:
    """
    Busca um status pelo ID e valida se pertence ao contexto esperado.

    Exemplo:
    - user
    - clinic
    - patient
    - exam
    """
    status = get_status_by_id(db=db, status_id=status_id)

    if status.applies_to != applies_to:
        raise HTTPException(
            status_code=400,
            detail=f"Status inválido para {applies_to}.",
        )

    return status


def get_status_by_name_and_applies_to(
    db: Session,
    name: str,
    applies_to: str,
) -> Status:
    """
    Busca um status pelo nome interno e contexto.

    Útil para outros módulos recuperarem status padrão.
    """
    status = repository_get_status_by_name_and_applies_to(
        db=db,
        name=name,
        applies_to=applies_to,
    )

    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Status '{name}' para '{applies_to}' não encontrado.",
        )

    return status


def check_status_duplicate(
    db: Session,
    name: str,
    applies_to: str,
    ignore_status_id: int | None = None,
) -> None:
    """
    Verifica duplicidade de status por nome e contexto.

    Usado na criação e atualização.
    """
    if exists_status(
        db=db,
        name=name,
        applies_to=applies_to,
        ignore_status_id=ignore_status_id,
    ):
        raise HTTPException(
            status_code=400,
            detail="Já existe um status com esse nome para essa referência.",
        )


# ========================================
# MÓDULOS
# ========================================

def list_statuses(
    db: Session,
    applies_to: str | None = None,
) -> list[Status]:
    """
    Lista os status cadastrados.
    Pode filtrar por contexto, como user, clinic, patient ou exam.
    """
    return repository_list_statuses(db=db, applies_to=applies_to)


def create_status(db: Session, payload: StatusCreate) -> Status:
    """
    Cria um novo status após validar duplicidade.
    """
    check_status_duplicate(
        db=db,
        name=payload.name,
        applies_to=payload.applies_to,
    )

    status = Status(
        name=payload.name,
        display_name=payload.display_name,
        applies_to=payload.applies_to,
        description=payload.description,
    )

    return repository_create_status(db=db, status=status)


def update_status(
    db: Session,
    status_id: int,
    payload: StatusUpdate,
) -> Status:
    """
    Atualiza parcialmente um status existente.

    Como é PATCH, somente os campos enviados são alterados.
    """
    status = get_status_by_id(db=db, status_id=status_id)
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return status

    new_name = update_data.get("name", status.name)
    new_applies_to = update_data.get("applies_to", status.applies_to)

    check_status_duplicate(
        db=db,
        name=new_name,
        applies_to=new_applies_to,
        ignore_status_id=status_id,
    )

    for field, value in update_data.items():
        setattr(status, field, value)

    return save_status(db=db, status=status)