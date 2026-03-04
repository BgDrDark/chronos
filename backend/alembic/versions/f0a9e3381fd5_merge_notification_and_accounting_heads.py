"""merge_notification_and_accounting_heads

Revision ID: f0a9e3381fd5
Revises: add_notification_settings, b9440e251f54
Create Date: 2026-02-15 00:13:13.651034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0a9e3381fd5'
down_revision: Union[str, Sequence[str], None] = ('add_notification_settings', 'b9440e251f54')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
