"""Add company_id to schedule_templates

Revision ID: add_st_company_id
Revises: add_invoice_item_extended_fields, add_labor_contract_fields, add_price_to_stock_consumption
Create Date: 2026-03-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_st_company_id'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add company_id column to schedule_templates table
    op.add_column('schedule_templates', 
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False, server_default='1'))
    
    # Create index for faster lookups
    op.create_index('idx_schedule_templates_company_id', 'schedule_templates', ['company_id'])


def downgrade() -> None:
    op.drop_index('idx_schedule_templates_company_id', table_name='schedule_templates')
    op.drop_column('schedule_templates', 'company_id')
