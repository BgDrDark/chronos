"""Add gateway, terminal, printer tables

Revision ID: gateway_tables_001
Revises: 
Create Date: 2026-02-19 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'gateway_tables_001'
down_revision = ('ea76c81c7703', 'merge_accounting_recipe_heads')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Gateways table
    op.create_table(
        'gateways',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('hardware_uuid', sa.String(length=64), nullable=False),
        sa.Column('alias', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('local_hostname', sa.String(length=100), nullable=True),
        sa.Column('terminal_port', sa.Integer(), nullable=True),
        sa.Column('web_port', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('registered_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hardware_uuid'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_gateways_id'), 'gateways', ['id'], unique=False)
    op.create_index(op.f('ix_gateways_name'), 'gateways', ['name'], unique=True)
    
    # Terminals table
    op.create_table(
        'terminals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hardware_uuid', sa.String(length=64), nullable=False),
        sa.Column('device_name', sa.String(length=100), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('device_model', sa.String(length=100), nullable=True),
        sa.Column('os_version', sa.String(length=50), nullable=True),
        sa.Column('gateway_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('total_scans', sa.Integer(), nullable=True),
        sa.Column('alias', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['gateway_id'], ['gateways.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hardware_uuid')
    )
    op.create_index(op.f('ix_terminals_id'), 'terminals', ['id'], unique=False)
    
    # Printers table
    op.create_table(
        'printers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('printer_type', sa.String(length=20), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('protocol', sa.String(length=20), nullable=True),
        sa.Column('windows_share_name', sa.String(length=100), nullable=True),
        sa.Column('manufacturer', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('gateway_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('last_test', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['gateway_id'], ['gateways.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_printers_id'), 'printers', ['id'], unique=False)
    
    # Gateway heartbeats table
    op.create_table(
        'gateway_heartbeats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gateway_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('cpu_usage', sa.Float(), nullable=True),
        sa.Column('memory_usage', sa.Float(), nullable=True),
        sa.Column('terminal_count', sa.Integer(), nullable=True),
        sa.Column('printer_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['gateway_id'], ['gateways.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gateway_heartbeats_id'), 'gateway_heartbeats', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_gateway_heartbeats_id'), table_name='gateway_heartbeats')
    op.drop_table('gateway_heartbeats')
    op.drop_index(op.f('ix_printers_id'), table_name='printers')
    op.drop_table('printers')
    op.drop_index(op.f('ix_terminals_id'), table_name='terminals')
    op.drop_table('terminals')
    op.drop_index(op.f('ix_gateways_name'), table_name='gateways')
    op.drop_index(op.f('ix_gateways_id'), table_name='gateways')
    op.drop_table('gateways')
