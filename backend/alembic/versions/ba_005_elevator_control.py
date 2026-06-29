"""Add ElevatorGroup + ElevatorFloor models (Phase 5)

Revision ID: ba_005
Revises: ba_004
Create Date: 2026-06-28 22:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ba_005"
down_revision: Union[str, None] = "ba_004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "elevator_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gateway_id", sa.Integer(), sa.ForeignKey("gateways.id", ondelete="CASCADE"), nullable=False),
        sa.Column("terminal_id", sa.String(50), nullable=False),
        sa.Column("controller_type", sa.String(30), nullable=False, server_default="sr201"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "elevator_floors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("elevator_group_id", sa.Integer(), sa.ForeignKey("elevator_groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("floor_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("access_zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("relay_device_id", sa.String(50), nullable=False),
        sa.Column("relay_number", sa.Integer(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index(op.f("ix_elevator_floors_elevator_group_id"), "elevator_floors", ["elevator_group_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_elevator_floors_elevator_group_id"), table_name="elevator_floors")
    op.drop_table("elevator_floors")
    op.drop_table("elevator_groups")
