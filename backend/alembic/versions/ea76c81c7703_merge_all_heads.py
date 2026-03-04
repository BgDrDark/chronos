"""merge_all_heads

Revision ID: ea76c81c7703
Revises: f0a9e3381fd5, fd66cfce85cb
Create Date: 2026-02-15 00:13:23.669968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea76c81c7703'
down_revision: Union[str, Sequence[str], None] = ('f0a9e3381fd5', 'fd66cfce85cb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
