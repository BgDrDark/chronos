"""Add AccessLevel, AccessLevelZone, AccessSchedule models (Phase 1)

Revision ID: ba_003
Revises: add_user_external_id
Create Date: 2026-06-27 12:35:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "ba_003"
down_revision: Union[str, None] = "add_user_external_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create access_levels table
    op.create_table("access_levels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_levels_company_id"), "access_levels", ["company_id"], unique=False)

    # Create access_schedules table
    op.create_table("access_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=True, server_default="Europe/Sofia"),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("holiday_override_auto", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_schedules_company_id"), "access_schedules", ["company_id"], unique=False)

    # Create access_level_zones table
    op.create_table("access_level_zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("access_level_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=False),
        sa.Column("schedule_id", sa.Integer(), nullable=True),
        sa.Column("out_of_hours_behavior", sa.String(length=20), nullable=True, server_default="deny"),
        sa.Column("priority", sa.Integer(), nullable=True, server_default="0"),
        sa.ForeignKeyConstraint(["access_level_id"], ["access_levels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["schedule_id"], ["access_schedules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["zone_id"], ["access_zones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_level_zones_level_id"), "access_level_zones", ["access_level_id"], unique=False)
    op.create_index(op.f("ix_access_level_zones_zone_id"), "access_level_zones", ["zone_id"], unique=False)

    # Add access_level_id to users table
    op.add_column("users", sa.Column("access_level_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_users_access_level_id", "users", "access_levels", ["access_level_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_users_access_level_id", "users", ["access_level_id"], unique=False)


def downgrade() -> None:
    # Remove access_level_id from users
    op.drop_index("ix_users_access_level_id", table_name="users")
    op.drop_constraint("fk_users_access_level_id", "users", type_="foreignkey")
    op.drop_column("users", "access_level_id")

    # Drop access_level_zones
    op.drop_index(op.f("ix_access_level_zones_level_id"), table_name="access_level_zones")
    op.drop_index(op.f("ix_access_level_zones_zone_id"), table_name="access_level_zones")
    op.drop_table("access_level_zones")

    # Drop access_schedules
    op.drop_index(op.f("ix_access_schedules_company_id"), table_name="access_schedules")
    op.drop_table("access_schedules")

    # Drop access_levels
    op.drop_index(op.f("ix_access_levels_company_id"), table_name="access_levels")
    op.drop_table("access_levels")
