"""Teste da migration que separa listagem e detalhes de exames."""

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
        / "e9f4a6b8c913_add_exam_list_permission.py"
    )
    spec = importlib.util.spec_from_file_location(
        "exam_list_permission_migration",
        migration_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_adds_and_removes_exam_list_permission() -> None:
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()

    roles = sa.Table(
        "roles",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
    )
    permissions = sa.Table(
        "permissions",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("display_name", sa.String, nullable=False),
        sa.Column("description", sa.String),
        sa.Column("module", sa.String, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    role_permissions = sa.Table(
        "role_permissions",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("role_id", sa.Integer, nullable=False),
        sa.Column("permission_id", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.UniqueConstraint("role_id", "permission_id"),
    )
    metadata.create_all(engine)

    migration = load_migration()

    with engine.begin() as connection:
        connection.execute(
            roles.insert(),
            [
                {"id": 1, "name": "admin_master"},
                {"id": 2, "name": "doctor"},
                {"id": 3, "name": "clinic_staff"},
            ],
        )
        migration.op = Operations(
            MigrationContext.configure(connection)
        )

        migration.upgrade()

        permission = connection.execute(
            sa.select(permissions).where(
                permissions.c.name == "exams:list"
            )
        ).mappings().one()

        links = set(
            connection.execute(
                sa.select(roles.c.name)
                .join(
                    role_permissions,
                    role_permissions.c.role_id == roles.c.id,
                )
                .where(
                    role_permissions.c.permission_id
                    == permission["id"]
                )
            ).scalars()
        )
        assert links == {
            "admin_master",
            "doctor",
            "clinic_staff",
        }

        migration.downgrade()

        assert (
            connection.execute(
                sa.select(sa.func.count())
                .select_from(permissions)
                .where(permissions.c.name == "exams:list")
            ).scalar_one()
            == 0
        )
        assert (
            connection.execute(
                sa.select(sa.func.count()).select_from(
                    role_permissions
                )
            ).scalar_one()
            == 0
        )

def test_migration_leaves_empty_database_for_bootstrap() -> None:
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()

    sa.Table(
        "roles",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
    )
    sa.Table(
        "permissions",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("display_name", sa.String, nullable=False),
        sa.Column("description", sa.String),
        sa.Column("module", sa.String, nullable=False),
    )
    sa.Table(
        "role_permissions",
        metadata,
        sa.Column("role_id", sa.Integer, primary_key=True),
        sa.Column("permission_id", sa.Integer, primary_key=True),
    )
    metadata.create_all(engine)

    migration = load_migration()

    with engine.begin() as connection:
        migration.op = Operations(
            MigrationContext.configure(connection)
        )
        migration.upgrade()

        permission_count = connection.scalar(
            sa.text("SELECT count(*) FROM permissions")
        )
        link_count = connection.scalar(
            sa.text("SELECT count(*) FROM role_permissions")
        )

    assert permission_count == 0
    assert link_count == 0
