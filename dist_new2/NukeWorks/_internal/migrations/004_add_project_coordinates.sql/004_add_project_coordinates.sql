-- 004_add_project_coordinates.sql
-- Description: Add latitude/longitude columns and supporting index for project map view
-- Version: 4
-- Date: 2026-02-11
-- Author: Codex Agent

BEGIN TRANSACTION;

-- ============================================================================
-- MIGRATION STATEMENTS
-- ============================================================================

ALTER TABLE Projects ADD COLUMN latitude REAL;
ALTER TABLE Projects ADD COLUMN longitude REAL;

-- Composite index to accelerate map queries filtering by lat/lon presence
CREATE INDEX IF NOT EXISTS idx_projects_lat_lon ON Projects(latitude, longitude);

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (4, datetime('now'), 'system', 'Add project latitude/longitude fields and index');

-- ============================================================================
-- COMMIT TRANSACTION
-- ============================================================================

COMMIT;
