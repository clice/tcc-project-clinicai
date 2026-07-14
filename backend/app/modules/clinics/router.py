"""
Rotas do módulo de clínicas.

Este arquivo expõe os endpoints relacionados ao cadastro e gerenciamento
das clínicas do sistema.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, require_permission
from app.modules.clinics.schema import (
    ClinicCreate,
    ClinicResponse,
    ClinicUpdate,
)
from app.modules.clinics.service import (
    activate_clinic,
    build_clinic_response,
    create_clinic,
    ensure_user_can_access_clinic,
    get_clinic_by_id,
    inactivate_clinic,
    list_clinics,
    update_clinic,
)


router = APIRouter(prefix="/clinics", tags=["Clinics"])


@router.post("/", response_model=ClinicResponse, status_code=201)
def create_clinic_route(
    payload: ClinicCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Cria uma nova clínica.
    """
    return create_clinic(
        db=db,
        payload=payload,
        current_user=current_user,
    )


@router.get("/", response_model=list[ClinicResponse])
def list_clinics_route(
    search: str | None = Query(default=None),
    include_inactive: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Lista clínicas cadastradas.
    """
    return list_clinics(
        db=db,
        current_user=current_user,
        search=search,
        include_inactive=include_inactive,
    )


# As rotas estáticas precisam ser registradas antes de /{clinic_id}.
# Caso contrário, o Starlette considera "/clinics/me" compatível com a rota
# dinâmica e o FastAPI tenta converter "me" para inteiro, devolvendo 422 antes
# de alcançar o endpoint de autoatendimento.
@router.get("/me", response_model=ClinicResponse)
def get_my_clinic(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("clinics:read_profile")),
):
    """
    Busca os dados da clínica vinculada ao usuário autenticado.
    """
    return get_clinic_by_id(db, current_user.clinic_id)


@router.patch("/me", response_model=ClinicResponse)
def update_my_clinic(
    payload: ClinicUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("clinics:update_profile")),
):
    """
    Atualiza parcialmente os dados da clínica vinculada ao usuário.
    """
    return update_clinic(
        db=db,
        clinic_id=current_user.clinic_id,
        payload=payload,
        current_user=current_user,
    )


@router.get("/{clinic_id}", response_model=ClinicResponse)
def get_clinic_route(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Busca uma clínica específica pelo ID.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)

    ensure_user_can_access_clinic(
        current_user=current_user,
        clinic_id=clinic.id,
    )

    return build_clinic_response(clinic)


@router.patch("/{clinic_id}", response_model=ClinicResponse)
def update_clinic_route(
    clinic_id: int,
    payload: ClinicUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Atualiza parcialmente uma clínica.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)

    ensure_user_can_access_clinic(
        current_user=current_user,
        clinic_id=clinic.id,
    )

    return update_clinic(
        db=db,
        clinic_id=clinic_id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/{clinic_id}/inactivate", response_model=ClinicResponse)
def inactivate_clinic_route(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Inativa uma clínica.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)

    ensure_user_can_access_clinic(
        current_user=current_user,
        clinic_id=clinic.id,
    )

    return inactivate_clinic(
        db=db,
        clinic_id=clinic_id,
        current_user=current_user,
    )


@router.patch("/{clinic_id}/activate", response_model=ClinicResponse)
def activate_clinic_route(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Ativa uma clínica.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)

    ensure_user_can_access_clinic(
        current_user=current_user,
        clinic_id=clinic.id,
    )

    return activate_clinic(
        db=db,
        clinic_id=clinic_id,
        current_user=current_user,
    )
