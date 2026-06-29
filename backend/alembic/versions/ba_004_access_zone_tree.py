"""Add parent_zone_id, inherit_permissions, traversal_order to AccessZone

Revision ID: ba_004
Revises: ba_003
Create Date: 2026-06-28 21:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ba_004"
down_revision: Union[str, None] = "ba_003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("access_zones", sa.Column("parent_zone_id", sa.Integer(), sa.ForeignKey("access_zones.id", ondelete="SET NULL"), nullable=True))
    op.add_column("access_zones", sa.Column("inherit_permissions", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.add_column("access_zones", sa.Column("traversal_order", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.create_index(op.f("ix_access_zones_parent_zone_id"), "access_zones", ["parent_zone_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_access_zones_parent_zone_id"), table_name="access_zones")
    op.drop_column("access_zones", "traversal_order")
    op.drop_column("access_zones", "inherit_permissions")
    op.drop_column("access_zones", "parent_zone_id")
