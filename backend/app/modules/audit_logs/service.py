"""
Service do módulo de audit logs.

Contém as regras de negócio relacionadas aos logs de auditoria.
"""

import re
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.common.constants import AuditAction, AuditEntity
from app.common.request_context import get_request_audit_context
from app.common.services import enum_to_value, is_admin_master
from app.modules.audit_logs.model import AuditLog
from app.modules.users.model import User


_SENSITIVE_AUDIT_KEYS = {
    "password",
    "password_hash",
    "current_password",
    "new_password",
    "confirm_password",
    "password_confirmation",
    "access_token",
    "refresh_token",
    "id_token",
    "token",
    "authorization",
    "authorization_header",
    "cookie",
    "set_cookie",
    "secret",
    "secret_key",
    "api_key",
    "client_secret",
    "image",
    "image_data",
    "image_data_url",
    "image_bytes",
    "image_base64",
    "image_content",
    "file_bytes",
    "file_content",
    "binary_data",
    "binary_content",
    "gradcam_image",
    "gradcam_base64",
    "raw_response",
    "file_path",
    "gradcam_path",
}

_SENSITIVE_AUDIT_KEY_SUFFIXES = (
    "_password",
    "_password_hash",
    "_token",
    "_secret",
    "_api_key",
    "_base64",
    "_bytes",
)

_BEARER_TOKEN_PATTERN = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"
)
_CREDENTIAL_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(password|passwd|pwd|access[_-]?token|refresh[_-]?token|"
    r"id[_-]?token|api[_-]?key|client[_-]?secret|secret[_-]?key|"
    r"authorization)\b\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
)
_IMAGE_DATA_URI_PATTERN = re.compile(
    r"(?i)data:image/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]+"
)
_LONG_BASE64_PATTERN = re.compile(
    r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{256,}={0,2}(?![A-Za-z0-9+/])"
)


def _is_sensitive_audit_key(key: object) -> bool:
    normalized_key = str(key).strip().lower().replace("-", "_")
    if normalized_key in _SENSITIVE_AUDIT_KEYS:
        return True
    return normalized_key.endswith(_SENSITIVE_AUDIT_KEY_SUFFIXES)


def sanitize_audit_text(value: str) -> str:
    """Redige segredos e conteúdo binário que apareçam em texto livre."""

    sanitized = _IMAGE_DATA_URI_PATTERN.sub("[REDACTED_IMAGE_DATA]", value)
    sanitized = _BEARER_TOKEN_PATTERN.sub("Bearer [REDACTED]", sanitized)
    sanitized = _CREDENTIAL_ASSIGNMENT_PATTERN.sub(
        lambda match: f"{match.group(1)}=[REDACTED]",
        sanitized,
    )
    return _LONG_BASE64_PATTERN.sub("[REDACTED_BINARY_DATA]", sanitized)


def sanitize_audit_data(value):
    """Remove credenciais, caminhos e imagens antes de persistir auditoria."""

    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if _is_sensitive_audit_key(key):
                continue
            sanitized[key] = sanitize_audit_data(item)
        return sanitized

    if isinstance(value, list):
        return [sanitize_audit_data(item) for item in value]

    if isinstance(value, tuple):
        return [sanitize_audit_data(item) for item in value]

    if isinstance(value, str):
        return sanitize_audit_text(value)

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
    request_ip_address, request_user_agent = (
        get_request_audit_context()
    )

    if ip_address is None:
        ip_address = request_ip_address

    if user_agent is None:
        user_agent = request_user_agent

    audit_log = AuditLog(
        user_id=user_id,
        clinic_id=clinic_id,
        action=enum_to_value(action),
        entity=enum_to_value(entity),
        entity_id=entity_id,
        description=sanitize_audit_data(description),
        old_data=sanitize_audit_data(old_data),
        new_data=sanitize_audit_data(new_data),
        ip_address=ip_address,
        user_agent=sanitize_audit_data(user_agent),
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
    date_from: date | None = None,
    date_to: date | None = None,
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

    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=422,
            detail="A data inicial não pode ser posterior à data final.",
        )

    if date_from is not None:
        start_at = datetime.combine(
            date_from,
            time.min,
            tzinfo=timezone.utc,
        )
        query = query.filter(
            AuditLog.created_at >= start_at
        )

    if date_to is not None:
        end_exclusive = datetime.combine(
            date_to + timedelta(days=1),
            time.min,
            tzinfo=timezone.utc,
        )
        query = query.filter(
            AuditLog.created_at < end_exclusive
        )

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
    date_from: date | None = None,
    date_to: date | None = None,
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
        date_from=date_from,
        date_to=date_to,
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
