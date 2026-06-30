"""Add card_number/pin_code to User + MFA/interlock/dual-auth to AccessZone (Phase 7)

Revision ID: ba_007
Revises: ba_006
Create Date: 2026-06-29 20:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ba_007"
down_revision: Union[str, None] = "ba_006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("card_number", sa.String(50), nullable=True, unique=True))
    op.add_column("users", sa.Column("pin_code", sa.String(128), nullable=True))
    op.create_index(op.f("ix_users_card_number"), "users", ["card_number"])

    op.add_column("access_zones", sa.Column("required_auth_factors", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("access_zones", sa.Column("interlock_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("access_zones", sa.Column("interlock_timeout", sa.Integer(), nullable=False, server_default="30"))
    op.add_column("access_zones", sa.Column("dual_auth_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("access_zones", sa.Column("dual_auth_timeout", sa.Integer(), nullable=False, server_default="5"))


def downgrade() -> None:
    op.drop_column("access_zones", "dual_auth_timeout")
    op.drop_column("access_zones", "dual_auth_enabled")
    op.drop_column("access_zones", "interlock_timeout")
    op.drop_column("access_zones", "interlock_enabled")
    op.drop_column("access_zones", "required_auth_factors")

    op.drop_index(op.f("ix_users_card_number"), table_name="users")
    op.drop_column("users", "pin_code")
    op.drop_column("users", "card_number")
