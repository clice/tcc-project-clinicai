"""Testes de regressão do catálogo fechado definido na RBAC-06."""

import re
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.permissions.catalog import (
    OFFICIAL_PERMISSION_DEFINITIONS,
    OFFICIAL_PERMISSION_NAMES,
)
from app.modules.permissions.model import Permission
from app.modules.permissions.router import router
from app.modules.permissions.schema import PermissionUpdate
from app.modules.permissions.seed import seed_permissions


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=[Permission.__table__])
    return Session(engine)


def test_api_does_not_expose_permission_creation() -> None:
    methods = {
        method
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }

    assert "POST" not in methods
    assert methods == {"GET", "PATCH"}


def test_update_accepts_only_presentation_fields() -> None:
    assert set(PermissionUpdate.model_fields) == {"display_name", "description"}


def test_empty_database_receives_the_complete_official_catalog() -> None:
    db = make_session()

    permissions = seed_permissions(db)

    assert set(permissions) == OFFICIAL_PERMISSION_NAMES
    assert db.query(Permission).count() == len(OFFICIAL_PERMISSION_NAMES)


def test_startup_does_not_recreate_permission_missing_from_existing_database() -> None:
    db = make_session()
    seed_permissions(db)
    removed_name = next(iter(OFFICIAL_PERMISSION_NAMES))
    db.query(Permission).filter(Permission.name == removed_name).delete()
    db.commit()

    with pytest.raises(RuntimeError, match="migration"):
        seed_permissions(db)

    assert db.query(Permission).filter(Permission.name == removed_name).first() is None


def test_catalog_has_unique_names_and_valid_module_prefixes() -> None:
    names = [definition.name for definition in OFFICIAL_PERMISSION_DEFINITIONS]

    assert len(names) == len(set(names))
    assert all(
        definition.name.startswith(f"{definition.module.value}:")
        for definition in OFFICIAL_PERMISSION_DEFINITIONS
    )


def test_every_backend_permission_check_exists_in_the_official_catalog() -> None:
    modules_directory = Path(__file__).parents[1] / "app" / "modules"
    references: set[str] = set()

    for router_file in modules_directory.glob("*/router.py"):
        source = router_file.read_text(encoding="utf-8")
        references.update(re.findall(r'require_permission\("([a-z_]+:[a-z_]+)"\)', source))

    assert references
    assert references <= OFFICIAL_PERMISSION_NAMES
