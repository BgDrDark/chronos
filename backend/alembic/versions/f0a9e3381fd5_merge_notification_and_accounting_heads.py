"""merge_notification_and_accounting_heads

Revision ID: f0a9e3381fd5
Revises: add_notification_settings, b9440e251f54
Create Date: 2026-02-15 00:13:13.651034

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "f0a9e3381fd5"
down_revision: str | Sequence[str] | None = ("add_notification_settings", "b9440e251f54")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
