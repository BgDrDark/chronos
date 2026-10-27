"""widen users.pin_sha256 for salted PBKDF2 hashes

Revision ID: ba_012
Revises: ba_011
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ba_012"
down_revision: str | Sequence[str] | None = "ba_011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "pin_sha256",
        type_=sa.String(length=255),
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "pin_sha256",
        type_=sa.String(length=64),
        existing_type=sa.String(length=255),
        existing_nullable=True,
    )
