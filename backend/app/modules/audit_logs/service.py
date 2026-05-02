"""
Service do módulo de audit logs.

Contém as regras de negócio relacionadas aos logs de auditoria.
"""

from sqlalchemy.orm import Session

from app.modules.audit_logs.model import AuditLog


def create_audit_log(
    db: Session,
    *,
    user_id: int | None,
    clinic_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    description: str | None = None,
    old_data: dict | None = None,
    new_data: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """
    Cria um novo log de auditoria.
    """

    audit_log = AuditLog(
        user_id=user_id,
        clinic_id=clinic_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        description=description,
        old_data=old_data,
        new_data=new_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def list_audit_logs(
    db: Session,
    *,
    clinic_id: int | None = None,
    user_id: int | None = None,
    entity: str | None = None,
    action: str | None = None,
) -> list[AuditLog]:
    """
    Lista logs de auditoria com filtros opcionais.
    """

    query = db.query(AuditLog)

    if clinic_id:
        query = query.filter(AuditLog.clinic_id == clinic_id)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if entity:
        query = query.filter(AuditLog.entity == entity)

    if action:
        query = query.filter(AuditLog.action == action)

    return query.order_by(AuditLog.created_at.desc()).all()