"""add indexes to audit_logs

Revision ID: idx_audit_logs_001
Revises: 5138fc0e331c
Create Date: 2026-05-25

"""
from alembic import op

revision = "idx_audit_logs_001"
down_revision = "5138fc0e331c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
