-- Migration 017: Add client_tier encrypted field to client_profiles
-- Adds Tier 1-4 classification for MPR clients (NED Team only, encrypted)

ALTER TABLE client_profiles ADD COLUMN client_tier_encrypted BLOB;

UPDATE schema_version SET version = 17;
