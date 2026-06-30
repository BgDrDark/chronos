"""pin_encrypted + pin_sha256 columns

Revision ID: ba_008
Revises: ba_007
Create Date: 2026-06-29 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ba_008'
down_revision: Union[str, None] = 'ba_007'
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('pin_encrypted', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('pin_sha256', sa.String(length=64), nullable=True))
    op.create_unique_constraint('uq_users_pin_sha256', 'users', ['pin_sha256'])


def downgrade() -> None:
    op.drop_constraint('uq_users_pin_sha256', 'users', type_='unique')
    op.drop_column('users', 'pin_sha256')
    op.drop_column('users', 'pin_encrypted')
