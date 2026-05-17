"""Add overnight to shifts + schedule_audit_logs table

Revision ID: shift_overnight_audit
Revises: add_update_schedule
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa


revision = 'shift_overnight_audit'
down_revision = 'add_update_schedule'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add overnight column to shifts
    op.add_column('shifts', sa.Column('overnight', sa.Boolean(), nullable=True, server_default='false'))

    # Create schedule_audit_logs table
    op.create_table('schedule_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=True),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_audit_logs_id'), 'schedule_audit_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_schedule_audit_logs_id'), table_name='schedule_audit_logs')
    op.drop_table('schedule_audit_logs')
    op.drop_column('shifts', 'overnight')
