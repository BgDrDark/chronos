-- PostgreSQL initialization script for WorkingTime
-- This script runs automatically when the database container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'Europe/Sofia';

-- Create initial roles (if they don't exist)
INSERT INTO roles (id, name, description, is_system_role, priority, created_at)
VALUES 
    (1, 'super_admin', 'Super Administrator with full system access', true, 100, NOW()),
    (2, 'company_admin', 'Company Administrator with company-scoped access', true, 80, NOW()),
    (3, 'hr_manager', 'HR Manager with people management permissions', true, 60, NOW()),
    (4, 'manager', 'Manager with team oversight permissions', true, 50, NOW()),
    (5, 'employee', 'Standard Employee with self-service permissions', true, 20, NOW()),
    (6, 'viewer', 'Read-only access for auditors and contractors', true, 10, NOW())
ON CONFLICT (name) DO NOTHING;

-- Create initial permissions (if they don't exist)
INSERT INTO permissions (name, resource, action, description, created_at) VALUES
    -- User Management
    ('users:read', 'users', 'read', 'View user information', NOW()),
    ('users:read_own', 'users', 'read_own', 'View own user information', NOW()),
    ('users:create', 'users', 'create', 'Create new users', NOW()),
    ('users:update', 'users', 'update', 'Update user information', NOW()),
    ('users:update_own', 'users', 'update_own', 'Update own profile', NOW()),
    ('users:delete', 'users', 'delete', 'Delete users', NOW()),
    ('users:manage_roles', 'users', 'manage_roles', 'Assign user roles', NOW()),
    
    -- Time Management
    ('timelogs:read', 'timelogs', 'read', 'View time logs', NOW()),
    ('timelogs:read_own', 'timelogs', 'read_own', 'View own time logs', NOW()),
    ('timelogs:create', 'timelogs', 'create', 'Create time logs', NOW()),
    ('timelogs:create_own', 'timelogs', 'create_own', 'Clock in/out for self', NOW()),
    ('timelogs:update', 'timelogs', 'update', 'Modify time logs', NOW()),
    ('timelogs:delete', 'timelogs', 'delete', 'Delete time logs', NOW()),
    ('timelogs:admin_create', 'timelogs', 'admin_create', 'Create time logs for others', NOW()),
    
    -- Schedule Management
    ('schedules:read', 'schedules', 'read', 'View schedules', NOW()),
    ('schedules:read_own', 'schedules', 'read_own', 'View own schedule', NOW()),
    ('schedules:create', 'schedules', 'create', 'Create schedules', NOW()),
    ('schedules:update', 'schedules', 'update', 'Update schedules', NOW()),
    ('schedules:delete', 'schedules', 'delete', 'Delete schedules', NOW()),
    ('schedules:approve_swaps', 'schedules', 'approve_swaps', 'Approve shift swaps', NOW()),
    
    -- Payroll Management
    ('payroll:read', 'payroll', 'read', 'View payroll information', NOW()),
    ('payroll:read_own', 'payroll', 'read_own', 'View own payroll', NOW()),
    ('payroll:create', 'payroll', 'create', 'Create payroll records', NOW()),
    ('payroll:update', 'payroll', 'update', 'Update payroll records', NOW()),
    ('payroll:delete', 'payroll', 'delete', 'Delete payroll records', NOW()),
    ('payroll:export', 'payroll', 'export', 'Export payroll data', NOW()),
    
    -- Leave Management
    ('leaves:read', 'leaves', 'read', 'View leave requests', NOW()),
    ('leaves:read_own', 'leaves', 'read_own', 'View own leave requests', NOW()),
    ('leaves:create', 'leaves', 'create', 'Create leave requests', NOW()),
    ('leaves:create_own', 'leaves', 'create_own', 'Create own leave requests', NOW()),
    ('leaves:approve', 'leaves', 'approve', 'Approve/reject leave requests', NOW()),
    ('leaves:update', 'leaves', 'update', 'Update leave requests', NOW()),
    ('leaves:delete', 'leaves', 'delete', 'Delete leave requests', NOW()),
    
    -- Company Management
    ('companies:read', 'companies', 'read', 'View company information', NOW()),
    ('companies:create', 'companies', 'create', 'Create companies', NOW()),
    ('companies:update', 'companies', 'update', 'Update company information', NOW()),
    ('companies:delete', 'companies', 'delete', 'Delete companies', NOW()),
    ('companies:manage_users', 'companies', 'manage_users', 'Manage company users', NOW()),
    
    -- System Administration
    ('system:backup', 'system', 'backup', 'Create system backups', NOW()),
    ('system:restore', 'system', 'restore', 'Restore from backup', NOW()),
    ('system:read_audit', 'system', 'read_audit', 'View audit logs', NOW()),
    ('system:manage_settings', 'system', 'manage_settings', 'Manage global settings', NOW()),
    ('system:manage_roles', 'system', 'manage_roles', 'Manage roles and permissions', NOW()),
    
    -- Reports & Analytics
    ('reports:read', 'reports', 'read', 'View reports', NOW()),
    ('reports:create', 'reports', 'create', 'Generate reports', NOW()),
    ('reports:export', 'reports', 'export', 'Export reports', NOW()),
    ('analytics:read', 'analytics', 'read', 'View analytics', NOW())
ON CONFLICT (name) DO NOTHING;

-- Assign permissions to roles
INSERT INTO role_permissions (role_id, permission_id, granted_at)
SELECT r.id, p.id, NOW()
FROM roles r, permissions p
WHERE r.name IN ('super_admin', 'company_admin', 'hr_manager', 'manager', 'employee', 'viewer')
  AND p.name IN (
    'users:read', 'users:create', 'users:update', 'users:delete',
    'timelogs:read', 'timelogs:create', 'timelogs:update', 'timelogs:delete',
    'schedules:read', 'schedules:create', 'schedules:update', 'schedules:delete',
    'payroll:read', 'payroll:create', 'payroll:update', 'payroll:export',
    'leaves:read', 'leaves:create', 'leaves:approve', 'leaves:update',
    'companies:read', 'companies:update', 'companies:manage_users',
    'system:backup', 'system:restore', 'system:read_audit', 'system:manage_settings',
    'reports:read', 'reports:create', 'reports:export', 'analytics:read'
  )
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Create default company if it doesn't exist
INSERT INTO companies (id, name)
VALUES (1, 'Default Company')
ON CONFLICT (name) DO NOTHING;

-- Create initial global settings
INSERT INTO global_settings (key, value) VALUES
    ('timezone', 'Europe/Sofia'),
    ('working_hours_per_day', '8'),
    ('working_days_per_week', '5'),
    ('overtime_enabled', 'true'),
    ('auto_leave_approval', 'false'),
    ('geo_fencing_enabled', 'true'),
    ('push_notifications_enabled', 'true')
ON CONFLICT (key) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_timelogs_user_start_time ON timelogs (user_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_timelogs_user_date_range ON timelogs (user_id, date_trunc('day', start_time));
CREATE INDEX IF NOT EXISTS idx_work_schedules_user_date ON work_schedules (user_id, date);
CREATE INDEX IF NOT EXISTS idx_leave_requests_user_dates ON leave_requests (user_id, start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_leave_requests_status_dates ON leave_requests (status, start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_payslips_user_period ON payslips (user_id, period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_active ON user_sessions (user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expiry ON user_sessions (expires_at);

-- Create performance monitoring functions
CREATE OR REPLACE FUNCTION update_database_stats()
RETURNS void AS $$
BEGIN
    ANALYZE;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Output completion message
\echo 'WorkingTime database initialization completed successfully!';