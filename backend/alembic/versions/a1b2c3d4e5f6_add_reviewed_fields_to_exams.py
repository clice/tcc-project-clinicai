"""add reviewed_by_id and reviewed_at to exams

Revision ID: a1b2c3d4e5f6
Revises: 61a3d1ba6d26
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '61a3d1ba6d26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('exams', sa.Column('reviewed_by_id', sa.Integer(), nullable=True))
    op.add_column('exams', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))

    op.create_index(op.f('ix_exams_reviewed_by_id'), 'exams', ['reviewed_by_id'], unique=False)
    op.create_foreign_key(
        'fk_exams_reviewed_by_id_users',
        'exams',
        'users',
        ['reviewed_by_id'],
        ['id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_exams_reviewed_by_id_users', 'exams', type_='foreignkey')
    op.drop_index(op.f('ix_exams_reviewed_by_id'), table_name='exams')
    op.drop_column('exams', 'reviewed_at')
    op.drop_column('exams', 'reviewed_by_id')
