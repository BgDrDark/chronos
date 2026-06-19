"""add personality test assignments table

Revision ID: ba_002_personality_test_assignments
Revises: ba_001_behavioral_analysis
Create Date: 2026-06-19 06:40:00.000000

"""
import sqlalchemy as sa

from alembic import op

revision = "ba_002_personality_test_assignments"
down_revision = "ba_001_behavioral_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "behavioral_personality_test_assignments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("behavioral_personality_test_templates.id"), nullable=False),
        sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("due_by", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("notified_overdue", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("behavioral_personality_test_assignments")
