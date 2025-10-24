-- Migration: 014_legacy_cleanup_extras.sql
-- Purpose: Extra cleanup of legacy tables, protective indexes, and housekeeping

BEGIN TRANSACTION;

-- Drop known legacy tables if any still exist (no-op if already gone)
DROP TABLE IF EXISTS owners_developers;
DROP TABLE IF EXISTS owner_developers;
DROP TABLE IF EXISTS technology_vendors;
DROP TABLE IF EXISTS vendor_preferred_constructor;
DROP TABLE IF EXISTS project_vendor_relationships;
DROP TABLE IF EXISTS project_constructor_relationships;
DROP TABLE IF EXISTS project_operator_relationships;
DROP TABLE IF EXISTS project_owner_relationships;

-- Re-assert important unique index on company_role_assignments
CREATE UNIQUE INDEX IF NOT EXISTS idx_cra_unique
  ON company_role_assignments (company_id, role_id, context_type, context_id);

-- Helpful secondary indexes (idempotent)
CREATE INDEX IF NOT EXISTS idx_company_role_company ON company_role_assignments (company_id);
CREATE INDEX IF NOT EXISTS idx_company_role_role ON company_role_assignments (role_id);
CREATE INDEX IF NOT EXISTS idx_company_role_context ON company_role_assignments (context_type, context_id);

COMMIT;

-- Optional (run separately):
-- PRAGMA optimize;
-- VACUUM;



