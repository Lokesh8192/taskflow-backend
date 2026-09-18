"""change project creator to integer

Revision ID: 9b7c1d2e4f5a
Revises: ee1b6268bcd3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b7c1d2e4f5a"
down_revision: Union[str, Sequence[str], None] = "ee1b6268bcd3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "projects",
        "created_by",
        existing_type=sa.String(),
        type_=sa.Integer(),
        postgresql_using="created_by::integer",
    )


def downgrade() -> None:
    op.alter_column(
        "projects",
        "created_by",
        existing_type=sa.Integer(),
        type_=sa.String(),
        postgresql_using="created_by::text",
    )
