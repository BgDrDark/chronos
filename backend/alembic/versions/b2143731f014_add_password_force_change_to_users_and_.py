"""add_password_force_change_to_users_and_versioning

Revision ID: b2143731f014
Revises: 787f72585657
Create Date: 2026-02-08 23:18:23.028063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2143731f014'
down_revision: Union[str, Sequence[str], None] = '787f72585657'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
