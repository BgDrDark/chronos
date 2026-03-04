"""Add accounting fields to invoices

Revision ID: add_invoice_accounting_fields
Revises: ea76c81c7703
Create Date: 2026-03-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_invoice_accounting_fields'
down_revision: Union[str, Sequence[str], None] = 'ea76c81c7703'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add accounting fields to invoices table."""
    op.add_column('invoices', sa.Column('is_accounted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('invoices', sa.Column('accounted_at', sa.DateTime(), nullable=True))
    op.add_column('invoices', sa.Column('accounted_by_id', sa.Integer(), nullable=True))
    op.add_column('invoices', sa.Column('accounting_date', sa.Date(), nullable=True))
    op.add_column('invoices', sa.Column('entry_number', sa.String(length=50), nullable=True))
    op.add_column('invoices', sa.Column('contra_account_code', sa.String(length=20), nullable=True, server_default='401'))
    op.add_column('invoices', sa.Column('payment_type', sa.String(length=20), nullable=True))
    
    # Add foreign key for accounted_by_id
    op.create_foreign_key(
        'fk_invoices_accounted_by_id',
        'invoices', 'users',
        ['accounted_by_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Remove accounting fields from invoices table."""
    op.drop_constraint('fk_invoices_accounted_by_id', 'invoices', type_='foreignkey')
    op.drop_column('invoices', 'payment_type')
    op.drop_column('invoices', 'contra_account_code')
    op.drop_column('invoices', 'entry_number')
    op.drop_column('invoices', 'accounting_date')
    op.drop_column('invoices', 'accounted_by_id')
    op.drop_column('invoices', 'accounted_at')
    op.drop_column('invoices', 'is_accounted')
