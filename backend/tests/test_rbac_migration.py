"""Teste da migration de dados que encerra a RBAC-01."""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def load_migration():
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "b7c1d4e2f901_remove_legacy_clinic_staff_permissions.py"
    )
    spec = importlib.util.spec_from_file_location("rbac_01_migration", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_marks_existing_roles_and_removes_only_legacy_links() -> None:
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    roles = sa.Table(
        "roles",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
    )
    permissions = sa.Table(
        "permissions",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
    )
    role_permissions = sa.Table(
        "role_permissions",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("role_id", sa.Integer, nullable=False),
        sa.Column("permission_id", sa.Integer, nullable=False),
    )
    metadata.create_all(engine)
    migration = load_migration()

    with engine.begin() as connection:
        connection.execute(
            roles.insert(),
            [
                {"id": 1, "name": "clinic_staff"},
                {"id": 2, "name": "doctor"},
                {"id": 3, "name": "empty_role"},
            ],
        )
        connection.execute(
            permissions.insert(),
            [
                {"id": 1, "name": "exams:read"},
                {"id": 2, "name": "ai_analysis:read"},
                {"id": 3, "name": "patients:read"},
            ],
        )
        connection.execute(
            role_permissions.insert(),
            [
                {"id": 1, "role_id": 1, "permission_id": 1},
                {"id": 2, "role_id": 1, "permission_id": 2},
                {"id": 3, "role_id": 1, "permission_id": 3},
                {"id": 4, "role_id": 2, "permission_id": 1},
            ],
        )
        migration.op = Operations(MigrationContext.configure(connection))

        migration.upgrade()

        columns = {
            column["name"] for column in sa.inspect(connection).get_columns("roles")
        }
        assert "permissions_initialized" in columns
        flags = connection.execute(
            sa.text("SELECT permissions_initialized FROM roles ORDER BY id")
        ).scalars().all()
        assert flags == [1, 1, 1]
        links = set(
            connection.execute(
                sa.text("SELECT role_id, permission_id FROM role_permissions")
            ).all()
        )
        assert links == {(1, 3), (2, 1)}

        migration.downgrade()

        columns = {
            column["name"] for column in sa.inspect(connection).get_columns("roles")
        }
        assert "permissions_initialized" not in columns
        links = set(
            connection.execute(
                sa.text("SELECT role_id, permission_id FROM role_permissions")
            ).all()
        )
        assert links == {(1, 1), (1, 2), (1, 3), (2, 1)}
