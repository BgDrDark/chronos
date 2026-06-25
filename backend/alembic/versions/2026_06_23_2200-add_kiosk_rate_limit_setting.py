"""add kiosk_validate_code_rate_limit global setting

Revision ID: add_kiosk_rate_limit
Revises: ('b1c2d3e4f5a6', 'ba_002_personality_test_assignments')
Create Date: 2026-06-23 22:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

revision = "add_kiosk_rate_limit"
down_revision = ("b1c2d3e4f5a6", "ba_002_personality_test_assignments")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO global_settings (key, value) "
        "VALUES ('kiosk_validate_code_rate_limit', '5/minute') "
        "ON CONFLICT (key) DO NOTHING"
    )


def downgrade() -> None:
    op.execute("DELETE FROM global_settings WHERE key = 'kiosk_validate_code_rate_limit'")
