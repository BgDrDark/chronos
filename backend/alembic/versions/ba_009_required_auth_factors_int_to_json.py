"""required_auth_factors: Integer -> JSON

Revision ID: ba_009
Revises: ba_008
Create Date: 2026-06-30 06:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ba_009"
down_revision: Union[str, None] = "ba_008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("access_zones", "required_auth_factors")
    op.add_column(
        "access_zones",
        sa.Column("required_auth_factors", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("access_zones", "required_auth_factors")
    op.add_column(
        "access_zones",
        sa.Column("required_auth_factors", sa.Integer(), nullable=False, server_default="1"),
    )
