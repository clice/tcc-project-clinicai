"""
Service do módulo de audit logs.

Contém as regras de negócio relacionadas aos logs de auditoria.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.common.constants import AuditAction, AuditEntity
from app.common.services import enum_to_value, is_admin_master
from app.modules.audit_logs.model import AuditLog
from app.modules.users.model import User


def build_audit_log_response(audit_log: AuditLog) -> dict:
    """
    Monta resposta enriquecida do log.
    """
    return {
        "id": audit_log.id,
        "user_id": audit_log.user_id,
        "user_name": audit_log.user.name if audit_log.user else None,
        "clinic_id": audit_log.clinic_id,
        "clinic_name": audit_log.clinic.name if audit_log.clinic else None,
        "action": audit_log.action,
        "entity": audit_log.entity,
        "entity_id": audit_log.entity_id,
        "description": audit_log.description,
        "old_data": audit_log.old_data,
        "new_data": audit_log.new_data,
        "ip_address": audit_log.ip_address,
        "user_agent": audit_log.user_agent,
        "created_at": audit_log.created_at,
    }

# ========================================
# MAIN METHODS
# ========================================


def create_audit_log(
    db: Session,
    *,
    user_id: int | None,
    clinic_id: int | None,
    action: AuditAction | str,
    entity: AuditEntity | str,
    entity_id: int | None = None,
    description: str | None = None,
    old_data: dict | None = None,
    new_data: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    commit: bool = False,
) -> AuditLog:
    """
    Cria um novo log de auditoria.

    Por padrão, não faz commit separado.
    Assim, o log participa da mesma transação do service que chamou.
    """
    audit_log = AuditLog(
        user_id=user_id,
        clinic_id=clinic_id,
        action=enum_to_value(action),
        entity=enum_to_value(entity),
        entity_id=entity_id,
        description=description,
        old_data=old_data,
        new_data=new_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(audit_log)

    if commit:
        db.commit()
        db.refresh(audit_log)

    return audit_log


def list_audit_logs(
    db: Session,
    *,
    current_user: User,
    clinic_id: int | None = None,
    user_id: int | None = None,
    entity: str | None = None,
    action: str | None = None,
) -> list[dict]:
    """
    Lista logs de auditoria com filtros opcionais.

    Regra:
    - admin_master visualiza todos;
    - outros usuários não devem visualizar logs.
    """
    if not is_admin_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Apenas administrador master pode visualizar logs de auditoria.",
        )

    query = (
        db.query(AuditLog)
        .options(
            joinedload(AuditLog.user),
            joinedload(AuditLog.clinic),
        )
    )

    if clinic_id:
        query = query.filter(AuditLog.clinic_id == clinic_id)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if entity:
        query = query.filter(AuditLog.entity == entity)

    if action:
        query = query.filter(AuditLog.action == action)

    logs = query.order_by(AuditLog.created_at.desc()).all()

    return [build_audit_log_response(log) for log in logs]
