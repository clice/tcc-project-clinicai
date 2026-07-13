"""
Service do módulo de permissions.

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
from app.modules.permissions.model import Permission
from app.modules.users.model import User
from app.modules.permissions.schema import PermissionUpdate
from app.modules.audit_logs.service import create_audit_log


# ========================================
# MAIN METHODS
# ========================================


def get_permission_by_id(db: Session, permission_id: int) -> Permission:
    """
    Busca uma permission pelo ID.
    Se não existir, retorna erro 404.
    """
    permission = (
        db.query(Permission)
        .filter(Permission.id == permission_id)
        .first()
    )

    if not permission:
        raise HTTPException(status_code=404, detail="Permissão não encontrada.")

    return permission


def list_permissions(db: Session) -> list[Permission]:
    """
    Lista todas as permissões cadastradas.
    """
    return (
        db.query(Permission)
        .order_by(Permission.module.asc(), Permission.display_name.asc())
        .all()
    )


def update_permission(
    db: Session,
    permission_id: int,
    payload: PermissionUpdate,
    current_user: User,
) -> Permission:
    """
    Atualiza parcialmente uma permissão.
    """
    permission = get_permission_by_id(db, permission_id)

    update_data = model_dump_update(payload)
    update_data = normalize_update_data(update_data)

    if not update_data:
        return permission

    old_data = {
        "name": permission.name,
        "display_name": permission.display_name,
        "description": permission.description,
        "module": permission.module,
    }

    apply_update_data(permission, update_data)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.PERMISSION,
        entity_id=permission.id,
        description="Permissão atualizada.",
        old_data=old_data,
        new_data=update_data,
    )

    db.commit()
    db.refresh(permission)

    return permission
