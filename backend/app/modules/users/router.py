"""Rotas da API relacionadas aos usuários do ClinicAI."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, require_permission
from app.modules.auth.schema import TokenResponse
from app.modules.users.schema import (
    UserCreate,
    UserListResponse,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)
from app.modules.users.service import (
    activate_user,
    change_current_user_password,
    create_user,
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
    current_user=Depends(require_admin),
):
    """Cria um usuário; operação exclusiva do administrador master."""

    return create_user(db=db, payload=payload, current_user=current_user)


@router.get("/", response_model=list[UserListResponse])
def list_users_route(
    search: str | None = Query(default=None),
    clinic_id: int | None = Query(default=None),
    role: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Lista usuários com filtros administrativos."""

    return list_users(
        db=db,
        current_user=current_user,
        search=search,
        clinic_id=clinic_id,
        role=role,
        status=status,
    )


# Rotas estáticas devem vir antes de /{user_id}. Caso contrário, "me" e
# "doctors" podem ser interpretados como o parâmetro dinâmico e retornar 422.
@router.get("/doctors", response_model=list[UserListResponse])
def list_doctors_route(
    clinic_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("patients:read")),
):
    """Lista médicos ativos da clínica disponível ao formulário de pacientes."""

    return list_users(
        db=db,
        current_user=current_user,
        clinic_id=clinic_id,
        role="doctor",
        status="active",
    )


@router.get("/me", response_model=UserListResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:read_profile")),
):
    """Retorna apenas os campos públicos do usuário autenticado."""

    return get_user_response(
        db=db,
        user_id=current_user.id,
        current_user=current_user,
    )


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:update_profile")),
):
    """Atualiza os dados cadastrais permitidos do próprio usuário."""

    return update_user(
        db=db,
        user_id=current_user.id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/me/password", response_model=TokenResponse)
def update_my_password(
    payload: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("users:update_profile")),
):
    """Troca a própria senha e devolve tokens da nova versão da sessão."""

    return change_current_user_password(
        db=db,
        payload=payload,
        current_user=current_user,
    )


@router.get("/{user_id}", response_model=UserListResponse)
def get_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Busca um usuário específico por ID."""

    return get_user_response(db=db, user_id=user_id, current_user=current_user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_route(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Atualiza parcialmente um usuário administrado."""

    return update_user(db=db, user_id=user_id, payload=payload, current_user=current_user)


@router.patch("/{user_id}/password", response_model=UserResponse)
def update_user_password_route(
    user_id: int,
    payload: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Redefine a senha de outro usuário e encerra as sessões dele."""

    return update_user_password(
        db=db,
        user_id=user_id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/{user_id}/inactivate", response_model=UserResponse)
def inactivate_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Inativa um usuário sem remover seu histórico."""

    return inactivate_user(db=db, user_id=user_id, current_user=current_user)


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Ativa um usuário anteriormente inativo."""

    return activate_user(db=db, user_id=user_id, current_user=current_user)
