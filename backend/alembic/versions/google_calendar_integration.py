"""Add Google Calendar integration

Revision ID: google_calendar_integration
Revises: rbac_001
Create Date: 2026-02-05 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'google_calendar_integration'
down_revision = 'rbac_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create google_calendar_accounts table
    op.create_table('google_calendar_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('google_user_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('access_token', sa.String(), nullable=True),
        sa.Column('refresh_token', sa.String(), nullable=False),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'google_user_id')
    )
    op.create_index(op.f('ix_google_calendar_accounts_id'), 'google_calendar_accounts', ['id'], unique=False)
    op.create_index('ix_google_calendar_accounts_google_user_id', 'google_calendar_accounts', ['google_user_id'], unique=False)
    
    # Create google_calendar_sync_settings table
    op.create_table('google_calendar_sync_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('calendar_id', sa.String(length=255), nullable=False),
        sa.Column('sync_work_schedules', sa.Boolean(), nullable=True),
        sa.Column('sync_time_logs', sa.Boolean(), nullable=True),
        sa.Column('sync_leave_requests', sa.Boolean(), nullable=True),
        sa.Column('sync_public_holidays', sa.Boolean(), nullable=True),
        sa.Column('sync_direction', sa.String(length=20), nullable=True),
        sa.Column('sync_frequency_minutes', sa.Integer(), nullable=True),
        sa.Column('privacy_level', sa.String(length=20), nullable=True),
        sa.Column('default_event_visibility', sa.String(length=20), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['google_calendar_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_google_calendar_sync_settings_id'), 'google_calendar_sync_settings', ['id'], unique=False)
    
    # Create google_calendar_events table
    op.create_table('google_calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('google_event_id', sa.String(length=255), nullable=False),
        sa.Column('google_calendar_id', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('is_all_day', sa.Boolean(), nullable=True),
        sa.Column('google_updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(length=20), nullable=True),
        sa.Column('sync_error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['google_calendar_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'google_event_id')
    )
    op.create_index(op.f('ix_google_calendar_events_id'), 'google_calendar_events', ['id'], unique=False)
    op.create_index('ix_google_calendar_events_google_event_id', 'google_calendar_events', ['google_event_id'], unique=False)
    op.create_index('ix_google_calendar_events_lookup', 'google_calendar_events', ['account_id', 'source_type', 'source_id'], unique=False)
    
    # Create google_sync_log table
    op.create_table('google_sync_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(length=50), nullable=False),
        sa.Column('events_processed', sa.Integer(), nullable=True),
        sa.Column('events_created', sa.Integer(), nullable=True),
        sa.Column('events_updated', sa.Integer(), nullable=True),
        sa.Column('events_deleted', sa.Integer(), nullable=True),
        sa.Column('errors_count', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('error_details', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['google_calendar_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_google_sync_log_id'), 'google_sync_log', ['id'], unique=False)


def downgrade() -> None:
    # Drop Google Calendar tables
    op.drop_index(op.f('ix_google_sync_log_id'), table_name='google_sync_log')
    op.drop_table('google_sync_log')
    
    op.drop_index('ix_google_calendar_events_lookup', table_name='google_calendar_events')
    op.drop_index('ix_google_calendar_events_google_event_id', table_name='google_calendar_events')
    op.drop_index(op.f('ix_google_calendar_events_id'), table_name='google_calendar_events')
    op.drop_table('google_calendar_events')
    
    op.drop_index(op.f('ix_google_calendar_sync_settings_id'), table_name='google_calendar_sync_settings')
    op.drop_table('google_calendar_sync_settings')
    
    op.drop_index('ix_google_calendar_accounts_google_user_id', table_name='google_calendar_accounts')
    op.drop_index(op.f('ix_google_calendar_accounts_id'), table_name='google_calendar_accounts')
    op.drop_table('google_calendar_accounts')