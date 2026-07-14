"""add atomic IA analysis claim to exams

Revision ID: e4f6a8b0c213
Revises: d3e5f7a9b102
Create Date: 2026-07-14 00:00:00.000000

CHK-09: impede duas requisições concorrentes de dispararem a inferência do
mesmo exame e registra quando a tentativa atual começou.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e4f6a8b0c213"
down_revision: Union[str, None] = "d3e5f7a9b102"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exams",
        sa.Column(
            "analysis_in_progress",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "exams",
        sa.Column("analysis_started_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("exams", "analysis_started_at")
    op.drop_column("exams", "analysis_in_progress")
