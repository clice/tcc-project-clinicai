"""Torna dados essenciais do paciente obrigatórios.

Revision ID: 0003patientrequired
Revises: 0002adminprivacy
"""

from alembic import op
import sqlalchemy as sa


revision = "0003patientrequired"
down_revision = "0002adminprivacy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    incomplete_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM patients
            WHERE birth_date IS NULL
               OR sex IS NULL
               OR BTRIM(sex) = ''
               OR phone IS NULL
               OR BTRIM(phone) = ''
            """
        )
    ).scalar_one()

    if incomplete_count:
        raise RuntimeError(
            "Existem pacientes sem data de nascimento, sexo ou telefone. "
            "Corrija os registros antes de aplicar esta migration."
        )

    op.alter_column(
        "patients",
        "birth_date",
        existing_type=sa.Date(),
        nullable=False,
    )
    op.alter_column(
        "patients",
        "sex",
        existing_type=sa.String(length=20),
        nullable=False,
    )
    op.alter_column(
        "patients",
        "phone",
        existing_type=sa.String(length=20),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "patients",
        "phone",
        existing_type=sa.String(length=20),
        nullable=True,
    )
    op.alter_column(
        "patients",
        "sex",
        existing_type=sa.String(length=20),
        nullable=True,
    )
    op.alter_column(
        "patients",
        "birth_date",
        existing_type=sa.Date(),
        nullable=True,
    )
