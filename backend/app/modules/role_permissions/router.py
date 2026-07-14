"""
Rotas do módulo de role_permissions.

Este arquivo expõe os endpoints relacionados aos vínculos
entre perfis de acesso e permissões.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.modules.role_permissions.schema import (
    RolePermissionCreate,
    RolePermissionResponse,
    RolePermissionSyncRequest,
    RolePermissionUpdate,
)
from app.modules.role_permissions.service import (
    build_role_permission_response,
    create_role_permission,
    delete_role_permission,
    get_role_permission_by_id,
    list_role_permissions,
    sync_role_permissions,
    update_role_permission,
)


router = APIRouter(prefix="/role-permissions", tags=["Role Permissions"])


@router.post("/", response_model=RolePermissionResponse, status_code=201)
def create_role_permission_route(
    payload: RolePermissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Cria um vínculo entre perfil de acesso e permissão.
    Apenas administradores devem poder alterar permissões do sistema.
    """
    role_permission = create_role_permission(db=db, payload=payload, current_user=current_user)
    return build_role_permission_response(role_permission)


@router.get("/", response_model=list[RolePermissionResponse])
def list_role_permissions_route(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Lista todos os vínculos entre roles e permissions.
    """
    return [build_role_permission_response(rp) for rp in list_role_permissions(db=db)]


@router.get("/{role_permission_id}", response_model=RolePermissionResponse)
def get_role_permission_route(
    role_permission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Busca um vínculo específico pelo ID.
    """
    role_permission = get_role_permission_by_id(
        db=db,
        role_permission_id=role_permission_id,
    )
    return build_role_permission_response(role_permission)


@router.patch("/{role_permission_id}", response_model=RolePermissionResponse)
def update_role_permission_route(
    role_permission_id: int,
    payload: RolePermissionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Atualiza parcialmente um vínculo existente.
    """
    role_permission = update_role_permission(
        db=db,
        role_permission_id=role_permission_id,
        payload=payload,
        current_user=current_user,
    )
    return build_role_permission_response(role_permission)


@router.delete("/{role_permission_id}")
def delete_role_permission_route(
    role_permission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Remove um vínculo entre perfil e permissão.
    """
    return delete_role_permission(
        db=db,
        role_permission_id=role_permission_id,
        current_user=current_user,
    )


@router.put("/roles/{role_id}", response_model=list[RolePermissionResponse])
def sync_role_permissions_route(
    role_id: int,
    payload: RolePermissionSyncRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Sincroniza, de forma transacional, todas as permissões de uma role.

    Substitui o padrão anterior do frontend (vários POST/DELETE via
    Promise.all, sem transação) — se qualquer parte falhar aqui, nada é
    aplicado (rollback integral), e nunca existe uma janela intermediária
    em que a role tem mais permissões do que deveria.
    """
    role_permissions = sync_role_permissions(
        db=db,
        role_id=role_id,
        permission_ids=payload.permission_ids,
        current_user=current_user,
    )
    return [build_role_permission_response(rp) for rp in role_permissions]
