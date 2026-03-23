"""Add invoices table

Revision ID: add_invoices_table
Revises: add_saft_accounting_tables
Create Date: 2026-02-18 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_invoices_table'
down_revision: Union[str, Sequence[str], None] = 'f0a9e3381fd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('number', sa.String(50), unique=True, nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('document_type', sa.String(50), server_default='ФАКТУРА'),
        sa.Column('griff', sa.String(20), server_default='ОРИГИНАЛ'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=True),
        sa.Column('batch_id', sa.Integer(), nullable=True),
        sa.Column('client_name', sa.String(255), nullable=True),
        sa.Column('client_eik', sa.String(20), nullable=True),
        sa.Column('client_address', sa.Text(), nullable=True),
        sa.Column('subtotal', sa.Numeric(12, 2), server_default='0'),
        sa.Column('discount_percent', sa.Numeric(5, 2), server_default='0'),
        sa.Column('discount_amount', sa.Numeric(12, 2), server_default='0'),
        sa.Column('vat_rate', sa.Numeric(5, 2), server_default='20.0'),
        sa.Column('vat_amount', sa.Numeric(12, 2), server_default='0'),
        sa.Column('total', sa.Numeric(12, 2), server_default='0'),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('delivery_method', sa.String(50), server_default='Доставка до адрес'),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )
    op.create_index(op.f('ix_invoices_id'), 'invoices', ['id'], unique=False)
    op.create_index(op.f('ix_invoices_number'), 'invoices', ['number'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_invoices_number'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_id'), table_name='invoices')
    op.drop_table('invoices')
