"""add probation_beneficiary and notice_period_days to employment_contracts

Revision ID: b1c2d3e4f5a6
Revises: ac5a9430d80f
Create Date: 2026-06-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'ac5a9430d80f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('employment_contracts', sa.Column('probation_beneficiary', sa.String(length=20), nullable=True))
    op.add_column('employment_contracts', sa.Column('notice_period_days', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('employment_contracts', 'notice_period_days')
    op.drop_column('employment_contracts', 'probation_beneficiary')
