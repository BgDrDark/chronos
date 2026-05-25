"""add_password_force_change_to_users_and_versioning

Revision ID: b2143731f014
Revises: 787f72585657
Create Date: 2026-02-08 23:18:23.028063

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "b2143731f014"
down_revision: str | Sequence[str] | None = "787f72585657"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
