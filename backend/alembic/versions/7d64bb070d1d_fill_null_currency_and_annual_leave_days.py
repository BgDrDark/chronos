"""Fill NULL currency and annual_leave_days

Revision ID: 7d64bb070d1d
Revises: 6488e84c6641
Create Date: 2026-01-06 22:42:15.409114

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d64bb070d1d"
down_revision: str | Sequence[str] | None = "6488e84c6641"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE payrolls SET currency = 'BGN' WHERE currency IS NULL")
    op.execute("UPDATE payrolls SET annual_leave_days = 20 WHERE annual_leave_days IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
