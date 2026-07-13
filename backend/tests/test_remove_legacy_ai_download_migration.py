"""Testes da migration que encerra a RBAC-07."""

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def load_migration():
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "c8d2e4f6a701_remove_legacy_ai_analysis_download.py"
    )
    spec = importlib.util.spec_from_file_location("rbac_07_migration", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_legacy_database(engine: sa.Engine) -> None:
    metadata = sa.MetaData()
    sa.Table(
        "roles",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
    )
    sa.Table(
        "permissions",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("display_name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("module", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    sa.Table(
        "role_permissions",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("role_id", sa.Integer, nullable=False),
        sa.Column("permission_id", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id"),
    )
    metadata.create_all(engine)


def test_upgrade_removes_legacy_permission_and_all_links_and_downgrade_restores_them(
) -> None:
    engine = sa.create_engine("sqlite://")
    create_legacy_database(engine)
    migration = load_migration()
    timestamp = datetime(2026, 7, 13, tzinfo=timezone.utc)

    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO roles (id, name) VALUES "
                "(1, 'admin_master'), (2, 'doctor'), (3, 'custom_role')"
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO permissions
                    (id, name, display_name, description, module, created_at, updated_at)
                VALUES
                    (10, 'ai_analysis:download', 'Baixar análise por IA',
                     'Permissão sem rota correspondente.', 'ai_analysis', :created, :updated),
                    (11, 'ai_analysis:read', 'Visualizar análise por IA',
                     'Permissão oficial.', 'ai_analysis', :created, :updated)
                """
            ),
            {"created": timestamp, "updated": timestamp},
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO role_permissions
                    (id, role_id, permission_id, created_at, updated_at)
                VALUES
                    (1, 1, 10, :created, :updated),
                    (2, 2, 10, :created, :updated),
                    (3, 3, 10, :created, :updated),
                    (4, 2, 11, :created, :updated)
                """
            ),
            {"created": timestamp, "updated": timestamp},
        )
        migration.op = Operations(MigrationContext.configure(connection))

        migration.upgrade()

        legacy_count = connection.execute(
            sa.text("SELECT COUNT(*) FROM permissions WHERE name = :name"),
            {"name": migration.LEGACY_PERMISSION_NAME},
        ).scalar_one()
        assert legacy_count == 0
        legacy_link_count = connection.execute(
            sa.text("SELECT COUNT(*) FROM role_permissions WHERE permission_id = 10")
        ).scalar_one()
        assert legacy_link_count == 0
        backed_up_roles = connection.execute(
            sa.text(
                "SELECT role_id FROM rbac_07_legacy_role_permission_backup "
                "ORDER BY role_id"
            )
        ).scalars().all()
        assert backed_up_roles == [1, 2, 3]
        active_links = connection.execute(
            sa.text("SELECT role_id, permission_id FROM role_permissions")
        ).all()
        assert active_links == [(2, 11)]

        migration.downgrade()

        restored_permission = connection.execute(
            sa.text(
                """
                SELECT id, name, display_name, description, module
                FROM permissions
                WHERE name = :name
                """
            ),
            {"name": migration.LEGACY_PERMISSION_NAME},
        ).one()
        assert restored_permission == (
            10,
            "ai_analysis:download",
            "Baixar análise por IA",
            "Permissão sem rota correspondente.",
            "ai_analysis",
        )
        restored_roles = connection.execute(
            sa.text(
                """
                SELECT role_permissions.role_id
                FROM role_permissions
                JOIN permissions ON permissions.id = role_permissions.permission_id
                WHERE permissions.name = :name
                ORDER BY role_permissions.role_id
                """
            ),
            {"name": migration.LEGACY_PERMISSION_NAME},
        ).scalars().all()
        assert restored_roles == [1, 2, 3]
        table_names = sa.inspect(connection).get_table_names()
        assert "rbac_07_legacy_permission_backup" not in table_names
        assert "rbac_07_legacy_role_permission_backup" not in table_names


def test_migration_is_safe_when_legacy_permission_does_not_exist() -> None:
    engine = sa.create_engine("sqlite://")
    create_legacy_database(engine)
    migration = load_migration()

    with engine.begin() as connection:
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        permission_count = connection.execute(
            sa.text("SELECT COUNT(*) FROM permissions")
        ).scalar_one()
        link_count = connection.execute(
            sa.text("SELECT COUNT(*) FROM role_permissions")
        ).scalar_one()
        assert permission_count == 0
        assert link_count == 0
        table_names = sa.inspect(connection).get_table_names()
        assert "rbac_07_legacy_permission_backup" not in table_names
        assert "rbac_07_legacy_role_permission_backup" not in table_names

        migration.downgrade()

        permission_count = connection.execute(
            sa.text("SELECT COUNT(*) FROM permissions")
        ).scalar_one()
        link_count = connection.execute(
            sa.text("SELECT COUNT(*) FROM role_permissions")
        ).scalar_one()
        assert permission_count == 0
        assert link_count == 0
