"""
Seed do módulo de audit logs.

Cria logs iniciais para desenvolvimento e testes.
"""

from sqlalchemy.orm import Session

from app.modules.audit_logs.model import AuditLog


def get_or_create_audit_log(
    db: Session,
    *,
    action: str,
    entity: str,
    entity_id: int | None,
) -> AuditLog:
    """
    Evita duplicidade básica no seed.
    """

    log = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == action,
            AuditLog.entity == entity,
            AuditLog.entity_id == entity_id,
        )
        .first()
    )

    if log:
        return log

    log = AuditLog(
        action=action,
        entity=entity,
        entity_id=entity_id,
        description="Log inicial de seed.",
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


def seed_audit_logs(db: Session):
    """
    Cria logs inicais do sistema.
    """

    return {
        "log_login": get_or_create_audit_log(
            db=db,
            action="LOGIN_SUCCESS",
            entity="auth",
            entity_id=None,
        ),
        "log_patient_create": get_or_create_audit_log(
            db=db,
            action="CREATE_PATIENT",
            entity="patients",
            entity_id=1,
        ),
        "log_exam_create": get_or_create_audit_log(
            db=db,
            action="CREATE_EXAM",
            entity="exams",
            entity_id=1,
        ),
        "log_exam_cancel": get_or_create_audit_log(
            db=db,
            action="CANCEL_EXAM",
            entity="exams",
            entity_id=1,
        ),
    }