"""add_department_manager

Revision ID: 8aad9bc5feef
Revises: c6f40e20fe4e
Create Date: 2026-02-08 23:58:55.800705

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8aad9bc5feef"
down_revision: str | Sequence[str] | None = "c6f40e20fe4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("departments", sa.Column("manager_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_departments_manager_id_users", "departments", "users", ["manager_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_departments_manager_id_users", "departments", type_="foreignkey")
    op.drop_column("departments", "manager_id")
