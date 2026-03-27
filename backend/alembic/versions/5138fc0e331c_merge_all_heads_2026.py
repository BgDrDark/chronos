"""merge_all_heads_2026

Revision ID: 5138fc0e331c
Revises: add_st_company_id, add_invoice_item_extended_fields, add_labor_contract_fields, add_price_to_stock_consumption
Create Date: 2026-03-26 10:10:07.119085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5138fc0e331c'
down_revision: Union[str, Sequence[str], None] = ('add_st_company_id', 'add_invoice_item_extended_fields', 'add_labor_contract_fields', 'add_price_to_stock_consumption')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
