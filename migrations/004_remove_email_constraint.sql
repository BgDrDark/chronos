-- Migration: 004_remove_email_constraint.sql
-- Description: Remove restrictive email format constraint from users table
-- Reason: Pydantic already validates EmailStr in schemas, allowing RFC 5322 compliant emails
-- Date: 2026-02-17

-- Drop the restrictive email format check constraint
ALTER TABLE users DROP CONSTRAINT IF EXISTS check_email_format;

-- Migration completed
SELECT '004_remove_email_constraint.sql migration completed successfully' as status;
