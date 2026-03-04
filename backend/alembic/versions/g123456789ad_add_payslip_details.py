"""add_payslip_details

Revision ID: g123456789ad
Revises: f123456789ac
Create Date: 2026-01-23 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g123456789ad'
down_revision: Union[str, Sequence[str], None] = 'f123456789ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('payslips', sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'))
    op.add_column('payslips', sa.Column('insurance_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'))
    op.add_column('payslips', sa.Column('sick_days', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('payslips', sa.Column('leave_days', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('payslips', 'leave_days')
    op.drop_column('payslips', 'sick_days')
    op.drop_column('payslips', 'insurance_amount')
    op.drop_column('payslips', 'tax_amount')
