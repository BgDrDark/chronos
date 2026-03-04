"""Add performance indexes

Revision ID: 001_add_performance_indexes
Revises: 
Create Date: 2026-02-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '001_add_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes using CONCURRENTLY for production safety"""
    
    # TimeLog Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_user_start_time 
        ON timelogs (user_id, start_time DESC);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_user_end_time 
        ON timelogs (user_id, end_time DESC) WHERE end_time IS NULL;
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_user_date_range 
        ON timelogs (user_id, date_trunc('day', start_time), start_time);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_manual_type 
        ON timelogs (is_manual, type, start_time DESC);
    """)
    
    # WorkSchedule Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_schedules_user_date 
        ON work_schedules (user_id, date);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_schedules_date_shift 
        ON work_schedules (date, shift_id);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_schedules_user_date_shift 
        ON work_schedules (user_id, date, shift_id);
    """)
    
    # LeaveRequest Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_status_dates 
        ON leave_requests (status, start_date, end_date);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_user_dates 
        ON leave_requests (user_id, start_date, end_date);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_date_overlap 
        ON leave_requests (user_id, status, start_date, end_date);
    """)
    
    # Payslip Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payslips_user_period 
        ON payslips (user_id, period_start DESC, period_end DESC);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payslips_period_user 
        ON payslips (period_start DESC, period_end DESC, user_id);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payslips_generated_amount 
        ON payslips (generated_at DESC, total_amount);
    """)
    
    # User Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_company 
        ON users (is_active, company_id);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_active 
        ON users (role_id, is_active);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active 
        ON users (email, is_active);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_locked_until 
        ON users (locked_until) WHERE locked_until IS NOT NULL;
    """)
    
    # UserSession Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_user_active 
        ON user_sessions (user_id, is_active, expires_at DESC);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_expires 
        ON user_sessions (expires_at) WHERE is_active = true;
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_refresh_token 
        ON user_sessions (refresh_token_jti, is_active);
    """)
    
    # Payroll Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payrolls_user_position 
        ON payrolls (user_id, position_id);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payrolls_currency_rate 
        ON payrolls (currency, hourly_rate, monthly_salary DESC);
    """)
    
    # Bonus Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bonuses_user_date 
        ON bonuses (user_id, date DESC);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bonuses_date_amount 
        ON bonuses (date DESC, amount DESC);
    """)
    
    # AuditLog Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_action 
        ON audit_logs (created_at DESC, action);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_created 
        ON audit_logs (user_id, created_at DESC);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_target_created 
        ON audit_logs (target_type, target_id, created_at DESC);
    """)
    
    # Notification Table Indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_user_read_created 
        ON notifications (user_id, is_read, created_at DESC);
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_unread 
        ON notifications (user_id, created_at DESC) WHERE is_read = false;
    """)
    
    # Partial Indexes for Common Query Patterns
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_active 
        ON timelogs (user_id, start_time DESC) WHERE end_time IS NULL;
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_schedules_today 
        ON work_schedules (user_id, shift_id) WHERE date = CURRENT_DATE;
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_pending 
        ON leave_requests (user_id, start_date) WHERE status = 'pending';
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_approved 
        ON leave_requests (user_id, start_date, end_date) WHERE status = 'approved';
    """)

def downgrade() -> None:
    """Remove performance indexes"""
    
    # List of all indexes to drop
    indexes_to_drop = [
        # TimeLog
        'idx_timelogs_user_start_time',
        'idx_timelogs_user_end_time', 
        'idx_timelogs_user_date_range',
        'idx_timelogs_manual_type',
        'idx_timelogs_active',
        
        # WorkSchedule
        'idx_work_schedules_user_date',
        'idx_work_schedules_date_shift',
        'idx_work_schedules_user_date_shift',
        'idx_work_schedules_today',
        
        # LeaveRequest
        'idx_leave_requests_status_dates',
        'idx_leave_requests_user_dates',
        'idx_leave_requests_date_overlap',
        'idx_leave_requests_pending',
        'idx_leave_requests_approved',
        
        # Payslip
        'idx_payslips_user_period',
        'idx_payslips_period_user',
        'idx_payslips_generated_amount',
        
        # User
        'idx_users_active_company',
        'idx_users_role_active',
        'idx_users_email_active',
        'idx_users_locked_until',
        
        # UserSession
        'idx_user_sessions_user_active',
        'idx_user_sessions_expires',
        'idx_user_sessions_refresh_token',
        
        # Payroll
        'idx_payrolls_user_position',
        'idx_payrolls_currency_rate',
        
        # Bonus
        'idx_bonuses_user_date',
        'idx_bonuses_date_amount',
        
        # AuditLog
        'idx_audit_logs_created_action',
        'idx_audit_logs_user_created',
        'idx_audit_logs_target_created',
        
        # Notification
        'idx_notifications_user_read_created',
        'idx_notifications_unread',
    ]
    
    # Drop all indexes
    for index_name in indexes_to_drop:
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name};")
