"""
Rotas do módulo de audit logs.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.audit_logs.schema import AuditLogResponse
from app.modules.audit_logs.service import list_audit_logs


router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs_route(
    clinic_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    entity: str | None = Query(default=None),
    action: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Lista logs de auditoria.
    Permite filtro por clínica, usuário, entidade e ação.
    """
    return list_audit_logs(
        db=db,
        clinic_id=clinic_id,
        user_id=user_id,
        entity=entity,
        action=action,
    )