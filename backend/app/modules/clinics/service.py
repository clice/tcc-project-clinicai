"""
Service do módulo de clínicas.

Este arquivo concentra as regras de negócio da tabela clinics.
O router deve apenas receber a requisição e chamar estas funções.
"""

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.common.access_control import ensure_user_can_access_clinic_data
from app.common.constants import AuditAction, AuditEntity, RoleName, StatusName, StatusScope
from app.common.services import (
    apply_update_data,
    model_dump_update,
)
from app.modules.clinics.model import Clinic
from app.modules.clinics.schema import ClinicCreate, ClinicUpdate
from app.modules.exams.model import Exam
from app.modules.patients.model import Patient
from app.modules.statuses.model import Status
from app.modules.audit_logs.service import create_audit_log
from app.modules.statuses.service import (
    get_status_by_name_and_applies_to,
)
from app.modules.users.model import User


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
        filters.append(func.lower(Clinic.email) == email.lower())

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

    if email and duplicated.email and duplicated.email.lower() == email.lower():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")


def ensure_user_can_access_clinic(current_user: User, clinic_id: int) -> None:
    """
    Garante que usuários comuns acessem apenas a própria clínica.
    """
    ensure_user_can_access_clinic_data(
        current_user=current_user,
        clinic_id=clinic_id,
        detail="Você não tem permissão para acessar esta clínica.",
    )


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


# ========================================
# MAIN METHODS
# ========================================


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
    current_user: User,
    search: str | None = None,
    include_inactive: bool = True,
) -> list[dict]:
    """
    Lista clínicas cadastradas.

    Regra:
    - admin_master visualiza todas;
    - usuários comuns visualizam apenas a própria clínica.
    """
    query = db.query(Clinic).options(joinedload(Clinic.status))

    role_name = current_user.role.name if current_user.role else None

    if role_name != RoleName.ADMIN_MASTER.value:
        if current_user.clinic_id is None:
            raise HTTPException(
                status_code=403,
                detail="Usuário não está vinculado a uma clínica.",
            )

        query = query.filter(Clinic.id == current_user.clinic_id)

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
        query = query.join(Status).filter(
            Status.name == StatusName.ACTIVE.value,
            Status.applies_to == StatusScope.CLINIC.value,
        )

    clinics = query.order_by(Clinic.name.asc()).all()

    return [build_clinic_response(clinic) for clinic in clinics]


def create_clinic(
    db: Session, 
    payload: ClinicCreate, 
    current_user: User
) -> dict:
    """
    Cria uma nova clínica.
    """
    active_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.ACTIVE.value,
        applies_to=StatusScope.CLINIC.value,
    )

    check_clinic_duplicate(
        db=db,
        cnpj=payload.cnpj,
        email=str(payload.email) if payload.email else None,
    )

    data = payload.model_dump()
    data["email"] = str(payload.email) if payload.email else None
    data["status_id"] = active_status.id

    clinic = Clinic(**data)

    db.add(clinic)
    db.flush()

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=clinic.id,
        action=AuditAction.CREATE,
        entity=AuditEntity.CLINIC,
        entity_id=clinic.id,
        description="Clínica cadastrada.",
        new_data={
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
        },
    )

    db.commit()
    db.refresh(clinic)

    clinic = get_clinic_by_id(db=db, clinic_id=clinic.id)

    return build_clinic_response(clinic)


def update_clinic(
    db: Session,
    clinic_id: int,
    payload: ClinicUpdate,
    current_user: User,
) -> dict:
    """
    Atualiza parcialmente uma clínica existente.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)

    update_data = model_dump_update(payload)

    if not update_data:
        return build_clinic_response(clinic)

    if "email" in update_data:
        update_data["email"] = str(update_data["email"]) if update_data["email"] else None

    check_clinic_duplicate(
        db=db,
        cnpj=update_data.get("cnpj"),
        email=update_data.get("email"),
        ignore_clinic_id=clinic_id,
    )

    old_data = {
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
    }
    
    apply_update_data(clinic, update_data)

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=clinic.id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.CLINIC,
        entity_id=clinic.id,
        description="Clínica atualizada.",
        old_data=old_data,
        new_data=update_data,
    )
    
    db.commit()
    db.refresh(clinic)

    clinic = get_clinic_by_id(db=db, clinic_id=clinic.id)

    return build_clinic_response(clinic)


def inactivate_clinic(db: Session, clinic_id: int, current_user: User) -> dict:
    """
    Inativa uma clínica.

    Não remove fisicamente o registro para preservar histórico e relações.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)

    inactive_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.INACTIVE.value,
        applies_to=StatusScope.CLINIC.value,
    )

    if clinic.status_id == inactive_status.id:
        return build_clinic_response(clinic)

    associated_users = db.query(User).filter(User.clinic_id == clinic.id).count()
    associated_patients = db.query(Patient).filter(Patient.clinic_id == clinic.id).count()
    associated_exams = db.query(Exam).filter(Exam.clinic_id == clinic.id).count()

    old_data = {
        "status_id": clinic.status_id,
        "status_name": clinic.status.name if clinic.status else None,
    }

    clinic.status_id = inactive_status.id

    # Uma clínica inativa não deve recuperar sessões antigas ao ser reativada.
    # Incrementar a versão encerra access/refresh tokens de todos os usuários
    # vinculados sem exigir lista de revogação, adequada ao protótipo acadêmico.
    invalidated_sessions = (
        db.query(User)
        .filter(User.clinic_id == clinic.id)
        .update(
            {User.token_version: User.token_version + 1},
            synchronize_session=False,
        )
    )

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=clinic.id,
        action=AuditAction.CHANGE_STATUS_INACTIVATE,
        entity=AuditEntity.CLINIC,
        entity_id=clinic.id,
        description="Clínica inativada.",
        old_data=old_data,
        new_data={
            "status_id": inactive_status.id,
            "status_name": StatusName.INACTIVE.value,
            "invalidated_user_sessions": invalidated_sessions,
            "associated_users": associated_users,
            "associated_patients": associated_patients,
            "associated_exams": associated_exams,
            "related_records_preserved": True,
        },
    )

    db.commit()
    db.refresh(clinic)

    clinic = get_clinic_by_id(db=db, clinic_id=clinic.id)

    return build_clinic_response(clinic)


def activate_clinic(db: Session, clinic_id: int, current_user: User) -> dict:
    """
    Ativa uma clínica.
    """
    clinic = get_clinic_by_id(db=db, clinic_id=clinic_id)

    active_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.ACTIVE.value,
        applies_to=StatusScope.CLINIC.value,
    )

    if clinic.status_id == active_status.id:
        return build_clinic_response(clinic)

    old_data = {
        "status_id": clinic.status_id,
        "status_name": clinic.status.name if clinic.status else None,
    }

    clinic.status_id = active_status.id

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=clinic.id,
        action=AuditAction.CHANGE_STATUS_ACTIVATE,
        entity=AuditEntity.CLINIC,
        entity_id=clinic.id,
        description="Clínica ativada.",
        old_data=old_data,
        new_data={
            "status_id": active_status.id,
            "status_name": StatusName.ACTIVE.value,
        },
    )

    db.commit()
    db.refresh(clinic)

    clinic = get_clinic_by_id(db=db, clinic_id=clinic.id)

    return build_clinic_response(clinic)
