"""
Service do módulo de statuses.

Aqui ficam as regras de negócio e operações com o banco.
O router deve ficar mais limpo e apenas chamar essas funções.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.constants import AuditAction, AuditEntity
from app.common.services import (
    apply_update_data,
    model_dump_update,
    normalize_update_data,
)
from app.modules.statuses.model import Status
from app.modules.users.model import User
from app.modules.statuses.schema import StatusUpdate
from app.modules.audit_logs.service import create_audit_log


def get_status_by_id_and_applies_to(
    db: Session,
    status_id: int,
    applies_to: str,
) -> Status:
    """
    Busca um status pelo ID e valida se pertence ao contexto esperado.

    Exemplo:
    - status de user
    - status de clinic
    - status de patient
    """
    status = get_status_by_id(db=db, status_id=status_id)

    if status.applies_to != applies_to:
        raise HTTPException(
            status_code=400,
            detail=f"Status inválido para {applies_to}.",
        )

    return status


def get_status_by_name_and_applies_to(
    db: Session,
    name: str,
    applies_to: str,
) -> Status:
    """
    Busca um status pelo nome interno e contexto.
    """
    status = (
        db.query(Status)
        .filter(
            Status.name == name,
            Status.applies_to == applies_to,
        )
        .first()
    )

    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Status '{name}' para '{applies_to}' não encontrado.",
        )

    return status


# ========================================
# MAIN METHODS
# ========================================


def get_status_by_id(db: Session, status_id: int) -> Status:
    """
    Busca um status pelo ID.
    """
    status = db.query(Status).filter(Status.id == status_id).first()

    if not status:
        raise HTTPException(status_code=404, detail="Status não encontrado.")

    return status


def list_statuses(db: Session) -> list[Status]:
    """
    Lista todos os statuses cadastrados.
    """
    return (
        db.query(Status)
        .order_by(Status.applies_to.asc(), Status.display_name.asc())
        .all()
    )


def update_status(
    db: Session,
    status_id: int,
    payload: StatusUpdate,
    current_user: User,
) -> Status:
    """
    Atualiza parcialmente um status e registra log de auditoria.
    """
    status = get_status_by_id(db=db, status_id=status_id)
    
    update_data = model_dump_update(payload)
    update_data = normalize_update_data(update_data)

    if not update_data:
        return status

    old_data = {
        "name": status.name,
        "display_name": status.display_name,
        "applies_to": status.applies_to,
        "description": status.description,
    }

    apply_update_data(status, update_data)

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.STATUS,
        entity_id=status.id,
        description="Status atualizado.",
        old_data=old_data,
        new_data=update_data,
    )

    db.commit()
    db.refresh(status)

    return status
