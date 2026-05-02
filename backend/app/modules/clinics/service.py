"""
Service do módulo de clínicas.

Este arquivo concentra as regras de negócio da tabela clinics.
O router deve apenas receber a requisição e chamar estas funções.
"""

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.modules.clinics.model import Clinic
from app.modules.clinics.schema import ClinicCreate, ClinicUpdate
from app.modules.statuses.model import Status
from app.modules.statuses.service import (
    get_status_by_id_and_applies_to,
    get_status_by_name_and_applies_to,
)


def check_clinic_duplicate(
    db: Session,
    cnpj: str | None = None,
    email: str | None = None,
    ignore_clinic_id: int | None = None,
) -> None:
    """
    Verifica duplicidade de CNPJ e e-mail.

    No update, ignora a própria clínica.
    """
    filters = []

    if cnpj:
        filters.append(Clinic.cnpj == cnpj)

    if email:
        filters.append(Clinic.email == email)

    if not filters:
        return

    query = db.query(Clinic).filter(or_(*filters))

    if ignore_clinic_id is not None:
        query = query.filter(Clinic.id != ignore_clinic_id)

    duplicated = query.first()

    if not duplicated:
        return

    if cnpj and duplicated.cnpj == cnpj:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")

    if email and duplicated.email == email:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")


def build_clinic_response(clinic: Clinic) -> dict:
    """
    Monta a resposta incluindo dados do status relacionado.
    """
    return {
        "id": clinic.id,
        "name": clinic.name,
        "cnpj": clinic.cnpj,
        "email": clinic.email,
        "phone": clinic.phone,
        "mobile_phone": clinic.mobile_phone,
        "zip_code": clinic.zip_code,
        "address": clinic.address,
        "number": clinic.number,
        "complement": clinic.complement,
        "neighborhood": clinic.neighborhood,
        "city": clinic.city,
        "state": clinic.state,
        "status_id": clinic.status_id,
        "status_name": clinic.status.name if clinic.status else None,
        "status_display_name": clinic.status.display_name if clinic.status else None,
        "created_at": clinic.created_at,
        "updated_at": clinic.updated_at,
    }


def get_clinic_by_id(db: Session, clinic_id: int) -> Clinic:
    """
    Busca uma clínica pelo ID.

    Se não existir, retorna erro 404.
    """
    clinic = (
        db.query(Clinic)
        .options(joinedload(Clinic.status))
        .filter(Clinic.id == clinic_id)
        .first()
    )

    if not clinic:
        raise HTTPException(status_code=404, detail="Clínica não encontrada.")

    return clinic


def list_clinics(
    db: Session,
    search: str | None = None,
    include_inactive: bool = True,
) -> list[dict]:
    """
    Lista clínicas cadastradas.

    Permite busca por razão social, nome fantasia, CNPJ ou cidade.
    """
    query = db.query(Clinic).options(joinedload(Clinic.status))

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Clinic.name.ilike(term),
                Clinic.cnpj.ilike(term),
                Clinic.city.ilike(term),
            )
        )

    if not include_inactive:
        query = query.join(Status).filter(Status.name == "active")

    clinics = query.order_by(Clinic.name.asc()).all()

    return [build_clinic_response(clinic) for clinic in clinics]


def create_clinic(db: Session, payload: ClinicCreate) -> dict:
    """
    Cria uma nova clínica.
    """
    get_status_by_id_and_applies_to(
        db=db,
        status_id=payload.status_id,
        applies_to="clinic",
    )

    check_clinic_duplicate(
        db=db,
        cnpj=payload.cnpj,
        email=str(payload.email) if payload.email else None,
    )

    clinic = Clinic(**payload.model_dump())

    db.add(clinic)
    db.commit()
    db.refresh(clinic)

    clinic = get_clinic_by_id(db=db, clinic_id=clinic.id)

    return build_clinic_response(clinic)


def update_clinic(
    db: Session,
    clinic_id: int,
    payload: ClinicUpdate,
) -> dict:
    """
    Atualiza parcialmente uma clínica existente.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return build_clinic_response(clinic)

    if "status_id" in update_data:
        get_status_by_id_and_applies_to(
            db=db,
            status_id=update_data["status_id"],
            applies_to="clinic",
        )

    check_clinic_duplicate(
        db=db,
        cnpj=update_data.get("cnpj"),
        email=str(update_data.get("email")) if update_data.get("email") else None,
        ignore_clinic_id=clinic_id,
    )

    for field, value in update_data.items():
        setattr(clinic, field, value)

    db.commit()
    db.refresh(clinic)

    clinic = get_clinic_by_id(db=db, clinic_id=clinic.id)

    return build_clinic_response(clinic)


def inactivate_clinic(db: Session, clinic_id: int) -> dict:
    """
    Inativa uma clínica.

    Não remove fisicamente o registro para preservar histórico e relações.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)
    inactivate_status = get_status_by_name_and_applies_to(
        db=db,
        name="inactive",
        applies_to="clinic",
    )

    clinic.status_id = inactivate_status.id

    db.commit()
    db.refresh(clinic)

    clinic = get_clinic_by_id(db=db, clinic_id=clinic.id)

    return build_clinic_response(clinic)


def activate_clinic(db: Session, clinic_id: int) -> dict:
    """
    Ativa clínica por status.
    """
    clinic = get_clinic_by_id(db, clinic_id)
    active_status = get_status_by_name_and_applies_to(
        db=db,
        name="active",
        applies_to="clinic",
    )

    clinic.status_id = active_status.id

    db.commit()
    db.refresh(clinic)

    clinic = get_clinic_by_id(db=db, clinic_id=clinic.id)

    return build_clinic_response(clinic)