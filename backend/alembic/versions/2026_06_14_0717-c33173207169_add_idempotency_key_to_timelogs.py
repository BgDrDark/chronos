"""add idempotency_key to timelogs

Revision ID: c33173207169
Revises: c7d1ef60c063
Create Date: 2026-06-14 07:17:26.683286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c33173207169'
down_revision: Union[str, Sequence[str], None] = 'c7d1ef60c063'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('timelogs', sa.Column('idempotency_key', sa.String(36), nullable=True))
    op.create_index('ix_timelogs_idempotency_key', 'timelogs', ['idempotency_key'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_timelogs_idempotency_key', table_name='timelogs')
    op.drop_column('timelogs', 'idempotency_key')
