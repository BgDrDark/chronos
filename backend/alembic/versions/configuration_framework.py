"""Add Configuration Framework

Revision ID: configuration_framework
Revises: enhanced_payroll_system
Create Date: 2026-02-05 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'configuration_framework'
down_revision = 'enhanced_payroll_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create configuration_categories table
    op.create_table('configuration_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_configuration_categories_id'), 'configuration_categories', ['id'], unique=False)
    op.create_index(op.f('ix_configuration_categories_name'), 'configuration_categories', ['name'], unique=True)
    
    # Create configuration_fields table
    op.create_table('configuration_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('field_type', sa.String(length=50), nullable=False),
        sa.Column('validation_rules', sa.JSON(), nullable=True),
        sa.Column('default_value', sa.String(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['configuration_categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_configuration_fields_id'), 'configuration_fields', ['id'], unique=False)
    
    # Create company_configurations table
    op.create_table('company_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['configuration_fields.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'field_id')
    )
    op.create_index(op.f('ix_company_configurations_id'), 'company_configurations', ['id'], unique=False)


def downgrade() -> None:
    # Drop Configuration Framework tables
    op.drop_index(op.f('ix_company_configurations_id'), table_name='company_configurations')
    op.drop_table('company_configurations')
    
    op.drop_index(op.f('ix_configuration_fields_id'), table_name='configuration_fields')
    op.drop_table('configuration_fields')
    
    op.drop_index(op.f('ix_configuration_categories_name'), table_name='configuration_categories')
    op.drop_index(op.f('ix_configuration_categories_id'), table_name='configuration_categories')
    op.drop_table('configuration_categories')