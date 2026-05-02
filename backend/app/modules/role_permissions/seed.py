"""
Seed do módulo de role_permissions.

Este arquivo cria os vínculos iniciais entre perfis de acesso
e permissões do sistema.
"""

from sqlalchemy.orm import Session

from app.modules.permissions.model import Permission
from app.modules.roles.model import Role
from app.modules.role_permissions.model import RolePermission


def get_or_create_role_permission(
    db: Session,
    role_id: int,
    permission_id: int,
) -> RolePermission:
    """
    Busca um vínculo existente ou cria um novo.

    Evita duplicidade durante a execução dos seeds.
    """
    role_permission = (
        db.query(RolePermission)
        .filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
        .first()
    )

    if role_permission:
        return role_permission

    role_permission = RolePermission(
        role_id=role_id,
        permission_id=permission_id,
    )

    db.add(role_permission)
    db.commit()
    db.refresh(role_permission)

    return role_permission


def apply_permissions_to_role(
    db: Session,
    role: Role,
    permissions: dict[str, Permission],
    permission_names: list[str],
) -> None:
    """
    Vincula uma lista de permissões a uma role.

    Caso alguma permissão ainda não exista no seed de permissions,
    ela é ignorada para evitar quebra durante o desenvolvimento.
    """
    for permission_name in permission_names:
        permission = permissions.get(permission_name)

        if not permission:
            continue

        get_or_create_role_permission(
            db=db,
            role_id=role.id,
            permission_id=permission.id,
        )


def seed_role_permissions(
    db: Session,
    roles: dict[str, Role],
    permissions: dict[str, Permission],
) -> None:
    """
    Cria os vínculos iniciais entre roles e permissions.
    """

    admin_master_permissions = list(permissions.keys())

    doctor_permissions = [
        "users:read",
        "users:update",
        
        "clinics:read",
        "clinics:update",
        
        "patients:create",
        "patients:read",
        "patients:update",
        "patients:change_status",

        "exams:create",
        "exams:read",
        "exams:update",
        "exams:delete",
        "exams:upload_file",
        "exams:download_file",

        "ai_analysis:create",
        "ai_analysis:read",
        "ai_analysis:update",
        "ai_analysis:review",
    ]

    clinic_staff_permissions = [
        "users:read",
        "users:update",
        
        "clinics:read",
        "clinics:update",
        
        "patients:create",
        "patients:read",
        "patients:update",
        "patients:change_status",
        
        "exams:read",
        "exams:download_file",
        
        "ai_analysis:read",
    ]

    role_permission_map = {
        "admin_master": admin_master_permissions,
        "doctor": doctor_permissions,
        "clinic_staff": clinic_staff_permissions,
    }

    for role_name, permission_names in role_permission_map.items():
        role = roles.get(role_name)

        if not role:
            continue

        apply_permissions_to_role(
            db=db,
            role=role,
            permissions=permissions,
            permission_names=permission_names,
        )
