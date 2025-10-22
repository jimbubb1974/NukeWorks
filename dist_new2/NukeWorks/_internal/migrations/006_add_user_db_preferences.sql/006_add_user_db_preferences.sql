-- Migration 006: Add database selection preferences to users table
-- Supports per-user/session database selection feature
-- Date: 2025-10-07

BEGIN TRANSACTION;

-- Add database selection preference columns to users table
ALTER TABLE users ADD COLUMN last_db_path TEXT;
ALTER TABLE users ADD COLUMN last_db_display_name TEXT;

-- Update schema version
INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (6, datetime('now'), 'system', 'Add database selection preferences to users table');

COMMIT;
