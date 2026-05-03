"""
Rotas do módulo de audit logs.

Logs são apenas consultados pela API.
A criação deve acontecer automaticamente pelos services do sistema.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.modules.audit_logs.schema import AuditLogResponse
from app.modules.audit_logs.service import list_audit_logs
from app.modules.users.model import User


router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs_route(
    clinic_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    entity: str | None = Query(default=None),
    action: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit_logs:read")),
):
    """
    Lista logs de auditoria.

    Apenas usuários com permissão audit_logs:read devem acessar.
    No sistema, essa permissão deve ficar somente com admin_master.
    """
    return list_audit_logs(
        db=db,
        current_user=current_user,
        clinic_id=clinic_id,
        user_id=user_id,
        entity=entity,
        action=action,
    )
