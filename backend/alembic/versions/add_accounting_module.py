"""Add accounting module

Revision ID: add_accounting_module
Revises: 3c93f2e81c02
Create Date: 2026-02-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_accounting_module'
down_revision: Union[str, Sequence[str], None] = '3c93f2e81c02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO modules (code, name, is_enabled, description, updated_at) VALUES 
        ('accounting', 'Счетоводство', true, 'Фактури - входящи и изходящи', NOW())
    """)


def downgrade() -> None:
    op.execute("DELETE FROM modules WHERE code = 'accounting'")
