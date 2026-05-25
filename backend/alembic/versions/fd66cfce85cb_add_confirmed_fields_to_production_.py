"""add confirmed fields to production orders

Revision ID: fd66cfce85cb
Revises: fdf2d575c873
Create Date: 2026-02-14 17:24:49.840921

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fd66cfce85cb"
down_revision: str | Sequence[str] | None = "fdf2d575c873"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("production_orders", sa.Column("confirmed_at", sa.DateTime(), nullable=True))
    op.add_column("production_orders", sa.Column("confirmed_by", sa.Integer(), nullable=True))
    op.create_foreign_key("production_orders_confirmed_by_fkey", "production_orders", "users", ["confirmed_by"], ["id"])


def downgrade() -> None:
    op.drop_constraint("production_orders_confirmed_by_fkey", "production_orders", "foreignkey")
    op.drop_column("production_orders", "confirmed_by")
    op.drop_column("production_orders", "confirmed_at")
