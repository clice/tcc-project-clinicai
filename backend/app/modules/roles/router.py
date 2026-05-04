"""
Rotas do módulo de roles.

Este arquivo expõe os endpoints da API relacionados aos perfis de acesso do sistema.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.modules.roles.schema import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.modules.roles.service import (
    create_role,
    get_role_by_id,
    list_roles,
    update_role,
)


router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("/", response_model=RoleResponse, status_code=201)
def create_role_route(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Cria um novo perfil de acesso.
    Apenas administradores devem poder criar perfis do sistema.
    """
    return create_role(db=db, payload=payload, current_user=current_user)


@router.get("/", response_model=list[RoleResponse])
def list_roles_route(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Lista todos os perfis cadastrados.
    """
    return list_roles(db=db)


@router.get("/{role_id}", response_model=RoleResponse)
def get_role_route(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Busca um perfil específico pelo ID.
    """
    return get_role_by_id(db=db, role_id=role_id)


@router.patch("/{role_id}", response_model=RoleResponse)
def update_role_route(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Atualiza parcialmente um perfil existente.
    Como usa PATCH, o frontend pode enviar somente os campos alterados.
    """
    return update_role(db=db, role_id=role_id, payload=payload, current_user=current_user)
