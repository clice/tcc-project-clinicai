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


_SENSITIVE_AUDIT_KEYS = {
    "password",
    "password_hash",
    "current_password",
    "access_token",
    "refresh_token",
    "authorization",
    "secret_key",
}


def sanitize_audit_data(value):
    """Remove credenciais conhecidas antes de persistir dados de auditoria."""

    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            normalized_key = str(key).strip().lower()
            if normalized_key in _SENSITIVE_AUDIT_KEYS:
                continue
            sanitized[key] = sanitize_audit_data(item)
        return sanitized

    if isinstance(value, list):
        return [sanitize_audit_data(item) for item in value]

    if isinstance(value, tuple):
        return [sanitize_audit_data(item) for item in value]

    return value


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
        old_data=sanitize_audit_data(old_data),
        new_data=sanitize_audit_data(new_data),
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(audit_log)

    if commit:
        db.commit()
        db.refresh(audit_log)

    return audit_log


def _query_audit_logs(
    db: Session,
    *,
    clinic_id: int | None = None,
    user_id: int | None = None,
    entity: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Executa a consulta comum depois que o chamador validou o acesso."""

    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    query = (
        db.query(AuditLog)
        .options(
            joinedload(AuditLog.user),
            joinedload(AuditLog.clinic),
        )
    )

    if clinic_id is not None:
        query = query.filter(AuditLog.clinic_id == clinic_id)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if entity is not None:
        query = query.filter(AuditLog.entity == entity)

    if entity_id is not None:
        query = query.filter(AuditLog.entity_id == entity_id)

    if action is not None:
        query = query.filter(AuditLog.action == action)

    total = query.count()

    logs = (
        query.order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return {
        "items": [build_audit_log_response(log) for log in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def list_audit_logs(
    db: Session,
    *,
    current_user: User,
    clinic_id: int | None = None,
    user_id: int | None = None,
    entity: str | None = None,
    action: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista global de auditoria, exclusiva do Administrador Master."""

    if not is_admin_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Apenas administrador master pode visualizar logs de auditoria.",
        )

    return _query_audit_logs(
        db,
        clinic_id=clinic_id,
        user_id=user_id,
        entity=entity,
        action=action,
        limit=limit,
        offset=offset,
    )


def list_entity_audit_logs(
    db: Session,
    *,
    entity: str,
    entity_id: int,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista o histórico de uma entidade após validação de escopo externa.

    Esta função não substitui a rota administrativa de auditoria. Ela existe
    para recursos como o histórico de um exame (RF36), cuja autorização é
    validada pelo próprio módulo antes da consulta.
    """

    return _query_audit_logs(
        db,
        entity=entity,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
