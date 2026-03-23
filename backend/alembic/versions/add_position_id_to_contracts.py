"""Add position_id to employment_contracts

Revision ID: add_position_id_to_contracts
Revises: fdf892bc6900
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_position_id_to_contracts'
down_revision = 'fdf892bc6900'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('employment_contracts', sa.Column('position_id', sa.Integer(), sa.ForeignKey('positions.id', ondelete='SET NULL'), nullable=True))

def downgrade() -> None:
    op.drop_column('employment_contracts', 'position_id')
