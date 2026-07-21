"""Testes de regressão da separação entre bootstrap e reconciliação RBAC."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.modules import models  # noqa: F401 - registra todos os mappers
from app.core.database import Base
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.role_permissions.seed import (
    ADMIN_MASTER_RESTRICTED_PERMISSIONS,
    reconcile_role_permissions,
    seed_role_permissions,
)
from app.modules.roles.model import Role


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[Role.__table__, Permission.__table__, RolePermission.__table__],
    )
    return Session(engine)


def add_catalog(db: Session) -> tuple[dict[str, Role], dict[str, Permission]]:
    roles = {
        name: Role(name=name, display_name=name)
        for name in ("admin_master", "doctor", "clinic_manager")
    }
    permission_names = {
        "users:create",
        "users:read",
        "users:update",
        "users:change_status",
        "users:read_profile",
        "users:update_profile",
        "clinics:read_profile",
        "clinics:update_profile",
        "patients:create",
        "patients:read",
        "patients:update",
        "patients:change_status",
        "exams:create",
        "exams:list",
        "exams:read",
        "exams:update",
        "exams:upload",
        "exams:download",
        "exams:change_status",
        "exams:review",
        "ai_analysis:create",
        "ai_analysis:read",
        "ai_analysis:update",
    }
    permissions = {
        name: Permission(
            name=name,
            display_name=name,
            module=name.split(":", 1)[0],
        )
        for name in permission_names
    }
    db.add_all([*roles.values(), *permissions.values()])
    db.commit()
    return roles, permissions


def permission_names_for(db: Session, role: Role) -> set[str]:
    return {
        name
        for (name,) in (
            db.query(Permission.name)
            .join(RolePermission)
            .filter(RolePermission.role_id == role.id)
            .all()
        )
    }


def test_restart_preserves_admin_customization() -> None:
    db = make_session()
    roles, permissions = add_catalog(db)

    assert set(seed_role_permissions(db, roles, permissions)) == {
        "admin_master",
        "doctor",
        "clinic_manager",
    }

    doctor = roles["doctor"]
    removed_permission = permissions["exams:download"]
    db.query(RolePermission).filter_by(
        role_id=doctor.id,
        permission_id=removed_permission.id,
    ).delete()
    db.commit()

    # Simula nova execução do entrypoint após edição feita pelo administrador.
    assert seed_role_permissions(db, roles, permissions) == []
    assert "exams:download" not in permission_names_for(db, doctor)


def test_restart_preserves_simultaneous_grant_and_revocation() -> None:
    """Cobre a matriz personalizada completa após nova execução do startup."""

    db = make_session()
    roles, permissions = add_catalog(db)
    seed_role_permissions(db, roles, permissions)
    clinic_manager = roles["clinic_manager"]
    revoked = permissions["patients:update"]
    granted = permissions["exams:read"]
    db.query(RolePermission).filter_by(
        role_id=clinic_manager.id,
        permission_id=revoked.id,
    ).delete()
    db.add(
        RolePermission(
            role_id=clinic_manager.id,
            permission_id=granted.id,
        )
    )
    db.commit()

    # Simula uma nova inicialização do backend.
    assert seed_role_permissions(db, roles, permissions) == []
    persisted = permission_names_for(db, clinic_manager)

    assert "patients:update" not in persisted
    assert "exams:read" in persisted


def test_bootstrap_fills_only_unconfigured_role() -> None:
    db = make_session()
    roles, permissions = add_catalog(db)
    doctor = roles["doctor"]
    db.add(
        RolePermission(
            role_id=doctor.id,
            permission_id=permissions["users:read_profile"].id,
        )
    )
    doctor.permissions_initialized = True
    db.commit()

    bootstrapped = seed_role_permissions(db, roles, permissions)

    assert "doctor" not in bootstrapped
    assert permission_names_for(db, doctor) == {"users:read_profile"}
    assert "clinic_manager" in bootstrapped


def test_restart_preserves_intentionally_empty_role() -> None:
    db = make_session()
    roles, permissions = add_catalog(db)
    seed_role_permissions(db, roles, permissions)
    clinic_manager = roles["clinic_manager"]
    db.query(RolePermission).filter_by(role_id=clinic_manager.id).delete()
    db.commit()

    assert seed_role_permissions(db, roles, permissions) == []
    assert permission_names_for(db, clinic_manager) == set()


def test_explicit_reconciliation_restores_default_matrix() -> None:
    db = make_session()
    roles, permissions = add_catalog(db)
    seed_role_permissions(db, roles, permissions)
    doctor = roles["doctor"]
    removed_permission = permissions["exams:download"]
    db.query(RolePermission).filter_by(
        role_id=doctor.id,
        permission_id=removed_permission.id,
    ).delete()
    db.commit()

    results = reconcile_role_permissions(db, roles, permissions)

    doctor_result = next(result for result in results if result.role_name == "doctor")
    assert doctor_result.added == 1
    assert doctor_result.removed == 0
    assert "exams:download" in permission_names_for(db, doctor)

def test_admin_master_keeps_exam_list_without_clinical_permissions() -> None:
    db = make_session()
    roles, permissions = add_catalog(db)

    seed_role_permissions(db, roles, permissions)

    admin_permissions = permission_names_for(db, roles["admin_master"])

    assert "exams:list" in admin_permissions
    assert ADMIN_MASTER_RESTRICTED_PERMISSIONS.isdisjoint(admin_permissions)

    reconcile_role_permissions(db, roles, permissions)

    reconciled_permissions = permission_names_for(db, roles["admin_master"])
    assert "exams:list" in reconciled_permissions
    assert ADMIN_MASTER_RESTRICTED_PERMISSIONS.isdisjoint(reconciled_permissions)
