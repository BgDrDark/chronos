"""add_recipe_workstation_fields

Revision ID: add_recipe_workstation_fields
Revises: ea76c81c7703
Create Date: 2026-02-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_recipe_workstation_fields'
down_revision = 'ea76c81c7703'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add standard_quantity to recipes
    op.add_column('recipes', sa.Column('standard_quantity', sa.Numeric(12, 2), server_default='1.0', nullable=True))
    
    # Add workstation_id to recipe_ingredients
    op.add_column('recipe_ingredients', sa.Column('workstation_id', sa.Integer(), sa.ForeignKey('workstations.id'), nullable=True))
    
    # Add brutto_g and net_g to recipe_steps
    op.add_column('recipe_steps', sa.Column('brutto_g', sa.Numeric(12, 2), nullable=True))
    op.add_column('recipe_steps', sa.Column('net_g', sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('recipe_steps', 'net_g')
    op.drop_column('recipe_steps', 'brutto_g')
    op.drop_column('recipe_ingredients', 'workstation_id')
    op.drop_column('recipes', 'standard_quantity')
