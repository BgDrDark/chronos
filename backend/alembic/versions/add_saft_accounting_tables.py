"""Add accounting module tables for SAF-T compliance

Revision ID: add_saft_accounting_tables
Revises: f0a9e3381fd5
Create Date: 2026-02-18 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'add_saft_accounting_tables'
down_revision: Union[str, Sequence[str], None] = 'f0a9e3381fd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add type field to invoices for proforma support
    op.execute("""
        ALTER TABLE invoices 
        ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'outgoing'
    """)
    
    # Invoice Corrections table
    op.create_table(
        'invoice_corrections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('original_invoice_id', sa.Integer(), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('correction_type', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('amount_diff', sa.Numeric(12, 2), default=0),
        sa.Column('vat_diff', sa.Numeric(12, 2), default=0),
        sa.Column('correction_date', sa.Date(), nullable=False),
        sa.Column('new_invoice_id', sa.Integer(), sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # Cash Receipts table
    op.create_table(
        'cash_receipts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('receipt_number', sa.String(50), unique=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('payment_type', sa.String(20), default='cash'),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('vat_amount', sa.Numeric(12, 2), default=0),
        sa.Column('items_json', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # Bank Accounts table
    op.create_table(
        'bank_accounts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('iban', sa.String(34), unique=True, nullable=False),
        sa.Column('bic', sa.String(11), nullable=True),
        sa.Column('bank_name', sa.String(255), nullable=False),
        sa.Column('account_type', sa.String(20), default='current'),
        sa.Column('currency', sa.String(3), default='BGN'),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # Bank Transactions table
    op.create_table(
        'bank_transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('bank_account_id', sa.Integer(), sa.ForeignKey('bank_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reference', sa.String(100), nullable=True),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('matched', sa.Boolean(), default=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # Accounts (Chart of Accounts) table
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('opening_balance', sa.Numeric(12, 2), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # Accounting Entries table
    op.create_table(
        'accounting_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('entry_number', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('debit_account_id', sa.Integer(), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('credit_account_id', sa.Integer(), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('vat_amount', sa.Numeric(12, 2), default=0),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('bank_transaction_id', sa.Integer(), sa.ForeignKey('bank_transactions.id'), nullable=True),
        sa.Column('cash_journal_id', sa.Integer(), sa.ForeignKey('cash_journal_entries.id'), nullable=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # VAT Registers table
    op.create_table(
        'vat_registers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_month', sa.Integer(), nullable=False),
        sa.Column('period_year', sa.Integer(), nullable=False),
        sa.Column('vat_collected_20', sa.Numeric(12, 2), default=0),
        sa.Column('vat_collected_9', sa.Numeric(12, 2), default=0),
        sa.Column('vat_collected_0', sa.Numeric(12, 2), default=0),
        sa.Column('vat_paid_20', sa.Numeric(12, 2), default=0),
        sa.Column('vat_paid_9', sa.Numeric(12, 2), default=0),
        sa.Column('vat_paid_0', sa.Numeric(12, 2), default=0),
        sa.Column('vat_adjustment', sa.Numeric(12, 2), default=0),
        sa.Column('vat_due', sa.Numeric(12, 2), default=0),
        sa.Column('vat_credit', sa.Numeric(12, 2), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )
    
    # Add indexes for better performance
    op.create_index('ix_invoice_corrections_company', 'invoice_corrections', ['company_id'])
    op.create_index('ix_cash_receipts_company', 'cash_receipts', ['company_id'])
    op.create_index('ix_bank_accounts_company', 'bank_accounts', ['company_id'])
    op.create_index('ix_bank_transactions_company', 'bank_transactions', ['company_id'])
    op.create_index('ix_accounts_company', 'accounts', ['company_id'])
    op.create_index('ix_accounting_entries_company', 'accounting_entries', ['company_id'])
    op.create_index('ix_vat_registers_company_period', 'vat_registers', ['company_id', 'period_year', 'period_month'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_vat_registers_company_period', 'vat_registers')
    op.drop_index('ix_accounting_entries_company', 'accounting_entries')
    op.drop_index('ix_accounts_company', 'accounts')
    op.drop_index('ix_bank_transactions_company', 'bank_transactions')
    op.drop_index('ix_bank_accounts_company', 'bank_accounts')
    op.drop_index('ix_cash_receipts_company', 'cash_receipts')
    op.drop_index('ix_invoice_corrections_company', 'invoice_corrections')
    
    # Drop tables
    op.drop_table('vat_registers')
    op.drop_table('accounting_entries')
    op.drop_table('accounts')
    op.drop_table('bank_transactions')
    op.drop_table('bank_accounts')
    op.drop_table('cash_receipts')
    op.drop_table('invoice_corrections')
