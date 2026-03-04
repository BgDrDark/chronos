-- =====================================================
-- WorkingTime Database Performance Optimization
-- Migration: 001_add_critical_indexes.sql
-- Description: Add critical composite indexes for performance
-- =====================================================

-- Enable timing for monitoring migration performance
\timing on

-- =====================================================
-- 1. TimeLog Table Indexes
-- =====================================================

-- Primary composite index for time log queries
-- This index covers: user presence, daily stats, payroll calculations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_user_start_time 
ON timelogs (user_id, start_time DESC);

-- Secondary index for end_time queries (active time logs)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_user_end_time 
ON timelogs (user_id, end_time DESC) WHERE end_time IS NULL;

-- Composite index for date range queries by user
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_user_date_range 
ON timelogs (user_id, date_trunc('day', start_time), start_time);

-- Index for manual vs automatic time logs filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_manual_type 
ON timelogs (is_manual, type, start_time DESC);

-- =====================================================
-- 2. WorkSchedule Table Indexes
-- =====================================================

-- Primary composite index for schedule queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_schedules_user_date 
ON work_schedules (user_id, date);

-- Composite index for shift-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_schedules_date_shift 
ON work_schedules (date, shift_id);

-- Join optimization index for user presence calculations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_schedules_user_date_shift 
ON work_schedules (user_id, date, shift_id);

-- =====================================================
-- 3. LeaveRequest Table Indexes
-- =====================================================

-- Composite index for leave request status queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_status_dates 
ON leave_requests (status, start_date, end_date);

-- User-specific leave requests index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_user_dates 
ON leave_requests (user_id, start_date, end_date);

-- Index for date overlap checks (critical for leave validation)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_date_overlap 
ON leave_requests (user_id, status, start_date, end_date);

-- =====================================================
-- 4. Payslip Table Indexes
-- =====================================================

-- Primary composite index for payslip queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payslips_user_period 
ON payslips (user_id, period_start DESC, period_end DESC);

-- Index for payroll period queries (management reports)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payslips_period_user 
ON payslips (period_start DESC, period_end DESC, user_id);

-- Index for amount-based queries and statistics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payslips_generated_amount 
ON payslips (generated_at DESC, total_amount);

-- =====================================================
-- 5. User Table Indexes
-- =====================================================

-- Composite index for user management queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_company 
ON users (is_active, company_id);

-- Index for role-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_active 
ON users (role_id, is_active);

-- Index for security fields (authentication)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active 
ON users (email, is_active);

-- Index for failed login tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_locked_until 
ON users (locked_until) WHERE locked_until IS NOT NULL;

-- =====================================================
-- 6. UserSession Table Indexes
-- =====================================================

-- Composite index for active session queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_user_active 
ON user_sessions (user_id, is_active, expires_at DESC);

-- Index for session cleanup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_expires 
ON user_sessions (expires_at) WHERE is_active = true;

-- Index for refresh token lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_refresh_token 
ON user_sessions (refresh_token_jti, is_active);

-- =====================================================
-- 7. Payroll Table Indexes
-- =====================================================

-- Composite index for payroll configuration queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payrolls_user_position 
ON payrolls (user_id, position_id);

-- Index for currency and rate-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payrolls_currency_rate 
ON payrolls (currency, hourly_rate, monthly_salary DESC);

-- =====================================================
-- 8. Bonus Table Indexes
-- =====================================================

-- Composite index for bonus queries by user and date
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bonuses_user_date 
ON bonuses (user_id, date DESC);

-- Index for monthly bonus calculations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bonuses_date_amount 
ON bonuses (date DESC, amount DESC);

-- =====================================================
-- 9. AuditLog Table Indexes
-- =====================================================

-- Primary composite index for audit log queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_action 
ON audit_logs (created_at DESC, action);

-- User-specific audit log index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_created 
ON audit_logs (user_id, created_at DESC);

-- Index for target-based searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_target_created 
ON audit_logs (target_type, target_id, created_at DESC);

-- =====================================================
-- 10. Notification Table Indexes
-- =====================================================

-- Composite index for user notification queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_user_read_created 
ON notifications (user_id, is_read, created_at DESC);

-- Index for unread notification queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_unread 
ON notifications (user_id, created_at DESC) WHERE is_read = false;

-- =====================================================
-- 11. ShiftSwapRequest Table Indexes
-- =====================================================

-- Composite index for swap request status queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_swap_requests_status_created 
ON shift_swap_requests (status, created_at DESC);

-- User-specific swap request index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_swap_requests_requestor_target 
ON shift_swap_requests (requestor_id, target_user_id, status);

-- =====================================================
-- 12. PublicHoliday Table Indexes
-- =====================================================

-- Composite index for holiday queries by year
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_public_holidays_year 
ON public_holidays (date DESC, name);

-- Index for date range queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_public_holidays_date_range 
ON public_holidays (date);

-- =====================================================
-- 13. Company/Department/Position Relationship Indexes
-- =====================================================

-- Company departments index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_departments_company 
ON departments (company_id, name);

-- Department positions index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_positions_department 
ON positions (department_id, title);

-- Users by department and position
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_department_position 
ON users (department_id, position_id, is_active);

-- =====================================================
-- 14. Partial Indexes for Common Query Patterns
-- =====================================================

-- Active time logs only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_active 
ON timelogs (user_id, start_time DESC) WHERE end_time IS NULL;

-- Today's work schedules only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_schedules_today 
ON work_schedules (user_id, shift_id) WHERE date = CURRENT_DATE;

-- Pending leave requests only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_pending 
ON leave_requests (user_id, start_date) WHERE status = 'pending';

-- Approved leave requests for date range checks
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_approved 
ON leave_requests (user_id, start_date, end_date) WHERE status = 'approved';

-- Failed login attempts tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_failed_attempts 
ON users (failed_login_attempts, locked_until) WHERE failed_login_attempts > 0;

-- =====================================================
-- Migration Verification Queries
-- =====================================================

-- Verify all indexes were created successfully
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND (
        tablename IN ('timelogs', 'work_schedules', 'leave_requests', 'payslips', 
                     'users', 'user_sessions', 'payrolls', 'bonuses', 'audit_logs',
                     'notifications', 'shift_swap_requests', 'public_holidays',
                     'departments', 'positions', 'companies')
        OR indexname LIKE 'idx_%'
    )
ORDER BY tablename, indexname;

-- Analyze tables to update statistics
ANALYZE timelogs;
ANALYZE work_schedules;
ANALYZE leave_requests;
ANALYZE payslips;
ANALYZE users;
ANALYZE user_sessions;
ANALYZE payrolls;
ANALYZE bonuses;
ANALYZE audit_logs;
ANALYZE notifications;
ANALYZE shift_swap_requests;
ANALYZE public_holidays;
ANALYZE departments;
ANALYZE positions;
ANALYZE companies;

-- Disable timing
\timing off

-- Migration completed successfully
SELECT '001_add_critical_indexes.sql migration completed successfully' as status;
