-- Migration 018: Remove contact tracking and relationship_strength fields from client_profiles

BEGIN TRANSACTION;

DROP INDEX IF EXISTS idx_client_profiles_last_contact;

ALTER TABLE client_profiles DROP COLUMN relationship_strength_encrypted;
ALTER TABLE client_profiles DROP COLUMN last_contact_date;
ALTER TABLE client_profiles DROP COLUMN last_contact_type;
ALTER TABLE client_profiles DROP COLUMN next_planned_contact_date;
ALTER TABLE client_profiles DROP COLUMN next_planned_contact_type;

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (18, datetime('now'), 'system', 'Drop contact tracking and relationship_strength fields from client_profiles');

COMMIT;
