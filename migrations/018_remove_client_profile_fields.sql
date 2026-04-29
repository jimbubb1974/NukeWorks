-- Migration 018: Remove unused fields from client_profiles
-- Drops: relationship_strength_encrypted, client_status_encrypted,
--        last_contact_date, last_contact_type,
--        next_planned_contact_date, next_planned_contact_type

BEGIN TRANSACTION;

DROP INDEX IF EXISTS idx_client_profiles_last_contact;

ALTER TABLE client_profiles DROP COLUMN relationship_strength_encrypted;
ALTER TABLE client_profiles DROP COLUMN client_status_encrypted;
ALTER TABLE client_profiles DROP COLUMN last_contact_date;
ALTER TABLE client_profiles DROP COLUMN last_contact_type;
ALTER TABLE client_profiles DROP COLUMN next_planned_contact_date;
ALTER TABLE client_profiles DROP COLUMN next_planned_contact_type;

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (
    18,
    datetime('now'),
    'system',
    'Remove relationship_strength, client_status, and contact tracking fields from client_profiles'
);

COMMIT;
