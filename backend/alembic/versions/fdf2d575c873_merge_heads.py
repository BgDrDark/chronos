"""merge_heads

Revision ID: fdf2d575c873
Revises: 716dacaac802, g123456789ad
Create Date: 2026-02-09 00:47:24.233220

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "fdf2d575c873"
down_revision: str | Sequence[str] | None = ("716dacaac802", "g123456789ad")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
