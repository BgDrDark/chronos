"""add_profile_picture_to_user

Revision ID: 716dacaac802
Revises: 8aad9bc5feef
Create Date: 2026-02-09 00:15:39.642238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '716dacaac802'
down_revision: Union[str, Sequence[str], None] = '8aad9bc5feef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('profile_picture', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'profile_picture')
