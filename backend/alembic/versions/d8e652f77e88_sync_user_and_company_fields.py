"""sync_user_and_company_fields

Revision ID: d8e652f77e88
Revises: fdf2d575c873
Create Date: 2026-02-09 00:48:19.470501

"""
import contextlib
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8e652f77e88"
down_revision: str | Sequence[str] | None = "fdf2d575c873"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Handle company unique constraints
    with contextlib.suppress(BaseException):
        op.drop_index("ix_companies_bulstat", table_name="companies")
    with contextlib.suppress(BaseException):
        op.drop_index("ix_companies_eik", table_name="companies")
    with contextlib.suppress(BaseException):
        op.drop_index("ix_companies_vat_number", table_name="companies")

    with contextlib.suppress(BaseException):
        op.create_unique_constraint("uq_companies_bulstat", "companies", ["bulstat"])
    with contextlib.suppress(BaseException):
        op.create_unique_constraint("uq_companies_vat_number", "companies", ["vat_number"])
    with contextlib.suppress(BaseException):
        op.create_unique_constraint("uq_companies_eik", "companies", ["eik"])

    # Add password_force_change if missing
    # We use a try-except block to make it idempotent
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "password_force_change" not in columns:
        op.add_column("users", sa.Column("password_force_change", sa.Boolean(), nullable=True, server_default="false"))

    if "username" not in columns:
        op.add_column("users", sa.Column("username", sa.String(), nullable=True))
        op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "username")
    op.drop_column("users", "password_force_change")
    op.drop_constraint("uq_companies_eik", "companies", type_="unique")
    op.drop_constraint("uq_companies_vat_number", "companies", type_="unique")
    op.drop_constraint("uq_companies_bulstat", "companies", type_="unique")
    op.create_index("ix_companies_vat_number", "companies", ["vat_number"], unique=True)
    op.create_index("ix_companies_eik", "companies", ["eik"], unique=True)
    op.create_index("ix_companies_bulstat", "companies", ["bulstat"], unique=True)
