"""Add database constraints for data integrity

Revision ID: 002_add_database_constraints
Revises: 001_add_performance_indexes
Create Date: 2026-02-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '002_add_database_constraints'
down_revision = '001_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add database constraints with proper error handling"""
    
    # Unique Constraints
    op.create_unique_constraint(
        'unique_user_date_schedule',
        'work_schedules',
        ['user_id', 'date'],
        schema='public'
    )
    
    op.create_unique_constraint(
        'unique_user_year_balance',
        'leave_balances',
        ['user_id', 'year'],
        schema='public'
    )
    
    op.create_unique_constraint(
        'unique_year_month_work_days',
        'monthly_work_days',
        ['year', 'month'],
        schema='public'
    )
    
    op.create_unique_constraint(
        'unique_shift_name',
        'shifts',
        ['name'],
        schema='public'
    )
    
    op.create_unique_constraint(
        'unique_template_name',
        'schedule_templates',
        ['name'],
        schema='public'
    )
    
    op.create_unique_constraint(
        'unique_key_prefix',
        'api_keys',
        ['key_prefix'],
        schema='public'
    )
    
    # CHECK Constraints for Data Validation
    
    # User table constraints
    op.execute("""
        ALTER TABLE users 
        ADD CONSTRAINT IF NOT EXISTS check_failed_login_attempts 
        CHECK (failed_login_attempts >= 0);
    """)
    
    op.execute("""
        ALTER TABLE users 
        ADD CONSTRAINT IF NOT EXISTS check_email_format 
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    """)
    
    # TimeLog table constraints
    op.execute("""
        ALTER TABLE timelogs 
        ADD CONSTRAINT IF NOT EXISTS check_timelog_dates 
        CHECK (end_time IS NULL OR end_time >= start_time);
    """)
    
    op.execute("""
        ALTER TABLE timelogs 
        ADD CONSTRAINT IF NOT EXISTS check_break_duration 
        CHECK (break_duration_minutes >= 0);
    """)
    
    op.execute("""
        ALTER TABLE timelogs 
        ADD CONSTRAINT IF NOT EXISTS check_timelog_type 
        CHECK (type IN ('work', 'break', 'overtime', 'lunch', 'meeting', 'travel'));
    """)
    
    op.execute("""
        ALTER TABLE timelogs 
        ADD CONSTRAINT IF NOT EXISTS check_coordinates 
        CHECK (
            (latitude IS NULL AND longitude IS NULL) OR 
            (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)
        );
    """)
    
    # Payroll table constraints
    op.execute("""
        ALTER TABLE payrolls 
        ADD CONSTRAINT IF NOT EXISTS check_hourly_rate_positive 
        CHECK (hourly_rate >= 0);
    """)
    
    op.execute("""
        ALTER TABLE payrolls 
        ADD CONSTRAINT IF NOT EXISTS check_monthly_salary_positive 
        CHECK (monthly_salary >= 0);
    """)
    
    op.execute("""
        ALTER TABLE payrolls 
        ADD CONSTRAINT IF NOT EXISTS check_overtime_multiplier 
        CHECK (overtime_multiplier >= 1);
    """)
    
    op.execute("""
        ALTER TABLE payrolls 
        ADD CONSTRAINT IF NOT EXISTS check_standard_hours 
        CHECK (standard_hours_per_day > 0 AND standard_hours_per_day <= 24);
    """)
    
    op.execute("""
        ALTER TABLE payrolls 
        ADD CONSTRAINT IF NOT EXISTS check_tax_percentage 
        CHECK (tax_percent >= 0 AND tax_percent <= 100);
    """)
    
    op.execute("""
        ALTER TABLE payrolls 
        ADD CONSTRAINT IF NOT EXISTS check_insurance_percentage 
        CHECK (health_insurance_percent >= 0 AND health_insurance_percent <= 100);
    """)
    
    # Payslip table constraints
    op.execute("""
        ALTER TABLE payslips 
        ADD CONSTRAINT IF NOT EXISTS check_payslip_periods 
        CHECK (period_end >= period_start);
    """)
    
    op.execute("""
        ALTER TABLE payslips 
        ADD CONSTRAINT IF NOT EXISTS check_payslip_hours 
        CHECK (
            total_regular_hours >= 0 AND 
            total_overtime_hours >= 0 AND 
            sick_days >= 0 AND 
            leave_days >= 0
        );
    """)
    
    op.execute("""
        ALTER TABLE payslips 
        ADD CONSTRAINT IF NOT EXISTS check_payslip_amounts 
        CHECK (
            regular_amount >= 0 AND 
            overtime_amount >= 0 AND 
            bonus_amount >= 0 AND 
            tax_amount >= 0 AND 
            insurance_amount >= 0 AND 
            total_amount >= 0
        );
    """)
    
    # LeaveRequest table constraints
    op.execute("""
        ALTER TABLE leave_requests 
        ADD CONSTRAINT IF NOT EXISTS check_leave_request_dates 
        CHECK (end_date >= start_date);
    """)
    
    op.execute("""
        ALTER TABLE leave_requests 
        ADD CONSTRAINT IF NOT EXISTS check_leave_request_type 
        CHECK (leave_type IN ('paid_leave', 'sick_leave', 'unpaid_leave', 'maternity_leave', 'paternity_leave'));
    """)
    
    op.execute("""
        ALTER TABLE leave_requests 
        ADD CONSTRAINT IF NOT EXISTS check_leave_request_status 
        CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled'));
    """)
    
    # LeaveBalance table constraints
    op.execute("""
        ALTER TABLE leave_balances 
        ADD CONSTRAINT IF NOT EXISTS check_leave_balance_days 
        CHECK (
            total_days >= 0 AND 
            used_days >= 0 AND 
            used_days <= total_days
        );
    """)
    
    op.execute("""
        ALTER TABLE leave_balances 
        ADD CONSTRAINT IF NOT EXISTS check_balance_year 
        CHECK (year BETWEEN 2000 AND 2100);
    """)
    
    # Bonus table constraints
    op.execute("""
        ALTER TABLE bonuses 
        ADD CONSTRAINT IF NOT EXISTS check_bonus_amount_positive 
        CHECK (amount > 0);
    """)
    
    # UserSession table constraints
    op.execute("""
        ALTER TABLE user_sessions 
        ADD CONSTRAINT IF NOT EXISTS check_session_expiry 
        CHECK (expires_at > created_at);
    """)
    
    op.execute("""
        ALTER TABLE user_sessions 
        ADD CONSTRAINT IF NOT EXISTS check_device_type 
        CHECK (device_type IN ('desktop', 'mobile', 'tablet', 'api', 'unknown'));
    """)
    
    # Shift table constraints
    op.execute("""
        ALTER TABLE shifts 
        ADD CONSTRAINT IF NOT EXISTS check_shift_times 
        CHECK (end_time != start_time);
    """)
    
    op.execute("""
        ALTER TABLE shifts 
        ADD CONSTRAINT IF NOT EXISTS check_shift_tolerance 
        CHECK (tolerance_minutes >= 0);
    """)
    
    op.execute("""
        ALTER TABLE shifts 
        ADD CONSTRAINT IF NOT EXISTS check_break_duration 
        CHECK (break_duration_minutes >= 0);
    """)
    
    op.execute("""
        ALTER TABLE shifts 
        ADD CONSTRAINT IF NOT EXISTS check_pay_multiplier 
        CHECK (pay_multiplier > 0);
    """)
    
    op.execute("""
        ALTER TABLE shifts 
        ADD CONSTRAINT IF NOT EXISTS check_shift_type 
        CHECK (shift_type IN ('regular', 'sick_leave', 'paid_leave', 'unpaid_leave', 'day_off', 'holiday'));
    """)
    
    # MonthlyWorkDays table constraints
    op.execute("""
        ALTER TABLE monthly_work_days 
        ADD CONSTRAINT IF NOT EXISTS check_month_range 
        CHECK (month BETWEEN 1 AND 12);
    """)
    
    op.execute("""
        ALTER TABLE monthly_work_days 
        ADD CONSTRAINT IF NOT EXISTS check_year_range 
        CHECK (year BETWEEN 2000 AND 2100);
    """)
    
    op.execute("""
        ALTER TABLE monthly_work_days 
        ADD CONSTRAINT IF NOT EXISTS check_days_count 
        CHECK (days_count BETWEEN 0 AND 31);
    """)
    
    # Notification table constraints
    op.execute("""
        ALTER TABLE notifications 
        ADD CONSTRAINT IF NOT EXISTS check_message_not_empty 
        CHECK (LENGTH(TRIM(message)) > 0);
    """)
    
    # ShiftSwapRequest table constraints
    op.execute("""
        ALTER TABLE shift_swap_requests 
        ADD CONSTRAINT IF NOT EXISTS check_swap_status 
        CHECK (status IN ('pending', 'accepted', 'rejected', 'approved', 'cancelled'));
    """)
    
    op.execute("""
        ALTER TABLE shift_swap_requests 
        ADD CONSTRAINT IF NOT EXISTS check_different_users 
        CHECK (requestor_id != target_user_id);
    """)

def downgrade() -> None:
    """Remove database constraints"""
    
    # List of constraints to drop
    constraints_to_drop = [
        # Unique constraints
        'unique_user_date_schedule',
        'unique_user_year_balance',
        'unique_year_month_work_days',
        'unique_shift_name',
        'unique_template_name',
        'unique_key_prefix',
        
        # CHECK constraints
        'check_failed_login_attempts',
        'check_email_format',
        'check_timelog_dates',
        'check_break_duration',
        'check_timelog_type',
        'check_coordinates',
        'check_hourly_rate_positive',
        'check_monthly_salary_positive',
        'check_overtime_multiplier',
        'check_standard_hours',
        'check_tax_percentage',
        'check_insurance_percentage',
        'check_payslip_periods',
        'check_payslip_hours',
        'check_payslip_amounts',
        'check_leave_request_dates',
        'check_leave_request_type',
        'check_leave_request_status',
        'check_leave_balance_days',
        'check_balance_year',
        'check_bonus_amount_positive',
        'check_session_expiry',
        'check_device_type',
        'check_shift_times',
        'check_shift_tolerance',
        'check_break_duration',
        'check_pay_multiplier',
        'check_shift_type',
        'check_month_range',
        'check_year_range',
        'check_days_count',
        'check_message_not_empty',
        'check_swap_status',
        'check_different_users',
    ]
    
    # Drop all constraints
    for constraint_name in constraints_to_drop:
        try:
            op.execute(f"ALTER TABLE IF EXISTS public DROP CONSTRAINT IF EXISTS {constraint_name};")
        except Exception:
            # Some constraints might be on specific tables, handle individually
            pass
    
    # Handle table-specific constraint drops
    try:
        op.drop_constraint('unique_user_date_schedule', 'work_schedules', type_='unique')
    except Exception:
        pass
    
    try:
        op.drop_constraint('unique_user_year_balance', 'leave_balances', type_='unique')
    except Exception:
        pass
    
    try:
        op.drop_constraint('unique_year_month_work_days', 'monthly_work_days', type_='unique')
    except Exception:
        pass
    
    try:
        op.drop_constraint('unique_shift_name', 'shifts', type_='unique')
    except Exception:
        pass
    
    try:
        op.drop_constraint('unique_template_name', 'schedule_templates', type_='unique')
    except Exception:
        pass
    
    try:
        op.drop_constraint('unique_key_prefix', 'api_keys', type_='unique')
    except Exception:
        pass
