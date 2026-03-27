"""Add price fields to StockConsumptionLog

Revision ID: add_price_to_stock_consumption
Revises: 
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_price_to_stock_consumption'
down_revision = None  # Update this to latest revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add price_per_unit field
    op.add_column('stock_consumption_logs', 
        sa.Column('price_per_unit', sa.Numeric(12, 4), nullable=True, comment='Цена на единица от партидата'))
    
    # Add total_price field
    op.add_column('stock_consumption_logs',
        sa.Column('total_price', sa.Numeric(12, 2), nullable=True, comment='Обща стойност на изразходваното'))


def downgrade() -> None:
    op.drop_column('stock_consumption_logs', 'total_price')
    op.drop_column('stock_consumption_logs', 'price_per_unit')
