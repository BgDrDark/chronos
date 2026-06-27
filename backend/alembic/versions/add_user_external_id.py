"""add external_id to users for gateway access control sync

Revision ID: add_user_external_id
Revises: add_kiosk_rate_limit
Create Date: 2026-06-27 06:50:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "add_user_external_id"
down_revision: Union[str, None] = "add_kiosk_rate_limit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("external_id", sa.Integer(), unique=True, nullable=True))

    conn = op.get_bind()
    rows = conn.execute(text("SELECT id, email FROM users WHERE external_id IS NULL")).fetchall()
    for row in rows:
        eid = int(uuid.uuid5(uuid.NAMESPACE_DNS, f"scim:{row.email}").int) & 0x7FFFFFFF
        conn.execute(
            text("UPDATE users SET external_id = :eid WHERE id = :uid"),
            {"eid": eid, "uid": row.id},
        )

    op.create_index("ix_users_external_id", "users", ["external_id"])


def downgrade() -> None:
    op.drop_index("ix_users_external_id", table_name="users")
    op.drop_column("users", "external_id")
