"""Add terminal_mode to access_doors

Revision ID: add_terminal_mode_to_doors
Revises: add_invoice_accounting_fields
Create Date: 2026-03-04 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_terminal_mode_to_doors'
down_revision: Union[str, Sequence[str], None] = 'add_invoice_accounting_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add terminal_mode column to access_doors table."""
    op.add_column(
        'access_doors',
        sa.Column('terminal_mode', sa.String(length=20), nullable=True, server_default='access')
    )


def downgrade() -> None:
    """Remove terminal_mode column from access_doors table."""
    op.drop_column('access_doors', 'terminal_mode')
