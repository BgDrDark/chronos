"""Fill NULL created_at for users

Revision ID: 656ab3cb1bdc
Revises: 441de29ab3f5
Create Date: 2026-01-06 23:40:01.992185

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "656ab3cb1bdc"
down_revision: str | Sequence[str] | None = "441de29ab3f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE users SET created_at = NOW() WHERE created_at IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
