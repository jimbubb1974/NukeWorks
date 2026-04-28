-- Migration 017: Add client_tier encrypted field to client_profiles
-- Adds Tier 1-4 classification for MPR clients (NED Team only, encrypted)

ALTER TABLE client_profiles ADD COLUMN client_tier_encrypted BLOB;

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (
    17,
    datetime('now'),
    'system',
    'Add client_tier_encrypted column to client_profiles for Tier 1-4 classification'
);
