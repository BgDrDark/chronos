"""Add documentation tables

Revision ID: doc_001
Revises: 5138fc0e331c
Create Date: 2026-06-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'doc_001'
down_revision = '5138fc0e331c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Documentation categories
    op.create_table(
        'documentation_categories',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('icon', sa.String(50), server_default='folder'),
        sa.Column('order', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Documentation articles
    op.create_table(
        'documentation_articles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('documentation_categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), server_default=''),
        sa.Column('order', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_index('ix_documentation_articles_category_id', 'documentation_articles', ['category_id'])


def downgrade() -> None:
    op.drop_index('ix_documentation_articles_category_id', table_name='documentation_articles')
    op.drop_table('documentation_articles')
    op.drop_table('documentation_categories')
