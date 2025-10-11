-- Migration 012: Clean up remaining legacy tables
-- Created: 2025-10-10
-- Description: Drop the remaining legacy tables that weren't caught in migration 011
-- Version: 12

-- Migration 011 missed these tables due to naming differences:
-- - owners_developers (with 's')
-- - vendor_preferred_constructor (singular)

BEGIN TRANSACTION;

-- Drop remaining legacy tables
DROP TABLE IF EXISTS owners_developers;
DROP TABLE IF EXISTS vendor_preferred_constructor;

-- Update schema version
INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (12, datetime('now'), 'system', 'Clean up remaining legacy tables missed in migration 011');

COMMIT;
