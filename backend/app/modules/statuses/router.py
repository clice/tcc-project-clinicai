"""
Rotas do módulo de statuses.

Este arquivo expõe os endpoints da API relacionados aos status do sistema.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.statuses.schema import (
    StatusCreate,
    StatusResponse,
    StatusUpdate,
)
from app.modules.statuses.service import (
    create_status,
    get_status_by_id,
    list_statuses,
    update_status,
)


router = APIRouter(prefix="/statuses", tags=["Statuses"])


@router.get("/{status_id}", response_model=StatusResponse)
def get_status_route(
    status_id: int,
    db: Session = Depends(get_db),
):
    """
    Busca um status específico pelo ID.
    """
    return get_status_by_id(db=db, status_id=status_id)


@router.get("/", response_model=list[StatusResponse])
def list_statuses_route(
    applies_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Lista todos os status cadastrados.
    """
    return list_statuses(db=db, applies_to=applies_to)


@router.post("/", response_model=StatusResponse, status_code=201)
def create_status_route(
    payload: StatusCreate,
    db: Session = Depends(get_db),
):
    """
    Cria um novo status.
    Apenas administradores devem poder criar status do sistema.
    """
    return create_status(db=db, payload=payload)


@router.patch("/{status_id}", response_model=StatusResponse)
def update_status_route(
    status_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Atualiza parcialmente um status existente.
    Como usa PATCH, o frontend pode enviar somente os campos alterados.
    """
    return update_status(db=db, status_id=status_id, payload=payload)