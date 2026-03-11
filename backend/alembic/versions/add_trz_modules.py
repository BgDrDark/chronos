"""add trz modules - night work, overtime, business trips

Revision ID: add_trz_modules
Revises: add_logistics_fleet_modules
Create Date: 2026-03-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_trz_modules'
down_revision: Union[str, Sequence[str], None] = 'add_logistics_fleet_modules'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # ==================== EMPLOYMENT CONTRACT UPDATES ====================
    op.add_column('employment_contracts', sa.Column('night_work_rate', sa.Numeric(precision=4, scale=2), nullable=True, server_default='0.5'))
    op.add_column('employment_contracts', sa.Column('overtime_rate', sa.Numeric(precision=4, scale=2), nullable=True, server_default='1.5'))
    op.add_column('employment_contracts', sa.Column('holiday_rate', sa.Numeric(precision=4, scale=2), nullable=True, server_default='2.0'))
    op.add_column('employment_contracts', sa.Column('work_class', sa.String(length=10), nullable=True))
    op.add_column('employment_contracts', sa.Column('dangerous_work', sa.Boolean(), nullable=True, server_default='false'))
    
    # ==================== PAYROLL PERIOD UPDATES ====================
    op.add_column('payroll_periods', sa.Column('period_type', sa.String(length=20), nullable=True, server_default='monthly'))
    op.add_column('payroll_periods', sa.Column('year_bonus_month', sa.Integer(), nullable=True))
    
    # ==================== PAYSLIP UPDATES ====================
    op.add_column('payslips', sa.Column('night_work_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))
    op.add_column('payslips', sa.Column('trip_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))
    op.add_column('payslips', sa.Column('voucher_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))
    op.add_column('payslips', sa.Column('benefit_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))
    op.add_column('payslips', sa.Column('sick_leave_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))
    
    # ==================== NIGHT WORK BONUS ====================
    op.create_table('night_work_bonuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hours', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_paid', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['period_id'], ['payroll_periods.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_night_work_bonuses_id', 'night_work_bonuses', ['id'])
    op.create_index('ix_night_work_bonuses_user_id', 'night_work_bonuses', ['user_id'])
    op.create_index('ix_night_work_bonuses_date', 'night_work_bonuses', ['date'])
    
    # ==================== OVERTIME WORK ====================
    op.create_table('overtime_works',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hours', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('multiplier', sa.Numeric(precision=4, scale=2), nullable=True, server_default='1.5'),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_paid', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['period_id'], ['payroll_periods.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_overtime_works_id', 'overtime_works', ['id'])
    op.create_index('ix_overtime_works_user_id', 'overtime_works', ['user_id'])
    op.create_index('ix_overtime_works_date', 'overtime_works', ['date'])
    
    # ==================== WORK ON HOLIDAY ====================
    op.create_table('work_on_holidays',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hours', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('multiplier', sa.Numeric(precision=4, scale=2), nullable=True, server_default='2.0'),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_paid', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['period_id'], ['payroll_periods.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_work_on_holidays_id', 'work_on_holidays', ['id'])
    op.create_index('ix_work_on_holidays_user_id', 'work_on_holidays', ['user_id'])
    op.create_index('ix_work_on_holidays_date', 'work_on_holidays', ['date'])
    
    # ==================== BUSINESS TRIP ====================
    op.create_table('business_trips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('destination', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('daily_allowance', sa.Numeric(precision=10, scale=2), nullable=True, server_default='40.00'),
        sa.Column('accommodation', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'),
        sa.Column('transport', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'),
        sa.Column('other_expenses', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_notes', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['period_id'], ['payroll_periods.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_business_trips_id', 'business_trips', ['id'])
    op.create_index('ix_business_trips_user_id', 'business_trips', ['user_id'])
    op.create_index('ix_business_trips_status', 'business_trips', ['status'])
    op.create_index('ix_business_trips_dates', 'business_trips', ['start_date', 'end_date'])
    
    # ==================== WORK EXPERIENCE ====================
    op.create_table('work_experiences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('position', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('years', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('months', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('class_level', sa.String(length=10), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_work_experiences_id', 'work_experiences', ['id'])
    op.create_index('ix_work_experiences_user_id', 'work_experiences', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    
    # Drop work experiences
    op.drop_index('ix_work_experiences_user_id', table_name='work_experiences')
    op.drop_index('ix_work_experiences_id', table_name='work_experiences')
    op.drop_table('work_experiences')
    
    # Drop business trips
    op.drop_index('ix_business_trips_dates', table_name='business_trips')
    op.drop_index('ix_business_trips_status', table_name='business_trips')
    op.drop_index('ix_business_trips_user_id', table_name='business_trips')
    op.drop_index('ix_business_trips_id', table_name='business_trips')
    op.drop_table('business_trips')
    
    # Drop work on holidays
    op.drop_index('ix_work_on_holidays_date', table_name='work_on_holidays')
    op.drop_index('ix_work_on_holidays_user_id', table_name='work_on_holidays')
    op.drop_index('ix_work_on_holidays_id', table_name='work_on_holidays')
    op.drop_table('work_on_holidays')
    
    # Drop overtime works
    op.drop_index('ix_overtime_works_date', table_name='overtime_works')
    op.drop_index('ix_overtime_works_user_id', table_name='overtime_works')
    op.drop_index('ix_overtime_works_id', table_name='overtime_works')
    op.drop_table('overtime_works')
    
    # Drop night work bonuses
    op.drop_index('ix_night_work_bonuses_date', table_name='night_work_bonuses')
    op.drop_index('ix_night_work_bonuses_user_id', table_name='night_work_bonuses')
    op.drop_index('ix_night_work_bonuses_id', table_name='night_work_bonuses')
    op.drop_table('night_work_bonuses')
    
    # Drop payslip columns
    op.drop_column('payslips', 'sick_leave_amount')
    op.drop_column('payslips', 'benefit_amount')
    op.drop_column('payslips', 'voucher_amount')
    op.drop_column('payslips', 'trip_amount')
    op.drop_column('payslips', 'night_work_amount')
    
    # Drop payroll period columns
    op.drop_column('payroll_periods', 'year_bonus_month')
    op.drop_column('payroll_periods', 'period_type')
    
    # Drop employment contract columns
    op.drop_column('employment_contracts', 'dangerous_work')
    op.drop_column('employment_contracts', 'work_class')
    op.drop_column('employment_contracts', 'holiday_rate')
    op.drop_column('employment_contracts', 'overtime_rate')
    op.drop_column('employment_contracts', 'night_work_rate')
