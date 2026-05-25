"""merge_all_heads

Revision ID: ea76c81c7703
Revises: f0a9e3381fd5, fd66cfce85cb
Create Date: 2026-02-15 00:13:23.669968

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "ea76c81c7703"
down_revision: str | Sequence[str] | None = ("f0a9e3381fd5", "fd66cfce85cb")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
