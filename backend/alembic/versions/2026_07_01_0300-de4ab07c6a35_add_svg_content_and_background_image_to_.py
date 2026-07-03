"""add svg_content and background_image to floor_plans

Revision ID: de4ab07c6a35
Revises: ba_010
Create Date: 2026-07-01 03:00:15.531366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de4ab07c6a35'
down_revision: Union[str, Sequence[str], None] = 'ba_010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('floor_plans', sa.Column('svg_content', sa.Text(), nullable=True))
    op.add_column('floor_plans', sa.Column('background_image', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('floor_plans', 'background_image')
    op.drop_column('floor_plans', 'svg_content')
