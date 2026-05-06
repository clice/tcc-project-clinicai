"""
Service do módulo de role_permissions.

Aqui ficam as regras de negócio relacionadas aos vínculos
entre perfis de acesso e permissões.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.common.constants import AuditAction, AuditEntity
from app.common.services import (
    apply_update_data,
    model_dump_update,
)
from app.modules.permissions.model import Permission
from app.modules.roles.model import Role
from app.modules.role_permissions.model import RolePermission
from app.modules.users.model import User
from app.modules.role_permissions.schema import (
    RolePermissionCreate,
    RolePermissionUpdate,
)
from app.modules.audit_logs.service import create_audit_log


def validate_role_exists(db: Session, role_id: int) -> Role:
    """
    Valida se a role informada existe.
    """
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Perfil de acesso não encontrado.",
        )

    return role


def validate_permission_exists(db: Session, permission_id: int) -> Permission:
    """
    Valida se a permission informada existe.
    """
    permission = (
        db.query(Permission)
        .filter(Permission.id == permission_id)
        .first()
    )

    if not permission:
        raise HTTPException(
            status_code=404,
            detail="Permissão não encontrada.",
        )

    return permission


def check_role_permission_duplicate(
    db: Session,
    role_id: int,
    permission_id: int,
    ignore_role_permission_id: int | None = None,
) -> None:
    """
    Verifica se já existe o mesmo vínculo entre role e permission.
    """
    query = db.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id,
    )

    if ignore_role_permission_id is not None:
        query = query.filter(RolePermission.id != ignore_role_permission_id)

    duplicated = query.first()

    if duplicated:
        raise HTTPException(
            status_code=400,
            detail="Essa permissão já está vinculada a esse perfil.",
        )


# ========================================
# MAIN METHODS
# ========================================


def get_role_permission_by_id(
    db: Session,
    role_permission_id: int,
) -> RolePermission:
    """
    Busca um vínculo pelo ID.

    Se não existir, retorna erro 404.
    """
    role_permission = (
        db.query(RolePermission)
        .options(
            joinedload(RolePermission.role),
            joinedload(RolePermission.permission),
        )
        .filter(RolePermission.id == role_permission_id)
        .first()
    )

    if not role_permission:
        raise HTTPException(
            status_code=404,
            detail="Vínculo entre perfil e permissão não encontrado.",
        )

    return role_permission


def list_role_permissions(db: Session) -> list[RolePermission]:
    """
    Lista todos os vínculos cadastrados.
    """
    return (
        db.query(RolePermission)
        .options(
            joinedload(RolePermission.role),
            joinedload(RolePermission.permission),
        )
        .order_by(RolePermission.role_id.asc(), RolePermission.permission_id.asc())
        .all()
    )


def create_role_permission(
    db: Session,
    payload: RolePermissionCreate,
    current_user: User,
) -> RolePermission:
    """
    Cria um novo vínculo entre role e permission.
    """
    role = validate_role_exists(db=db, role_id=payload.role_id)
    permission = validate_permission_exists(db=db, permission_id=payload.permission_id)

    check_role_permission_duplicate(
        db=db,
        role_id=payload.role_id,
        permission_id=payload.permission_id,
    )

    role_permission = RolePermission(
        role_id=payload.role_id,
        permission_id=payload.permission_id,
    )

    db.add(role_permission)
    db.flush()

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.CREATE,
        entity=AuditEntity.ROLE_PERMISSION,
        entity_id=role_permission.id,
        description="Permissão vinculada ao perfil de acesso.",
        new_data={
            "id": role_permission.id,
            "role_id": role_permission.role_id,
            "role_name": role.name,
            "permission_id": role_permission.permission_id,
            "permission_name": permission.name,
        },
    )

    db.commit()
    db.refresh(role_permission)

    return role_permission


def update_role_permission(
    db: Session,
    role_permission_id: int,
    payload: RolePermissionUpdate,
    current_user: User,
) -> RolePermission:
    """
    Atualiza parcialmente um vínculo existente.
    """
    role_permission = get_role_permission_by_id(
        db=db,
        role_permission_id=role_permission_id,
    )

    update_data = model_dump_update(payload)

    if not update_data:
        return role_permission

    old_data = {
        "role_id": role_permission.role_id,
        "role_name": role_permission.role.name if role_permission.role else None,
        "permission_id": role_permission.permission_id,
        "permission_name": role_permission.permission.name if role_permission.permission else None,
    }

    new_role_id = update_data.get("role_id", role_permission.role_id)
    new_permission_id = update_data.get(
        "permission_id",
        role_permission.permission_id,
    )

    role = validate_role_exists(db=db, role_id=new_role_id)
    permission = validate_permission_exists(db=db, permission_id=new_permission_id)

    check_role_permission_duplicate(
        db=db,
        role_id=new_role_id,
        permission_id=new_permission_id,
        ignore_role_permission_id=role_permission_id,
    )

    apply_update_data(role_permission, update_data)

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.ROLE_PERMISSION,
        entity_id=role_permission.id,
        description="Vínculo entre perfil e permissão atualizado.",
        old_data=old_data,
        new_data={
            "role_id": new_role_id,
            "role_name": role.name,
            "permission_id": new_permission_id,
            "permission_name": permission.name,
        },
    )

    db.commit()
    db.refresh(role_permission)

    return role_permission


def delete_role_permission(
    db: Session,
    role_permission_id: int,
    current_user: User,
) -> dict[str, str]:
    """
    Remove um vínculo entre role e permission.
    """
    role_permission = get_role_permission_by_id(
        db=db,
        role_permission_id=role_permission_id,
    )

    old_data = {
        "id": role_permission.id,
        "role_id": role_permission.role_id,
        "role_name": role_permission.role.name if role_permission.role else None,
        "permission_id": role_permission.permission_id,
        "permission_name": role_permission.permission.name if role_permission.permission else None,
    }

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.DELETE,
        entity=AuditEntity.ROLE_PERMISSION,
        entity_id=role_permission.id,
        description="Vínculo entre perfil e permissão removido.",
        old_data=old_data,
    )

    db.delete(role_permission)
    db.commit()

    return {"detail": "Vínculo removido com sucesso."}
