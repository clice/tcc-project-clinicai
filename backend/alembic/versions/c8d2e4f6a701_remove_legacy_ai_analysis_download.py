"""remove a permissão legada ai_analysis:download

Revision ID: c8d2e4f6a701
Revises: b7c1d4e2f901
Create Date: 2026-07-13 00:00:00.000000

RBAC-07: a permissão não pertence mais ao catálogo oficial, mas pode continuar
armazenada em bancos inicializados por versões anteriores. A migration mantém
uma salvaguarda dos dados removidos para permitir rollback sem perder os
vínculos personalizados entre roles e a permissão legada.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c8d2e4f6a701"
down_revision: Union[str, None] = "b7c1d4e2f901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY_PERMISSION_NAME = "ai_analysis:download"
PERMISSION_BACKUP_TABLE = "rbac_07_legacy_permission_backup"
ROLE_LINK_BACKUP_TABLE = "rbac_07_legacy_role_permission_backup"


def upgrade() -> None:
    """Salva e remove a permissão legada e todos os seus vínculos ativos."""

    connection = op.get_bind()
    legacy_permission_id = connection.execute(
        sa.text("SELECT id FROM permissions WHERE name = :permission_name"),
        {"permission_name": LEGACY_PERMISSION_NAME},
    ).scalar_one_or_none()
    if legacy_permission_id is None:
        return

    op.create_table(
        PERMISSION_BACKUP_TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        ROLE_LINK_BACKUP_TABLE,
        sa.Column("role_id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    connection.execute(
        sa.text(
            f"""
            INSERT INTO {PERMISSION_BACKUP_TABLE}
                (id, name, display_name, description, module, created_at, updated_at)
            SELECT id, name, display_name, description, module, created_at, updated_at
            FROM permissions
            WHERE name = :permission_name
            """
        ),
        {"permission_name": LEGACY_PERMISSION_NAME},
    )
    connection.execute(
        sa.text(
            f"""
            INSERT INTO {ROLE_LINK_BACKUP_TABLE} (role_id, created_at, updated_at)
            SELECT role_permissions.role_id,
                   role_permissions.created_at,
                   role_permissions.updated_at
            FROM role_permissions
            JOIN permissions
              ON permissions.id = role_permissions.permission_id
            WHERE permissions.name = :permission_name
            """
        ),
        {"permission_name": LEGACY_PERMISSION_NAME},
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE name = :permission_name
            )
            """
        ),
        {"permission_name": LEGACY_PERMISSION_NAME},
    )
    connection.execute(
        sa.text("DELETE FROM permissions WHERE name = :permission_name"),
        {"permission_name": LEGACY_PERMISSION_NAME},
    )


def downgrade() -> None:
    """Restaura a permissão e os vínculos salvos antes da remoção."""

    connection = op.get_bind()
    existing_tables = set(sa.inspect(connection).get_table_names())
    if not {PERMISSION_BACKUP_TABLE, ROLE_LINK_BACKUP_TABLE}.issubset(
        existing_tables
    ):
        return

    connection.execute(
        sa.text(
            f"""
            INSERT INTO permissions
                (id, name, display_name, description, module, created_at, updated_at)
            SELECT id, name, display_name, description, module, created_at, updated_at
            FROM {PERMISSION_BACKUP_TABLE}
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions
                WHERE permissions.name = {PERMISSION_BACKUP_TABLE}.name
            )
            """
        )
    )
    connection.execute(
        sa.text(
            f"""
            INSERT INTO role_permissions
                (role_id, permission_id, created_at, updated_at)
            SELECT backup.role_id,
                   permissions.id,
                   backup.created_at,
                   backup.updated_at
            FROM {ROLE_LINK_BACKUP_TABLE} AS backup
            JOIN roles ON roles.id = backup.role_id
            JOIN permissions ON permissions.name = :permission_name
            WHERE NOT EXISTS (
                SELECT 1 FROM role_permissions
                WHERE role_permissions.role_id = backup.role_id
                  AND role_permissions.permission_id = permissions.id
            )
            """
        ),
        {"permission_name": LEGACY_PERMISSION_NAME},
    )

    op.drop_table(ROLE_LINK_BACKUP_TABLE)
    op.drop_table(PERMISSION_BACKUP_TABLE)
