"""Add notification_settings table

Revision ID: add_notification_settings
Revises: add_accounting_module
Create Date: 2026-02-14 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_notification_settings'
down_revision: Union[str, Sequence[str], None] = 'add_accounting_module'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notification_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('push_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('email_template', sa.Text(), nullable=True),
        sa.Column('recipients', sa.JSON(), nullable=True),
        sa.Column('interval_minutes', sa.Integer(), nullable=True, server_default='60'),
        sa.Column('enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('last_sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_settings_company_id'), 'notification_settings', ['company_id'])
    op.create_index(op.f('ix_notification_settings_event_type'), 'notification_settings', ['event_type'])


def downgrade() -> None:
    op.drop_index(op.f('ix_notification_settings_event_type'), table_name='notification_settings')
    op.drop_index(op.f('ix_notification_settings_company_id'), table_name='notification_settings')
    op.drop_table('notification_settings')
