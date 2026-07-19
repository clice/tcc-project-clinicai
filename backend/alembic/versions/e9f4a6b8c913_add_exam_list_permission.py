"""Adiciona permissão resumida de listagem de exames.

Revision ID: e9f4a6b8c913
Revises: e4f6a8b0c213
Create Date: 2026-07-18 00:00:00.000000

A listagem operacional é separada do acesso aos detalhes clínicos.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e9f4a6b8c913"
down_revision: Union[str, None] = "e4f6a8b0c213"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSION_NAME = "exams:list"
ROLE_NAMES = ("admin_master", "doctor", "clinic_staff")

permissions_table = sa.table(
    "permissions",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
    sa.column("display_name", sa.String()),
    sa.column("description", sa.String()),
    sa.column("module", sa.String()),
)
roles_table = sa.table(
    "roles",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
)
role_permissions_table = sa.table(
    "role_permissions",
    sa.column("role_id", sa.Integer()),
    sa.column("permission_id", sa.Integer()),
)


def get_permission_id(connection) -> int | None:
    return connection.execute(
        sa.select(permissions_table.c.id).where(
            permissions_table.c.name == PERMISSION_NAME
        )
    ).scalar_one_or_none()


def upgrade() -> None:
    connection = op.get_bind()
    role_ids = set(
        connection.execute(
            sa.select(roles_table.c.id).where(
                roles_table.c.name.in_(ROLE_NAMES)
            )
        ).scalars()
    )
    catalog_has_entries = (
        connection.execute(
            sa.select(permissions_table.c.id).limit(1)
        ).first()
        is not None
    )

    # Em uma instalação nova, migrations precedem o bootstrap. Nesse caso,
    # roles e permissions ainda estão vazias e o seed criará o catálogo e a
    # matriz completos. Inserir somente exams:list aqui deixaria o catálogo
    # parcial e impediria o bootstrap.
    if not role_ids and not catalog_has_entries:
        return

    # Fora do banco totalmente vazio, os três perfis oficiais devem existir.
    # Um catálogo ainda vazio é aceito quando todos os perfis estão presentes,
    # preservando a compatibilidade da migration com bancos inicializados por
    # fluxos anteriores.
    if len(role_ids) != len(ROLE_NAMES):
        raise RuntimeError(
            "Nem todos os perfis oficiais foram encontrados."
        )

    permission_id = get_permission_id(connection)

    if permission_id is None:
        connection.execute(
            sa.insert(permissions_table).values(
                name=PERMISSION_NAME,
                display_name="Listar Exames",
                description=(
                    "Permite acompanhar a listagem e os status dos "
                    "exames sem acessar detalhes clínicos."
                ),
                module="exams",
            )
        )
        permission_id = get_permission_id(connection)

    if permission_id is None:
        raise RuntimeError(
            "Não foi possível criar ou localizar exams:list."
        )

    linked_role_ids = set(
        connection.execute(
            sa.select(role_permissions_table.c.role_id).where(
                role_permissions_table.c.permission_id
                == permission_id
            )
        ).scalars()
    )

    for role_id in sorted(role_ids - linked_role_ids):
        connection.execute(
            sa.insert(role_permissions_table).values(
                role_id=role_id,
                permission_id=permission_id,
            )
        )


def downgrade() -> None:
    connection = op.get_bind()
    permission_id = get_permission_id(connection)

    if permission_id is None:
        return

    connection.execute(
        sa.delete(role_permissions_table).where(
            role_permissions_table.c.permission_id
            == permission_id
        )
    )
    connection.execute(
        sa.delete(permissions_table).where(
            permissions_table.c.id == permission_id
        )
    )
