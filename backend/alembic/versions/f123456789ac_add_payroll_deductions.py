"""add_payroll_deductions

Revision ID: f123456789ac
Revises: e123456789ab
Create Date: 2026-01-23 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f123456789ac'
down_revision: Union[str, Sequence[str], None] = 'e123456789ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('payrolls', sa.Column('tax_percent', sa.Numeric(precision=5, scale=2), nullable=True, server_default='10.00'))
    op.add_column('payrolls', sa.Column('health_insurance_percent', sa.Numeric(precision=5, scale=2), nullable=True, server_default='13.78'))
    op.add_column('payrolls', sa.Column('has_tax_deduction', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('payrolls', sa.Column('has_health_insurance', sa.Boolean(), nullable=True, server_default='true'))


def downgrade() -> None:
    op.drop_column('payrolls', 'has_health_insurance')
    op.drop_column('payrolls', 'has_tax_deduction')
    op.drop_column('payrolls', 'health_insurance_percent')
    op.drop_column('payrolls', 'tax_percent')
