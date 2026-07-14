"""
Service do módulo de roles.

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
from app.modules.roles.model import Role
from app.modules.users.model import User
from app.modules.roles.schema import RoleUpdate
from app.modules.audit_logs.service import create_audit_log


# ========================================
# MAIN METHODS
# ========================================


def get_role_by_id(db: Session, role_id: int) -> Role:
    """
    Busca um role pelo ID.
    """
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(status_code=404, detail="Perfil de acesso não encontrado.")

    return role


def list_roles(db: Session) -> list[Role]:
    """
    Lista todos os roles cadastrados.
    """
    return db.query(Role).order_by(Role.display_name.asc()).all()


def update_role(
    db: Session,
    role_id: int,
    payload: RoleUpdate,
    current_user: User,
) -> Role:
    """
    Atualiza parcialmente um role e registra log de auditoria.
    """
    role = get_role_by_id(db, role_id)

    update_data = model_dump_update(payload)
    update_data = normalize_update_data(update_data)

    if not update_data:
        return role

    old_data = {
        "name": role.name,
        "display_name": role.display_name,
        "description": role.description,
    }

    apply_update_data(role, update_data)

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.ROLE,
        entity_id=role.id,
        description="Perfil de acesso atualizado.",
        old_data=old_data,
        new_data=update_data,
    )

    db.commit()
    db.refresh(role)

    return role
