-- =====================================================
-- WorkingTime Database Table Partitioning
-- Migration: 003_table_partitioning.sql
-- Description: Implement table partitioning for TimeLog and AuditLog
-- =====================================================

-- Enable timing for monitoring migration performance
\timing on

-- =====================================================
-- 1. TimeLog Table Partitioning by Month
-- =====================================================

-- First, create the partitioned table structure
-- Note: This requires recreating the table, so we'll create new tables and migrate data

-- Create new partitioned timelogs table
CREATE TABLE timelogs_partitioned (
    LIKE timelogs INCLUDING ALL
) PARTITION BY RANGE (date_trunc('month', start_time));

-- Create partitions for the last 24 months and future 12 months
DO $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
    i integer;
BEGIN
    -- Create partitions for past 24 months
    FOR i IN -24..0 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'timelogs_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF timelogs_partitioned
                       FOR VALUES FROM (%L) TO (%L)',
                       partition_name, start_date, end_date);
    END LOOP;
    
    -- Create partitions for future 12 months
    FOR i IN 1..12 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'timelogs_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF timelogs_partitioned
                       FOR VALUES FROM (%L) TO (%L)',
                       partition_name, start_date, end_date);
    END LOOP;
END $$;

-- Create indexes on the partitioned table
-- These indexes will be automatically created on each partition

-- Primary composite index for time log queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_partitioned_user_start_time 
ON timelogs_partitioned (user_id, start_time DESC);

-- Secondary index for end_time queries (active time logs)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_partitioned_user_end_time 
ON timelogs_partitioned (user_id, end_time DESC) WHERE end_time IS NULL;

-- Composite index for date range queries by user
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_partitioned_user_date_range 
ON timelogs_partitioned (user_id, date_trunc('day', start_time), start_time);

-- Index for manual vs automatic time logs filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_timelogs_partitioned_manual_type 
ON timelogs_partitioned (is_manual, type, start_time DESC);

-- =====================================================
-- 2. AuditLog Table Partitioning by Month
-- =====================================================

-- Create new partitioned audit_logs table
CREATE TABLE audit_logs_partitioned (
    LIKE audit_logs INCLUDING ALL
) PARTITION BY RANGE (date_trunc('month', created_at));

-- Create partitions for audit logs
DO $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
    i integer;
BEGIN
    -- Create partitions for past 12 months
    FOR i IN -12..0 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs_partitioned
                       FOR VALUES FROM (%L) TO (%L)',
                       partition_name, start_date, end_date);
    END LOOP;
    
    -- Create partitions for future 6 months
    FOR i IN 1..6 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs_partitioned
                       FOR VALUES FROM (%L) TO (%L)',
                       partition_name, start_date, end_date);
    END LOOP;
END $$;

-- Create indexes on the partitioned audit_logs table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_partitioned_created_action 
ON audit_logs_partitioned (created_at DESC, action);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_partitioned_user_created 
ON audit_logs_partitioned (user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_partitioned_target_created 
ON audit_logs_partitioned (target_type, target_id, created_at DESC);

-- =====================================================
-- 3. Automated Partition Management Functions
-- =====================================================

-- Function to create new partitions for timelogs
CREATE OR REPLACE FUNCTION create_timelog_partitions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
    i integer;
BEGIN
    -- Create partitions for next 3 months
    FOR i IN 1..3 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || 'months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'timelogs_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF timelogs_partitioned
                       FOR VALUES FROM (%L) TO (%L)',
                       partition_name, start_date, end_date);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to create new partitions for audit logs
CREATE OR REPLACE FUNCTION create_audit_log_partitions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
    i integer;
BEGIN
    -- Create partitions for next 3 months
    FOR i IN 1..3 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || 'months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs_partitioned
                       FOR VALUES FROM (%L) TO (%L)',
                       partition_name, start_date, end_date);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to drop old partitions (older than 2 years)
CREATE OR REPLACE FUNCTION drop_old_partitions()
RETURNS void AS $$
DECLARE
    partition_name text;
    cutoff_date date;
BEGIN
    cutoff_date := CURRENT_DATE - interval '2 years';
    
    -- Drop old timelog partitions
    FOR partition_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'timelogs_%' 
        AND tablename < 'timelogs_' || to_char(cutoff_date, 'YYYY_MM')
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', partition_name);
        RAISE NOTICE 'Dropped timelog partition: %', partition_name;
    END LOOP;
    
    -- Drop old audit log partitions
    FOR partition_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'audit_logs_%' 
        AND tablename < 'audit_logs_' || to_char(cutoff_date, 'YYYY_MM')
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', partition_name);
        RAISE NOTICE 'Dropped audit log partition: %', partition_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. Automated Partition Management with pg_cron
-- =====================================================

-- Schedule partition management (requires pg_cron extension)
-- Note: Uncomment these if pg_cron is available
-- SELECT cron.schedule('create-timelog-partitions', '0 0 1 * *', 'SELECT create_timelog_partitions();');
-- SELECT cron.schedule('create-audit-log-partitions', '0 0 1 * *', 'SELECT create_audit_log_partitions();');
-- SELECT cron.schedule('drop-old-partitions', '0 2 1 * *', 'SELECT drop_old_partitions();');

-- =====================================================
-- 5. Data Migration Script (Run separately during maintenance window)
-- =====================================================

-- Create a migration function to move data from original to partitioned tables
CREATE OR REPLACE FUNCTION migrate_to_partitioned_tables(batch_size integer DEFAULT 10000)
RETURNS void AS $$
DECLARE
    migrated_rows integer;
    total_migrated integer := 0;
    start_time timestamp;
BEGIN
    -- Start timing
    start_time := clock_timestamp();
    
    RAISE NOTICE 'Starting migration of TimeLog data...';
    
    -- Migrate TimeLog data in batches
    LOOP
        INSERT INTO timelogs_partitioned 
        SELECT * FROM timelogs 
        WHERE id NOT IN (SELECT id FROM timelogs_partitioned)
        LIMIT batch_size;
        
        GET DIAGNOSTICS migrated_rows = ROW_COUNT;
        total_migrated := total_migrated + migrated_rows;
        
        RAISE NOTICE 'Migrated % rows (total: %)', migrated_rows, total_migrated;
        
        IF migrated_rows = 0 THEN
            EXIT;
        END IF;
        
        -- Commit every batch to avoid long transactions
        COMMIT;
    END LOOP;
    
    RAISE NOTICE 'Starting migration of AuditLog data...';
    
    -- Migrate AuditLog data in batches
    LOOP
        INSERT INTO audit_logs_partitioned 
        SELECT * FROM audit_logs 
        WHERE id NOT IN (SELECT id FROM audit_logs_partitioned)
        LIMIT batch_size;
        
        GET DIAGNOSTICS migrated_rows = ROW_COUNT;
        total_migrated := total_migrated + migrated_rows;
        
        RAISE NOTICE 'Migrated % audit log rows (total: %)', migrated_rows, total_migrated;
        
        IF migrated_rows = 0 THEN
            EXIT;
        END IF;
        
        COMMIT;
    END LOOP;
    
    RAISE NOTICE 'Migration completed in % seconds', 
        EXTRACT(EPOCH FROM clock_timestamp() - start_time);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 6. View for Seamless Migration
-- =====================================================

-- Create a view that unions both tables during migration period
CREATE OR REPLACE VIEW timelogs_all AS
SELECT * FROM timelogs
UNION ALL
SELECT * FROM timelogs_partitioned;

CREATE OR REPLACE VIEW audit_logs_all AS
SELECT * FROM audit_logs
UNION ALL
SELECT * FROM audit_logs_partitioned;

-- =====================================================
-- 7. Migration Verification
-- =====================================================

-- Check partition structure
SELECT 
    schemaname,
    tablename,
    partitionname,
    partitionkeydef
FROM pg_partitioned_tables pt
JOIN pg_partitions p ON pt.tablename = p.schemaname || '.' || p.partitiontablename
WHERE pt.schemaname = 'public'
ORDER BY pt.tablename, p.partitionname;

-- Analyze new tables
ANALYZE timelogs_partitioned;
ANALYZE audit_logs_partitioned;

-- Disable timing
\timing off

-- Migration completed successfully
SELECT '003_table_partitioning.sql migration completed successfully' as status;
