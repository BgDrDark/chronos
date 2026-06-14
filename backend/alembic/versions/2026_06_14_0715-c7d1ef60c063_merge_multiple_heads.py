"""merge multiple heads

Revision ID: c7d1ef60c063
Revises: doc_001, idx_audit_logs_001, shift_overnight_audit
Create Date: 2026-06-14 07:15:59.766959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d1ef60c063'
down_revision: Union[str, Sequence[str], None] = ('doc_001', 'idx_audit_logs_001', 'shift_overnight_audit')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
