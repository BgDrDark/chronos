"""Add invoice item extended fields

Revision ID: add_invoice_item_extended_fields
Revises: add_invoices_table
Create Date: 2026-03-23 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_invoice_item_extended_fields'
down_revision: Union[str, Sequence[str], None] = 'add_invoices_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('invoice_items', sa.Column('unit_price_with_vat', sa.Numeric(12, 2), nullable=True))
    op.add_column('invoice_items', sa.Column('expiration_date', sa.Date(), nullable=True))
    op.add_column('invoice_items', sa.Column('batch_number', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('invoice_items', 'batch_number')
    op.drop_column('invoice_items', 'expiration_date')
    op.drop_column('invoice_items', 'unit_price_with_vat')
