"""
Rotas do módulo de permissions.

Este arquivo expõe os endpoints da API relacionados às permissões do sistema.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.modules.permissions.schema import (
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
)
from app.modules.permissions.service import (
    create_permission,
    get_permission_by_id,
    list_permissions,
    update_permission,
)


router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post("/", response_model=PermissionResponse, status_code=201)
def create_permission_route(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Cria uma nova permissão do sistema.
    Apenas administradores devem poder criar permissões.
    """
    return create_permission(db=db, payload=payload, current_user=current_user)


@router.get("/", response_model=list[PermissionResponse])
def list_permissions_route(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Lista todas as permissões cadastradas.
    """
    return list_permissions(db=db)


@router.get("/{permission_id}", response_model=PermissionResponse)
def get_permission_route(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Busca uma permissão específica pelo ID.
    """
    return get_permission_by_id(db=db, permission_id=permission_id)


@router.patch("/{permission_id}", response_model=PermissionResponse)
def update_permission_route(
    permission_id: int,
    payload: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Atualiza parcialmente uma permissão existente.
    Como usa PATCH, o frontend pode enviar somente os campos alterados.
    """
    return update_permission(
        db=db,
        permission_id=permission_id,
        payload=payload,
        current_user=current_user,
    )
