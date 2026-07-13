"""remove legacy clinic_staff exam and AI permissions

Revision ID: b7c1d4e2f901
Revises: a1b2c3d4e5f6
Create Date: 2026-07-13 00:00:00.000000

RBAC-01: mudanças oficiais na matriz de bancos existentes são migrations de
dados. O bootstrap não deve reconciliar customizações a cada inicialização.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b7c1d4e2f901"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_NAME = "clinic_staff"
LEGACY_PERMISSION_NAMES = ("exams:read", "ai_analysis:read")


def upgrade() -> None:
    """Marca roles existentes e revoga vínculos legados específicos."""

    connection = op.get_bind()
    op.add_column(
        "roles",
        sa.Column(
            "permissions_initialized",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    # Toda role já existente pertence a um banco inicializado por uma versão
    # anterior. Marcar todas também preserva uma role que o administrador
    # tenha deixado intencionalmente sem permissões antes desta migration.
    connection.execute(
        sa.text(
            """
            UPDATE roles
            SET permissions_initialized = true
            """
        )
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE role_id = (SELECT id FROM roles WHERE name = :role_name)
              AND permission_id IN (
                  SELECT id FROM permissions WHERE name IN (:exam_read, :ai_read)
              )
            """
        ),
        {
            "role_name": ROLE_NAME,
            "exam_read": LEGACY_PERMISSION_NAMES[0],
            "ai_read": LEGACY_PERMISSION_NAMES[1],
        },
    )


def downgrade() -> None:
    """Restaura os vínculos legados somente quando role e permissões existem."""

    connection = op.get_bind()
    for permission_name in LEGACY_PERMISSION_NAMES:
        connection.execute(
            sa.text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT roles.id, permissions.id
                FROM roles, permissions
                WHERE roles.name = :role_name
                  AND permissions.name = :permission_name
                  AND NOT EXISTS (
                      SELECT 1 FROM role_permissions
                      WHERE role_permissions.role_id = roles.id
                        AND role_permissions.permission_id = permissions.id
                  )
                """
            ),
            {"role_name": ROLE_NAME, "permission_name": permission_name},
        )
    op.drop_column("roles", "permissions_initialized")
