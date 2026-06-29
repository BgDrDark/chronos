"""Add emergency/lockdown fields to AccessZone + EmergencyEvent table (Phase 6)

Revision ID: ba_006
Revises: ba_005
Create Date: 2026-06-28 22:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ba_006"
down_revision: Union[str, None] = "ba_005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("access_zones", sa.Column("is_safe_zone", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("access_zones", sa.Column("lockdown_behavior", sa.String(20), nullable=False, server_default=sa.text("'lock'")))
    op.add_column("access_zones", sa.Column("emergency_contact", sa.String(255), nullable=True))
    op.create_table(
        "emergency_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False, server_default="all"),
        sa.Column("gateway_id", sa.Integer(), sa.ForeignKey("gateways.id", ondelete="SET NULL"), nullable=True),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("access_zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("triggered_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("emergency_events")
    op.drop_column("access_zones", "emergency_contact")
    op.drop_column("access_zones", "lockdown_behavior")
    op.drop_column("access_zones", "is_safe_zone")
