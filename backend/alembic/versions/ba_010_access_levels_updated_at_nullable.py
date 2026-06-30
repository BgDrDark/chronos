"""access_levels.updated_at: NOT NULL -> nullable

Revision ID: ba_010
Revises: ba_009
Create Date: 2026-06-30 06:55:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ba_010"
down_revision: Union[str, None] = "ba_009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("access_levels", "updated_at", nullable=True)


def downgrade() -> None:
    op.alter_column("access_levels", "updated_at", nullable=False)
