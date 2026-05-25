"""Merge accounting and recipe heads

Revision ID: merge_accounting_recipe_heads
Revises: add_saft_accounting_tables, add_recipe_workstation_fields
Create Date: 2026-02-18 12:30:00.000000

"""
from collections.abc import Sequence

revision: str = "merge_accounting_recipe_heads"
down_revision: str | Sequence[str] | None = ("add_saft_accounting_tables", "add_recipe_workstation_fields")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Merge heads"""


def downgrade() -> None:
    """Unmerge heads"""
