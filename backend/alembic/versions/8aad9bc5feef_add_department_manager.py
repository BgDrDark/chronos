"""add_department_manager

Revision ID: 8aad9bc5feef
Revises: c6f40e20fe4e
Create Date: 2026-02-08 23:58:55.800705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8aad9bc5feef'
down_revision: Union[str, Sequence[str], None] = 'c6f40e20fe4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('departments', sa.Column('manager_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_departments_manager_id_users', 'departments', 'users', ['manager_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_departments_manager_id_users', 'departments', type_='foreignkey')
    op.drop_column('departments', 'manager_id')
