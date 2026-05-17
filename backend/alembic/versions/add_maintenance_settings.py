"""Add maintenance_settings table

Revision ID: add_maintenance_settings
Revises: shift_company_schedule_uc
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_maintenance_settings'
down_revision = 'shift_company_schedule_uc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('maintenance_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False, server_default=''),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_maintenance_settings_id'), 'maintenance_settings', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_maintenance_settings_id'), table_name='maintenance_settings')
    op.drop_table('maintenance_settings')
