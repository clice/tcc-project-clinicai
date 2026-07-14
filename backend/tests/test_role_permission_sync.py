"""Testes transacionais da sincronização da matriz de permissões."""

from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.role_permissions.service import sync_role_permissions
from app.modules.roles.model import Role


def add_role_with_permissions(
    db: Session,
) -> tuple[Role, Permission, Permission]:
    role = Role(
        name="doctor",
        display_name="Médico",
        permissions_initialized=True,
    )
    permission_to_remove = Permission(
        name="patients:read",
        display_name="Visualizar pacientes",
        module="patients",
    )
    permission_to_add = Permission(
        name="exams:read",
        display_name="Visualizar exames",
        module="exams",
    )
    sentinel_role = Role(
        name="clinic_staff",
        display_name="Funcionário da clínica",
        permissions_initialized=True,
    )
    db.add_all([role, sentinel_role, permission_to_remove, permission_to_add])
    db.flush()
    db.add_all(
        [
            RolePermission(
                role_id=role.id,
                permission_id=permission_to_remove.id,
            ),
            # Mantém o contador de chave primária acima do vínculo removido.
            # No PostgreSQL isso já ocorre pela sequence; no SQLite em memória
            # evita reutilização artificial do ID durante o mesmo flush.
            RolePermission(
                id=100,
                role_id=sentinel_role.id,
                permission_id=permission_to_remove.id,
            ),
        ]
    )
    db.commit()
    return role, permission_to_remove, permission_to_add


def permission_ids(db: Session, role_id: int) -> set[int]:
    return {
        permission_id
        for (permission_id,) in (
            db.query(RolePermission.permission_id)
            .filter(RolePermission.role_id == role_id)
            .all()
        )
    }


def test_sync_grants_and_revokes_in_one_final_matrix(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    role, removed, added = add_role_with_permissions(db_session)
    monkeypatch.setattr(
        "app.modules.role_permissions.service.create_audit_log",
        lambda **kwargs: None,
    )

    sync_role_permissions(
        db_session,
        role_id=role.id,
        permission_ids=[added.id],
        current_user=SimpleNamespace(id=999, clinic_id=None),
    )

    assert permission_ids(db_session, role.id) == {added.id}
    assert removed.id not in permission_ids(db_session, role.id)


def test_sync_rolls_back_every_change_when_a_step_fails(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    role, original, added = add_role_with_permissions(db_session)

    def fail_audit(**kwargs) -> None:
        raise RuntimeError("falha simulada após alterar os vínculos")

    monkeypatch.setattr(
        "app.modules.role_permissions.service.create_audit_log",
        fail_audit,
    )

    with pytest.raises(RuntimeError, match="falha simulada"):
        sync_role_permissions(
            db_session,
            role_id=role.id,
            permission_ids=[added.id],
            current_user=SimpleNamespace(id=999, clinic_id=None),
        )

    db_session.expire_all()
    assert permission_ids(db_session, role.id) == {original.id}
