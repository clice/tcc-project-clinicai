"""Restringe o acesso clínico do Administrador Master.

Revision ID: 0002adminprivacy
Revises: 0001clinicai
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002adminprivacy"
down_revision: Union[str, None] = "0001clinicai"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_DESCRIPTION = "Administrador com acesso total ao sistema."
NEW_DESCRIPTION = (
    "Administrador da estrutura do sistema, sem acesso aos detalhes clínicos, "
    "às imagens, às análises de IA ou à revisão médica dos exames."
)

RESTRICTED_PERMISSIONS = (
    "exams:create",
    "exams:read",
    "exams:update",
    "exams:upload",
    "exams:download",
    "exams:change_status",
    "exams:review",
    "ai_analysis:create",
    "ai_analysis:read",
    "ai_analysis:update",
)

roles = sa.table(
    "roles",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
    sa.column("description", sa.String()),
)

permissions = sa.table(
    "permissions",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
)

role_permissions = sa.table(
    "role_permissions",
    sa.column("id", sa.Integer()),
    sa.column("role_id", sa.Integer()),
    sa.column("permission_id", sa.Integer()),
)


def _admin_role_id(bind) -> int | None:
    return bind.execute(
        sa.select(roles.c.id).where(roles.c.name == "admin_master")
    ).scalar_one_or_none()


def upgrade() -> None:
    bind = op.get_bind()
    admin_role_id = _admin_role_id(bind)

    bind.execute(
        roles.update()
        .where(roles.c.name == "admin_master")
        .values(description=NEW_DESCRIPTION)
    )

    if admin_role_id is None:
        return

    restricted_ids = sa.select(permissions.c.id).where(
        permissions.c.name.in_(RESTRICTED_PERMISSIONS)
    )

    bind.execute(
        role_permissions.delete().where(
            sa.and_(
                role_permissions.c.role_id == admin_role_id,
                role_permissions.c.permission_id.in_(restricted_ids),
            )
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    admin_role_id = _admin_role_id(bind)

    bind.execute(
        roles.update()
        .where(roles.c.name == "admin_master")
        .values(description=OLD_DESCRIPTION)
    )

    if admin_role_id is None:
        return

    permission_ids = set(
        bind.execute(
            sa.select(permissions.c.id).where(
                permissions.c.name.in_(RESTRICTED_PERMISSIONS)
            )
        ).scalars()
    )
    existing_ids = set(
        bind.execute(
            sa.select(role_permissions.c.permission_id).where(
                role_permissions.c.role_id == admin_role_id
            )
        ).scalars()
    )

    missing_ids = permission_ids - existing_ids
    if missing_ids:
        bind.execute(
            role_permissions.insert(),
            [
                {
                    "role_id": admin_role_id,
                    "permission_id": permission_id,
                }
                for permission_id in sorted(missing_ids)
            ],
        )
