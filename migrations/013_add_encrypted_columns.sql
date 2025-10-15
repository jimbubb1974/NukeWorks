-- Migration 013: Add Encrypted Columns for Field-Level Encryption
-- Adds encrypted BLOB columns alongside existing text/float columns
-- This is a NON-BREAKING migration - old columns remain for backward compatibility

-- ===========================================================================
-- PROJECTS: Add Encrypted Financial Fields (Confidential Access Required)
-- ===========================================================================

ALTER TABLE projects ADD COLUMN capex_encrypted BLOB;
ALTER TABLE projects ADD COLUMN opex_encrypted BLOB;
ALTER TABLE projects ADD COLUMN fuel_cost_encrypted BLOB;
ALTER TABLE projects ADD COLUMN lcoe_encrypted BLOB;

-- ===========================================================================
-- CLIENT_PROFILES: Add Encrypted CRM Fields (NED Team Access Required)
-- ===========================================================================

ALTER TABLE client_profiles ADD COLUMN relationship_strength_encrypted BLOB;
ALTER TABLE client_profiles ADD COLUMN relationship_notes_encrypted BLOB;
ALTER TABLE client_profiles ADD COLUMN client_priority_encrypted BLOB;
ALTER TABLE client_profiles ADD COLUMN client_status_encrypted BLOB;

-- ===========================================================================
-- ROUNDTABLE_HISTORY: Add Encrypted Meeting Notes (NED Team Access Required)
-- ===========================================================================

ALTER TABLE roundtable_history ADD COLUMN discussion_encrypted BLOB;
ALTER TABLE roundtable_history ADD COLUMN action_items_encrypted BLOB;
ALTER TABLE roundtable_history ADD COLUMN next_steps_encrypted BLOB;
ALTER TABLE roundtable_history ADD COLUMN client_near_term_focus_encrypted BLOB;
ALTER TABLE roundtable_history ADD COLUMN mpr_work_targets_encrypted BLOB;

-- ===========================================================================
-- COMPANY_ROLE_ASSIGNMENTS: Add Encrypted Notes (Confidential - when flagged)
-- ===========================================================================

ALTER TABLE company_role_assignments ADD COLUMN notes_encrypted BLOB;

-- ===========================================================================
-- INTERNAL_EXTERNAL_LINKS: Add Encrypted Relationship Data (NED Team Access)
-- ===========================================================================

ALTER TABLE internal_external_links ADD COLUMN relationship_strength_encrypted BLOB;
ALTER TABLE internal_external_links ADD COLUMN notes_encrypted BLOB;

-- ===========================================================================
-- SCHEMA VERSION UPDATE
-- ===========================================================================

UPDATE schema_version SET version = 13 WHERE version = 12;
INSERT OR IGNORE INTO schema_version_history (version, description, applied_by, applied_date)
VALUES (
    13,
    'Add encrypted columns for field-level encryption (capex, opex, relationship_notes, etc.)',
    'system',
    datetime('now')
);

-- ===========================================================================
-- MIGRATION NOTES
-- ===========================================================================
--
-- This migration adds encrypted BLOB columns for sensitive data:
--
-- CONFIDENTIAL ACCESS fields (financial data):
--   - projects: capex, opex, fuel_cost, lcoe
--   - company_role_assignments: notes (when is_confidential=True)
--
-- NED TEAM ACCESS fields (internal assessments):
--   - client_profiles: relationship_strength, relationship_notes, client_priority, client_status
--   - roundtable_history: ALL discussion/planning fields
--   - internal_external_links: relationship_strength, notes
--
-- OLD COLUMNS REMAIN:
--   - Original text/float columns are NOT dropped for safety
--   - Data migration script will populate encrypted columns from old columns
--   - After validation, old columns can be dropped in future migration
--
-- ENCRYPTION METHOD:
--   - Uses Fernet (symmetric encryption) from cryptography library
--   - Master keys stored in environment variables (CONFIDENTIAL_DATA_KEY, NED_TEAM_KEY)
--   - SQLAlchemy models use EncryptedField properties for automatic enc/dec
--
-- NEXT STEPS:
--   1. Run this migration to add columns
--   2. Run scripts/migrate_data_to_encrypted.py to encrypt existing data
--   3. Test that encrypted fields work correctly
--   4. Optionally drop old columns after validation period
--
-- ===========================================================================
