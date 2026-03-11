"""add trz global settings

Revision ID: add_trz_settings
Revises: add_trz_modules
Create Date: 2026-03-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_trz_settings'
down_revision: Union[str, Sequence[str], None] = 'add_trz_modules'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add TRZ feature toggle settings."""
    
    # ТРЗ настройки - чекбоксове за включване/изключване
    trz_settings = [
        ('trz_night_work_enabled', 'false'),
        ('trz_overtime_enabled', 'false'),
        ('trz_holiday_work_enabled', 'false'),
        ('trz_business_trips_enabled', 'false'),
        ('trz_work_experience_enabled', 'false'),
        ('trz_food_vouchers_enabled', 'false'),
        ('trz_transport_allowance_enabled', 'false'),
        ('trz_company_benefits_enabled', 'false'),
        # Ставки по подразбиране
        ('trz_default_night_rate', '0.5'),  # 50%
        ('trz_default_overtime_rate', '1.5'),  # 50% надбавка
        ('trz_default_holiday_rate', '2.0'),  # 100% надбавка
        ('trz_default_daily_allowance', '40.00'),  # 40 лв дневни
    ]
    
    for key, value in trz_settings:
        op.execute(f"INSERT INTO global_settings (key, value) VALUES ('{key}', '{value}') ON CONFLICT (key) DO NOTHING")


def downgrade() -> None:
    """Remove TRZ settings."""
    
    settings_keys = [
        'trz_night_work_enabled',
        'trz_overtime_enabled',
        'trz_holiday_work_enabled',
        'trz_business_trips_enabled',
        'trz_work_experience_enabled',
        'trz_food_vouchers_enabled',
        'trz_transport_allowance_enabled',
        'trz_company_benefits_enabled',
        'trz_default_night_rate',
        'trz_default_overtime_rate',
        'trz_default_holiday_rate',
        'trz_default_daily_allowance',
    ]
    
    for key in settings_keys:
        op.execute(f"DELETE FROM global_settings WHERE key = '{key}'")
