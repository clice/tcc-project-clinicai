"""add index to clinics.status_id

Revision ID: d3e5f7a9b102
Revises: c8d2e4f6a701
Create Date: 2026-07-14 00:00:00.000000

CHK-03: todas as FKs usadas em filtros/joins operacionais devem possuir índice.
``clinics.status_id`` era a única FK principal sem índice explícito.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d3e5f7a9b102"
down_revision: Union[str, None] = "c8d2e4f6a701"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria o índice utilizado por filtros e joins de status de clínica."""

    op.create_index(
        op.f("ix_clinics_status_id"),
        "clinics",
        ["status_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove somente o índice introduzido por esta revisão."""

    op.drop_index(op.f("ix_clinics_status_id"), table_name="clinics")
