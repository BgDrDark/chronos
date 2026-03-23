"""Merge accounting and recipe heads

Revision ID: merge_accounting_recipe_heads
Revises: add_saft_accounting_tables, add_recipe_workstation_fields
Create Date: 2026-02-18 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'merge_accounting_recipe_heads'
down_revision: Union[str, Sequence[str], None] = ('add_saft_accounting_tables', 'add_recipe_workstation_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge heads"""
    pass


def downgrade() -> None:
    """Unmerge heads"""
    pass
