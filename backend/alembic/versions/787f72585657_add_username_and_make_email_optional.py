"""add_username_and_make_email_optional

Revision ID: 787f72585657
Revises: 3c93f2e81c02
Create Date: 2026-02-08 22:59:27.676316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '787f72585657'
down_revision: Union[str, Sequence[str], None] = '3c93f2e81c02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add username column
    op.add_column('users', sa.Column('username', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Make email optional
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade() -> None:
    # Make email required again (CAUTION: ensure no nulls exist)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
               
    # Remove username column
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'username')
