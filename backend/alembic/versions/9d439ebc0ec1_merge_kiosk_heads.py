"""merge_kiosk_heads

Revision ID: 9d439ebc0ec1
Revises: ba71d6763af9, add_terminal_mode_to_doors
Create Date: 2026-03-04 22:00:37.156285

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d439ebc0ec1'
down_revision: Union[str, Sequence[str], None] = ('ba71d6763af9', 'add_terminal_mode_to_doors')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
