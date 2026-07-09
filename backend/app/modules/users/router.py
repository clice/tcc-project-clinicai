"""
Rotas do módulo de usuários.

Este arquivo expõe os endpoints da API relacionados aos usuários do sistema.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.modules.users.schema import (
    UserCreate,
    UserListResponse,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)
from app.modules.users.service import (
    activate_user,
    create_user,
    get_user_by_id,
    get_user_response,
    inactivate_user,
    list_users,
    update_user,
    update_user_password,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=201)
def create_user_route(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:create")),
):
    """
    Cria um novo usuário.
    Inicialmente, somente usuários com permissão users:create podem criar usuários.
    """
    return create_user(db=db, payload=payload, current_user=current_user)


@router.get("/", response_model=list[UserListResponse])
def list_users_route(
    search: str | None = Query(default=None),
    clinic_id: int | None = Query(default=None),
    role: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:read")),
):
    """
    Lista usuários.

    Permite:
    - busca por nome, e-mail ou CPF;
    - filtro por clínica;
    - filtro por perfil;
    - filtro por status.

    Usado também pelo módulo Patients para listar médicos ativos da clínica.
    """
    return list_users(
        db=db,
        current_user=current_user,
        search=search,
        clinic_id=clinic_id,
        role=role,
        status=status,
    )
    

@router.get("/doctors", response_model=list[UserListResponse])
def list_doctors_route(
    clinic_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("patients:read")),
):
    """
    Lista médicos ativos de uma clínica.
    Usado no formulário de pacientes.
    """
    return list_users(
        db=db,
        current_user=current_user,
        clinic_id=clinic_id,
        role="doctor",
        status="active",
    )


@router.get("/{user_id}", response_model=UserListResponse)
def get_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:read")),
):
    """
    Busca usuário específico pelo ID.
    """
    return get_user_response(db=db, user_id=user_id, current_user=current_user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_route(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:update")),
):
    """
    Atualiza parcialmente um usuário.
    Como usa PATCH, o frontend pode enviar somente os campos alterados.
    """
    return update_user(db=db, user_id=user_id, payload=payload, current_user=current_user)


@router.patch("/{user_id}/password", response_model=UserResponse)
def update_user_password_route(
    user_id: int,
    payload: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:update")),
):
    """
    Atualiza a senha de um usuário.
    Mantido separado do update geral por segurança.
    """
    return update_user_password(db=db, user_id=user_id, payload=payload, current_user=current_user)


@router.patch("/{user_id}/inactivate", response_model=UserResponse)
def inactivate_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:change_status")),
):
    """
    Inativa um usuário.
    Não remove fisicamente o registro do banco.
    """
    return inactivate_user(db=db, user_id=user_id, current_user=current_user)


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:change_status")),
):
    """
    Ativa um usuário inativo.
    """
    return activate_user(db=db, user_id=user_id, current_user=current_user)


@router.get("/me")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:read_profile")),
):
    """
    Busca dados de uma clínica para o perfil.
    """
    return get_user_by_id(db, current_user.id)


@router.patch("/me")
def update_my_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:update_profile")),
):
    """
    Atualiza parcialmente os dados do perfil do usuário.
    """
    return update_user(
        db=db,
        user_id=current_user.id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/me/password")
def update_my_password(
    payload: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:update_profile")),
):
    """
    Permite que o próprio usuário (doctor, clinic_staff, admin_master)
    troque sua senha, exigindo a senha atual.
    """
    return update_user_password(
        db=db,
        user_id=current_user.id,
        payload=payload,
        current_user=current_user,
    )