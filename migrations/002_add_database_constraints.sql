-- =====================================================
-- WorkingTime Database Constraints Optimization
-- Migration: 002_add_database_constraints.sql
-- Description: Add missing database constraints for data integrity
-- =====================================================

-- Enable timing for monitoring migration performance
\timing on

-- =====================================================
-- 1. Unique Constraints
-- =====================================================

-- Prevent duplicate work schedules for the same user on the same date
ALTER TABLE work_schedules 
ADD CONSTRAINT IF NOT EXISTS unique_user_date_schedule 
UNIQUE (user_id, date);

-- Prevent duplicate leave balance entries for the same user and year
ALTER TABLE leave_balances 
ADD CONSTRAINT IF NOT EXISTS unique_user_year_balance 
UNIQUE (user_id, year);

-- Prevent duplicate monthly work days entries
ALTER TABLE monthly_work_days 
ADD CONSTRAINT IF NOT EXISTS unique_year_month_work_days 
UNIQUE (year, month);

-- Prevent duplicate public holidays on the same date (already exists but ensure)
ALTER TABLE public_holidays 
ADD CONSTRAINT IF NOT EXISTS unique_holiday_date 
UNIQUE (date);

-- Prevent duplicate shifts with the same name
ALTER TABLE shifts 
ADD CONSTRAINT IF NOT EXISTS unique_shift_name 
UNIQUE (name);

-- Prevent duplicate schedule template names
ALTER TABLE schedule_templates 
ADD CONSTRAINT IF NOT EXISTS unique_template_name 
UNIQUE (name);

-- Prevent duplicate api key prefixes
ALTER TABLE api_keys 
ADD CONSTRAINT IF NOT EXISTS unique_key_prefix 
UNIQUE (key_prefix);

-- =====================================================
-- 2. CHECK Constraints for Data Validation
-- =====================================================

-- User table constraints
ALTER TABLE users 
ADD CONSTRAINT IF NOT EXISTS check_failed_login_attempts 
CHECK (failed_login_attempts >= 0);

ALTER TABLE users 
ADD CONSTRAINT IF NOT EXISTS check_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- TimeLog table constraints
ALTER TABLE timelogs 
ADD CONSTRAINT IF NOT EXISTS check_timelog_dates 
CHECK (end_time IS NULL OR end_time >= start_time);

ALTER TABLE timelogs 
ADD CONSTRAINT IF NOT EXISTS check_break_duration 
CHECK (break_duration_minutes >= 0);

ALTER TABLE timelogs 
ADD CONSTRAINT IF NOT EXISTS check_timelog_type 
CHECK (type IN ('work', 'break', 'overtime', 'lunch', 'meeting', 'travel'));

ALTER TABLE timelogs 
ADD CONSTRAINT IF NOT EXISTS check_coordinates 
CHECK (
    (latitude IS NULL AND longitude IS NULL) OR 
    (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)
);

-- Payroll table constraints
ALTER TABLE payrolls 
ADD CONSTRAINT IF NOT EXISTS check_hourly_rate_positive 
CHECK (hourly_rate >= 0);

ALTER TABLE payrolls 
ADD CONSTRAINT IF NOT EXISTS check_monthly_salary_positive 
CHECK (monthly_salary >= 0);

ALTER TABLE payrolls 
ADD CONSTRAINT IF NOT EXISTS check_overtime_multiplier 
CHECK (overtime_multiplier >= 1);

ALTER TABLE payrolls 
ADD CONSTRAINT IF NOT EXISTS check_standard_hours 
CHECK (standard_hours_per_day > 0 AND standard_hours_per_day <= 24);

ALTER TABLE payrolls 
ADD CONSTRAINT IF NOT EXISTS check_tax_percentage 
CHECK (tax_percent >= 0 AND tax_percent <= 100);

ALTER TABLE payrolls 
ADD CONSTRAINT IF NOT EXISTS check_insurance_percentage 
CHECK (health_insurance_percent >= 0 AND health_insurance_percent <= 100);

-- Payslip table constraints
ALTER TABLE payslips 
ADD CONSTRAINT IF NOT EXISTS check_payslip_periods 
CHECK (period_end >= period_start);

ALTER TABLE payslips 
ADD CONSTRAINT IF NOT EXISTS check_payslip_hours 
CHECK (
    total_regular_hours >= 0 AND 
    total_overtime_hours >= 0 AND 
    sick_days >= 0 AND 
    leave_days >= 0
);

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

-- WorkSchedule table constraints (redundant due to unique constraint but keep for clarity)
ALTER TABLE work_schedules 
ADD CONSTRAINT IF NOT EXISTS check_schedule_date_future 
CHECK (date >= CURRENT_DATE - INTERVAL '1 year');

-- LeaveRequest table constraints
ALTER TABLE leave_requests 
ADD CONSTRAINT IF NOT EXISTS check_leave_request_dates 
CHECK (end_date >= start_date);

ALTER TABLE leave_requests 
ADD CONSTRAINT IF NOT EXISTS check_leave_request_type 
CHECK (leave_type IN ('paid_leave', 'sick_leave', 'unpaid_leave', 'maternity_leave', 'paternity_leave'));

ALTER TABLE leave_requests 
ADD CONSTRAINT IF NOT EXISTS check_leave_request_status 
CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled'));

-- LeaveBalance table constraints
ALTER TABLE leave_balances 
ADD CONSTRAINT IF NOT EXISTS check_leave_balance_days 
CHECK (
    total_days >= 0 AND 
    used_days >= 0 AND 
    used_days <= total_days
);

ALTER TABLE leave_balances 
ADD CONSTRAINT IF NOT EXISTS check_balance_year 
CHECK (year BETWEEN 2000 AND 2100);

-- Bonus table constraints
ALTER TABLE bonuses 
ADD CONSTRAINT IF NOT EXISTS check_bonus_amount_positive 
CHECK (amount > 0);

-- UserSession table constraints
ALTER TABLE user_sessions 
ADD CONSTRAINT IF NOT EXISTS check_session_expiry 
CHECK (expires_at > created_at);

ALTER TABLE user_sessions 
ADD CONSTRAINT IF NOT EXISTS check_device_type 
CHECK (device_type IN ('desktop', 'mobile', 'tablet', 'api', 'unknown'));

-- Shift table constraints
ALTER TABLE shifts 
ADD CONSTRAINT IF NOT EXISTS check_shift_times 
CHECK (end_time != start_time);

ALTER TABLE shifts 
ADD CONSTRAINT IF NOT EXISTS check_shift_tolerance 
CHECK (tolerance_minutes >= 0);

ALTER TABLE shifts 
ADD CONSTRAINT IF NOT EXISTS check_break_duration 
CHECK (break_duration_minutes >= 0);

ALTER TABLE shifts 
ADD CONSTRAINT IF NOT EXISTS check_pay_multiplier 
CHECK (pay_multiplier > 0);

ALTER TABLE shifts 
ADD CONSTRAINT IF NOT EXISTS check_shift_type 
CHECK (shift_type IN ('regular', 'sick_leave', 'paid_leave', 'unpaid_leave', 'day_off', 'holiday'));

-- MonthlyWorkDays table constraints
ALTER TABLE monthly_work_days 
ADD CONSTRAINT IF NOT EXISTS check_month_range 
CHECK (month BETWEEN 1 AND 12);

ALTER TABLE monthly_work_days 
ADD CONSTRAINT IF NOT EXISTS check_year_range 
CHECK (year BETWEEN 2000 AND 2100);

ALTER TABLE monthly_work_days 
ADD CONSTRAINT IF NOT EXISTS check_days_count 
CHECK (days_count BETWEEN 0 AND 31);

-- PublicHoliday table constraints
ALTER TABLE public_holidays 
ADD CONSTRAINT IF NOT EXISTS check_holiday_year 
CHECK (EXTRACT(YEAR FROM date) BETWEEN 2000 AND 2100);

-- Notification table constraints
ALTER TABLE notifications 
ADD CONSTRAINT IF NOT EXISTS check_message_not_empty 
CHECK (LENGTH(TRIM(message)) > 0);

-- ShiftSwapRequest table constraints
ALTER TABLE shift_swap_requests 
ADD CONSTRAINT IF NOT EXISTS check_swap_status 
CHECK (status IN ('pending', 'accepted', 'rejected', 'approved', 'cancelled'));

ALTER TABLE shift_swap_requests 
ADD CONSTRAINT IF NOT EXISTS check_different_users 
CHECK (requestor_id != target_user_id);

-- WorkplaceLocation table constraints
ALTER TABLE workplace_locations 
ADD CONSTRAINT IF NOT EXISTS check_location_coordinates 
CHECK (
    latitude BETWEEN -90 AND 90 AND 
    longitude BETWEEN -180 AND 180
);

ALTER TABLE workplace_locations 
ADD CONSTRAINT IF NOT EXISTS check_radius_positive 
CHECK (radius_meters > 0);

-- =====================================================
-- 3. Foreign Key Constraints with Proper Actions
-- =====================================================

-- Ensure referential integrity with proper cascade rules
-- Note: Most foreign keys should already exist, but we verify and add missing ones

-- User to Role
ALTER TABLE users 
DROP CONSTRAINT IF EXISTS users_role_id_fkey,
ADD CONSTRAINT users_role_id_fkey 
FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT ON UPDATE CASCADE;

-- TimeLog to User
ALTER TABLE timelogs 
DROP CONSTRAINT IF EXISTS timelogs_user_id_fkey,
ADD CONSTRAINT timelogs_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- Payroll to User and Position
ALTER TABLE payrolls 
DROP CONSTRAINT IF EXISTS payrolls_user_id_fkey,
ADD CONSTRAINT payrolls_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE payrolls 
DROP CONSTRAINT IF EXISTS payrolls_position_id_fkey,
ADD CONSTRAINT payrolls_position_id_fkey 
FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE SET NULL ON UPDATE CASCADE;

-- Payslip to User
ALTER TABLE payslips 
DROP CONSTRAINT IF EXISTS payslips_user_id_fkey,
ADD CONSTRAINT payslips_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- WorkSchedule to User and Shift
ALTER TABLE work_schedules 
DROP CONSTRAINT IF EXISTS work_schedules_user_id_fkey,
ADD CONSTRAINT work_schedules_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE work_schedules 
DROP CONSTRAINT IF EXISTS work_schedules_shift_id_fkey,
ADD CONSTRAINT work_schedules_shift_id_fkey 
FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE RESTRICT ON UPDATE CASCADE;

-- LeaveRequest to User
ALTER TABLE leave_requests 
DROP CONSTRAINT IF EXISTS leave_requests_user_id_fkey,
ADD CONSTRAINT leave_requests_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- LeaveBalance to User
ALTER TABLE leave_balances 
DROP CONSTRAINT IF EXISTS leave_balances_user_id_fkey,
ADD CONSTRAINT leave_balances_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- Bonus to User
ALTER TABLE bonuses 
DROP CONSTRAINT IF EXISTS bonuses_user_id_fkey,
ADD CONSTRAINT bonuses_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- Notification to User
ALTER TABLE notifications 
DROP CONSTRAINT IF EXISTS notifications_user_id_fkey,
ADD CONSTRAINT notifications_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- UserSession to User
ALTER TABLE user_sessions 
DROP CONSTRAINT IF EXISTS user_sessions_user_id_fkey,
ADD CONSTRAINT user_sessions_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- =====================================================
-- 4. Triggers for Advanced Data Integrity
-- =====================================================

-- Function to prevent overlapping work schedules
CREATE OR REPLACE FUNCTION prevent_overlapping_schedules()
RETURNS TRIGGER AS $$
BEGIN
    -- Check for existing schedule for the same user and date
    IF EXISTS (
        SELECT 1 FROM work_schedules 
        WHERE user_id = NEW.user_id 
        AND date = NEW.date 
        AND id != COALESCE(NEW.id, 0)
    ) THEN
        RAISE EXCEPTION 'Work schedule already exists for user % on date %', 
            NEW.user_id, NEW.date;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to prevent overlapping schedules
DROP TRIGGER IF EXISTS trigger_prevent_overlapping_schedules ON work_schedules;
CREATE TRIGGER trigger_prevent_overlapping_schedules
BEFORE INSERT OR UPDATE ON work_schedules
FOR EACH ROW EXECUTE FUNCTION prevent_overlapping_schedules();

-- Function to validate leave request dates and prevent overlaps
CREATE OR REPLACE FUNCTION validate_leave_request()
RETURNS TRIGGER AS $$
BEGIN
    -- Check date validity
    IF NEW.end_date < NEW.start_date THEN
        RAISE EXCEPTION 'End date cannot be before start date';
    END IF;
    
    -- Check for overlapping approved leaves
    IF NEW.status = 'approved' THEN
        IF EXISTS (
            SELECT 1 FROM leave_requests 
            WHERE user_id = NEW.user_id 
            AND status = 'approved'
            AND id != COALESCE(NEW.id, 0)
            AND (
                (start_date <= NEW.start_date AND end_date >= NEW.start_date) OR
                (start_date <= NEW.end_date AND end_date >= NEW.end_date) OR
                (start_date >= NEW.start_date AND end_date <= NEW.end_date)
            )
        ) THEN
            RAISE EXCEPTION 'Overlapping approved leave request exists for user %', 
                NEW.user_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for leave request validation
DROP TRIGGER IF EXISTS trigger_validate_leave_request ON leave_requests;
CREATE TRIGGER trigger_validate_leave_request
BEFORE INSERT OR UPDATE ON leave_requests
FOR EACH ROW EXECUTE FUNCTION validate_leave_request();

-- Function to automatically update leave balance
CREATE OR REPLACE FUNCTION update_leave_balance()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.status = 'approved' THEN
        INSERT INTO leave_balances (user_id, year, total_days, used_days)
        VALUES (NEW.user_id, EXTRACT(YEAR FROM NEW.start_date), 20, 1)
        ON CONFLICT (user_id, year)
        DO UPDATE SET used_days = leave_balances.used_days + 1;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.status != 'approved' AND NEW.status = 'approved' THEN
            INSERT INTO leave_balances (user_id, year, total_days, used_days)
            VALUES (NEW.user_id, EXTRACT(YEAR FROM NEW.start_date), 20, 1)
            ON CONFLICT (user_id, year)
            DO UPDATE SET used_days = leave_balances.used_days + 1;
        ELSIF OLD.status = 'approved' AND NEW.status != 'approved' THEN
            UPDATE leave_balances 
            SET used_days = GREATEST(used_days - 1, 0)
            WHERE user_id = NEW.user_id 
            AND year = EXTRACT(YEAR FROM NEW.start_date);
        END IF;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic leave balance updates
DROP TRIGGER IF EXISTS trigger_update_leave_balance ON leave_requests;
CREATE TRIGGER trigger_update_leave_balance
AFTER INSERT OR UPDATE ON leave_requests
FOR EACH ROW EXECUTE FUNCTION update_leave_balance();

-- =====================================================
-- 5. Migration Verification
-- =====================================================

-- Verify all constraints were created successfully
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name,
    kcu.column_name,
    cc.check_clause
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
LEFT JOIN information_schema.check_constraints cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_schema = 'public'
    AND tc.table_name IN (
        'users', 'timelogs', 'payrolls', 'payslips', 'work_schedules',
        'leave_requests', 'leave_balances', 'bonuses', 'user_sessions',
        'shifts', 'notifications', 'monthly_work_days', 'public_holidays',
        'shift_swap_requests', 'workplace_locations'
    )
    AND tc.constraint_type IN ('CHECK', 'UNIQUE', 'FOREIGN KEY')
ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;

-- Analyze tables to update statistics
ANALYZE users;
ANALYZE timelogs;
ANALYZE payrolls;
ANALYZE payslips;
ANALYZE work_schedules;
ANALYZE leave_requests;
ANALYZE leave_balances;
ANALYZE bonuses;
ANALYZE user_sessions;
ANALYZE shifts;
ANALYZE notifications;
ANALYZE monthly_work_days;
ANALYZE public_holidays;
ANALYZE shift_swap_requests;
ANALYZE workplace_locations;

-- Disable timing
\timing off

-- Migration completed successfully
SELECT '002_add_database_constraints.sql migration completed successfully' as status;
