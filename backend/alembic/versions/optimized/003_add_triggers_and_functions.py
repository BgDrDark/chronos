"""Add database triggers and advanced functions

Revision ID: 003_add_triggers_and_functions
Revises: 002_add_database_constraints
Create Date: 2026-02-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '003_add_triggers_and_functions'
down_revision = '002_add_database_constraints'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add database triggers and advanced functions"""
    
    # Function to prevent overlapping work schedules
    op.execute("""
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
    """)
    
    # Trigger to prevent overlapping schedules
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_prevent_overlapping_schedules ON work_schedules;
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_prevent_overlapping_schedules
        BEFORE INSERT OR UPDATE ON work_schedules
        FOR EACH ROW EXECUTE FUNCTION prevent_overlapping_schedules();
    """)
    
    # Function to validate leave request dates and prevent overlaps
    op.execute("""
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
    """)
    
    # Trigger for leave request validation
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_validate_leave_request ON leave_requests;
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_validate_leave_request
        BEFORE INSERT OR UPDATE ON leave_requests
        FOR EACH ROW EXECUTE FUNCTION validate_leave_request();
    """)
    
    # Function to automatically update leave balance
    op.execute("""
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
    """)
    
    # Trigger for automatic leave balance updates
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_update_leave_balance ON leave_requests;
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_update_leave_balance
        AFTER INSERT OR UPDATE ON leave_requests
        FOR EACH ROW EXECUTE FUNCTION update_leave_balance();
    """)
    
    # Function for audit logging
    op.execute("""
        CREATE OR REPLACE FUNCTION log_audit_trail()
        RETURNS TRIGGER AS $$
        DECLARE
            v_user_id INTEGER;
            v_action TEXT;
            v_target_type TEXT;
            v_target_id INTEGER;
            v_details TEXT;
        BEGIN
            -- Try to get current user from session variable
            BEGIN
                v_user_id := current_setting('app.current_user_id')::INTEGER;
            EXCEPTION WHEN OTHERS THEN
                v_user_id := NULL;
            END;
            
            -- Determine action and target information
            IF TG_OP = 'INSERT' THEN
                v_action := 'CREATE_' || UPPER(TG_TABLE_NAME);
                v_target_id := NEW.id;
                v_details := 'Created new record in ' || TG_TABLE_NAME;
                RETURN NEW;
            ELSIF TG_OP = 'UPDATE' THEN
                v_action := 'UPDATE_' || UPPER(TG_TABLE_NAME);
                v_target_id := NEW.id;
                v_details := 'Updated record in ' || TG_TABLE_NAME;
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                v_action := 'DELETE_' || UPPER(TG_TABLE_NAME);
                v_target_id := OLD.id;
                v_details := 'Deleted record from ' || TG_TABLE_NAME;
                RETURN OLD;
            END IF;
            
            v_target_type := TG_TABLE_NAME;
            
            -- Insert audit log
            INSERT INTO audit_logs (user_id, action, target_type, target_id, details, created_at)
            VALUES (v_user_id, v_action, v_target_type, v_target_id, v_details, NOW());
            
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Add audit triggers to important tables
    audit_tables = [
        'users', 'payrolls', 'payslips', 'leave_requests', 'work_schedules',
        'timelogs', 'shifts', 'companies', 'departments', 'positions'
    ]
    
    for table in audit_tables:
        op.execute(f"""
            DROP TRIGGER IF EXISTS trigger_audit_{table} ON {table};
        """)
        
        op.execute(f"""
            CREATE TRIGGER trigger_audit_{table}
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION log_audit_trail();
        """)

def downgrade() -> None:
    """Remove database triggers and functions"""
    
    # Drop triggers
    audit_tables = [
        'users', 'payrolls', 'payslips', 'leave_requests', 'work_schedules',
        'timelogs', 'shifts', 'companies', 'departments', 'positions'
    ]
    
    for table in audit_tables:
        op.execute(f"DROP TRIGGER IF EXISTS trigger_audit_{table} ON {table};")
    
    op.execute("DROP TRIGGER IF EXISTS trigger_update_leave_balance ON leave_requests;")
    op.execute("DROP TRIGGER IF EXISTS trigger_validate_leave_request ON leave_requests;")
    op.execute("DROP TRIGGER IF EXISTS trigger_prevent_overlapping_schedules ON work_schedules;")
    
    # Drop functions
    functions_to_drop = [
        'log_audit_trail',
        'update_leave_balance',
        'validate_leave_request',
        'prevent_overlapping_schedules'
    ]
    
    for function_name in functions_to_drop:
        op.execute(f"DROP FUNCTION IF EXISTS {function_name}();")
