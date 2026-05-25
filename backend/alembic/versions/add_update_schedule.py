"""Add update_schedule table

Revision ID: add_update_schedule
Revises: add_maintenance_settings
Create Date: 2026-05-17

"""
import sqlalchemy as sa

from alembic import op

revision = "add_update_schedule"
down_revision = "add_maintenance_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("update_schedule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("schedule_type", sa.String(20), nullable=False, server_default="once"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("hour", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("minute", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notify_email", sa.String(255), nullable=False, server_default=""),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_status", sa.String(20), nullable=True),
        sa.Column("last_run_output", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_update_schedule_id"), "update_schedule", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_update_schedule_id"), table_name="update_schedule")
    op.drop_table("update_schedule")
