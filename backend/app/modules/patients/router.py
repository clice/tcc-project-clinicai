"""
Rotas do módulo de pacientes.

Este arquivo expõe os endpoints da API relacionados aos pacientes.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.modules.patients.schema import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from app.modules.patients.service import (
    activate_patient,
    create_patient,
    get_patient,
    inactivate_patient,
    list_patients,
    update_patient,
)
from app.modules.users.model import User


router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("/", response_model=PatientResponse, status_code=201)
def create_patient_route(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patients:create")),
):
    """
    Cria um novo paciente.

    Usuários com permissão patients:create podem cadastrar pacientes.
    """
    return create_patient(
        db=db,
        payload=payload,
        current_user=current_user,
    )


@router.get("/", response_model=list[PatientResponse])
def list_patients_route(
    include_inactive: bool = Query(default=False),
    search: str | None = Query(default=None),
    clinic_id: int | None = Query(default=None),
    doctor_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patients:read")),
):
    """
    Lista pacientes cadastrados com filtros que não ampliam o escopo.

    Administrador vê todos; funcionário vê a própria clínica; médico vê
    somente os pacientes sob sua responsabilidade.
    """
    return list_patients(
        db=db,
        include_inactive=include_inactive,
        search=search,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        current_user=current_user,
    )


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient_route(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("patients:read")),
):
    """
    Busca um paciente específico pelo ID.
    """
    return get_patient(
        db=db,
        patient_id=patient_id,
        current_user=current_user,
    )


@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient_route(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("patients:update")),
):
    """
    Atualiza parcialmente um paciente existente.
    """
    return update_patient(
        db=db,
        patient_id=patient_id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/{patient_id}/activate", response_model=PatientResponse)
def activate_patient_route(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patients:change_status")),
):
    """
    Ativa um paciente inativo.
    """
    return activate_patient(
        db=db,
        patient_id=patient_id,
        current_user=current_user,
    )


@router.patch("/{patient_id}/inactivate", response_model=PatientResponse)
def inactivate_patient_route(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patients:change_status")),
):
    """
    Inativa um paciente.

    Essa ação substitui a exclusão física do registro.
    """
    return inactivate_patient(
        db=db,
        patient_id=patient_id,
        current_user=current_user,
    )
