"""Add labor contract fields to employment_contracts

Revision ID: add_labor_contract_fields
Revises: add_position_id_to_contracts
Create Date: 2026-03-18
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_labor_contract_fields'
down_revision = 'add_position_id_to_contracts'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'employment_contracts',
        sa.Column('employee_name', sa.String(200), nullable=True)
    )
    op.add_column(
        'employment_contracts',
        sa.Column('employee_egn', sa.String(10), nullable=True)
    )
    op.add_column(
        'employment_contracts',
        sa.Column('status', sa.String(20), default='draft', server_default='draft')
    )
    op.add_column(
        'employment_contracts',
        sa.Column('signed_at', sa.DateTime(), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('employment_contracts', 'signed_at')
    op.drop_column('employment_contracts', 'status')
    op.drop_column('employment_contracts', 'employee_egn')
    op.drop_column('employment_contracts', 'employee_name')
