"""merge_heads

Revision ID: fdf2d575c873
Revises: 716dacaac802, g123456789ad
Create Date: 2026-02-09 00:47:24.233220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fdf2d575c873'
down_revision: Union[str, Sequence[str], None] = ('716dacaac802', 'g123456789ad')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
