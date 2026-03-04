"""Add modules table and initial seeding

Revision ID: 3c93f2e81c02
Revises: configuration_framework
Create Date: 2026-02-08 21:45:36.217161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c93f2e81c02'
down_revision: Union[str, Sequence[str], None] = 'configuration_framework'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_modules_code'), 'modules', ['code'], unique=True)
    op.create_index(op.f('ix_modules_id'), 'modules', ['id'], unique=False)

    # Initial seeding
    op.execute("""
        INSERT INTO modules (code, name, is_enabled, description, updated_at) VALUES 
        ('shifts', 'Смени и работно време', true, 'Управление на работно време, смени и присъствие', NOW()),
        ('salaries', 'Заплати', true, 'Изчисляване на заплати, ТРЗ и договори', NOW()),
        ('kiosk', 'Kiosk терминал', true, 'Управление на физически терминали и QR чекиране', NOW()),
        ('integrations', 'Интеграции', true, 'Google Calendar, Webhooks и външни услуги', NOW())
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_modules_id'), table_name='modules')
    op.drop_index(op.f('ix_modules_code'), table_name='modules')
    op.drop_table('modules')
