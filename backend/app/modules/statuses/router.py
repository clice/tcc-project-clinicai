"""
Rotas do módulo de statuses.

Este arquivo expõe os endpoints da API relacionados aos status do sistema.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.modules.statuses.schema import StatusResponse, StatusUpdate
from app.modules.statuses.service import (
    get_status_by_id,
    list_statuses,
    update_status,
)


router = APIRouter(prefix="/statuses", tags=["Statuses"])


@router.get("/", response_model=list[StatusResponse])
def list_statuses_route(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Lista todos os status cadastrados.
    """
    return list_statuses(db=db)


@router.get("/{status_id}", response_model=StatusResponse)
def get_status_route(
    status_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Busca um status específico pelo ID.
    """
    return get_status_by_id(db=db, status_id=status_id)


@router.patch("/{status_id}", response_model=StatusResponse)
def update_status_route(
    status_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Atualiza parcialmente um status existente.
    Como usa PATCH, o frontend pode enviar somente os campos alterados.
    """
    return update_status(db=db, status_id=status_id, payload=payload, current_user=current_user)
