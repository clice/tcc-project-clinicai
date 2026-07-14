"""A matriz do Administrador Master deve ser fixa no frontend e no backend."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.role_permissions.schema import RolePermissionCreate, RolePermissionUpdate
from app.modules.role_permissions.service import (
    create_role_permission,
    delete_role_permission,
    sync_role_permissions,
    update_role_permission,
)
from app.modules.roles.model import Role


def add_admin_matrix(db: Session) -> tuple[Role, Permission, Permission, RolePermission]:
    admin = Role(
        name="admin_master",
        display_name="Administrador Master",
        permissions_initialized=True,
    )
    permission_a = Permission(
        name="users:read",
        display_name="Visualizar usuários",
        module="users",
    )
    permission_b = Permission(
        name="clinics:read",
        display_name="Visualizar clínicas",
        module="clinics",
    )
    db.add_all([admin, permission_a, permission_b])
    db.flush()

    link = RolePermission(role_id=admin.id, permission_id=permission_a.id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return admin, permission_a, permission_b, link


def assert_fixed_matrix_error(exc_info) -> None:
    assert exc_info.value.status_code == 403
    assert "Administrador Master" in exc_info.value.detail


def test_admin_master_matrix_rejects_create_update_delete_and_sync(
    db_session: Session,
) -> None:
    admin, _, permission_b, link = add_admin_matrix(db_session)
    current_user = SimpleNamespace(id=999, clinic_id=None)

    with pytest.raises(HTTPException) as create_error:
        create_role_permission(
            db_session,
            RolePermissionCreate(role_id=admin.id, permission_id=permission_b.id),
            current_user,
        )
    assert_fixed_matrix_error(create_error)

    with pytest.raises(HTTPException) as update_error:
        update_role_permission(
            db_session,
            link.id,
            RolePermissionUpdate(permission_id=permission_b.id),
            current_user,
        )
    assert_fixed_matrix_error(update_error)

    with pytest.raises(HTTPException) as delete_error:
        delete_role_permission(db_session, link.id, current_user)
    assert_fixed_matrix_error(delete_error)

    with pytest.raises(HTTPException) as sync_error:
        sync_role_permissions(
            db_session,
            role_id=admin.id,
            permission_ids=[permission_b.id],
            current_user=current_user,
        )
    assert_fixed_matrix_error(sync_error)
