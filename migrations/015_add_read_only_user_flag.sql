-- Migration 015: Add read-only permission flag to users
-- Implements Type 3 permission: can view non-confidential data but cannot edit anything

BEGIN TRANSACTION;

ALTER TABLE users ADD COLUMN is_read_only BOOLEAN NOT NULL DEFAULT 0;

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (
    15,
    datetime('now'),
    'system',
    'Add is_read_only flag to users for read-only permission tier'
);

COMMIT;
