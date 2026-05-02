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
    create_clinic,
    get_clinic_by_id,
    build_clinic_response,
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
    Por segurança, apenas admin_master deve cadastrar clínicas.
    """
    return create_clinic(db=db, payload=payload)


@router.get("/", response_model=list[ClinicResponse])
def list_clinics_route(
    search: str | None = Query(default=None),
    include_inactive: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("clinics:read")),
):
    """
    Lista clínicas cadastradas.
    Permite busca por nome, CNPJ ou cidade.
    """
    return list_clinics(
        db=db,
        search=search,
        include_inactive=include_inactive,
    )


@router.get("/{clinic_id}", response_model=ClinicResponse)
def get_clinic_route(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("clinics:read")),
):
    """
    Busca uma clínica específica pelo ID.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)
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
    Como usa PATCH, o frontend pode enviar apenas os campos alterados.
    """
    return update_clinic(
        db=db,
        clinic_id=clinic_id,
        payload=payload,
    )


@router.patch("/{clinic_id}/inactivate", response_model=ClinicResponse)
def inactivate_clinic_route(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Inativa uma clínica.
    Esta rota substitui o DELETE físico para evitar perda de histórico.
    """
    return inactivate_clinic(db=db, clinic_id=clinic_id)


@router.patch("/{clinic_id}/activate", response_model=ClinicResponse)
def activate_clinic_route(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Ativa uma clínica inativa.
    """
    return activate_clinic(db=db, clinic_id=clinic_id)