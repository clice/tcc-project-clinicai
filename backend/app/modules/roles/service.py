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
from app.modules.roles.schema import RoleCreate, RoleUpdate
from app.modules.audit_logs.service import create_audit_log


def check_role_duplicate(
    db: Session,
    name: str,
    ignore_role_id: int | None = None,
) -> None:
    """
    Verifica se já existe outro role com o mesmo name.
    """
    query = db.query(Role).filter(Role.name == name)

    if ignore_role_id is not None:
        query = query.filter(Role.id != ignore_role_id)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="Já existe um perfil com esse nome.",
        )


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


def create_role(
    db: Session,
    payload: RoleCreate,
    current_user: User,
) -> Role:
    """
    Cria um novo role e registra log de auditoria.
    """
    name = payload.name.value

    check_role_duplicate(db=db, name=name)

    role = Role(
        name=name,
        display_name=payload.display_name,
        description=payload.description,
    )

    db.add(role)
    db.flush()

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.CREATE,
        entity=AuditEntity.ROLE,
        entity_id=role.id,
        description="Perfil de acesso cadastrado.",
        new_data={
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
        },
    )

    db.commit()
    db.refresh(role)

    return role


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

    new_name = update_data.get("name", role.name)

    check_role_duplicate(
        db=db,
        name=new_name,
        ignore_role_id=role_id,
    )

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
