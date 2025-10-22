-- Migration: 013_owner_developer_cleanup.sql
-- Purpose: Normalize legacy 'owner' role to 'developer', deduplicate, drop legacy tables, and enforce uniqueness

BEGIN TRANSACTION;

-- 1) Ensure unified 'developer' role exists
INSERT INTO company_roles (role_code, role_label, description, is_active)
SELECT 'developer', 'Owner / Developer', 'Owns or develops nuclear projects', 1
WHERE NOT EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'developer');

-- 2) Remap assignments from legacy 'owner' to unified 'developer'
--    First, identify role_ids
-- 3) Delete collisions: owner rows that duplicate existing developer rows
DELETE FROM company_role_assignments
WHERE role_id = (SELECT role_id FROM company_roles WHERE role_code = 'owner')
  AND EXISTS (
    SELECT 1 FROM company_role_assignments cra2
    WHERE cra2.company_id = company_role_assignments.company_id
      AND cra2.context_type = company_role_assignments.context_type
      AND cra2.context_id = company_role_assignments.context_id
      AND cra2.role_id = (SELECT role_id FROM company_roles WHERE role_code = 'developer')
  );

-- 4) Repoint remaining owner rows to developer
UPDATE company_role_assignments
SET role_id = (SELECT role_id FROM company_roles WHERE role_code = 'developer')
WHERE role_id = (SELECT role_id FROM company_roles WHERE role_code = 'owner')
  AND EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'developer');

-- 5) Drop legacy 'owner' role row (safe if null or not present)
DELETE FROM company_roles WHERE role_code = 'owner';

-- 6) Drop lingering legacy tables (no-op if already dropped)
DROP TABLE IF EXISTS owners_developers;
DROP TABLE IF EXISTS owner_developers;
DROP TABLE IF EXISTS technology_vendors;  -- legacy
DROP TABLE IF EXISTS vendor_preferred_constructor;  -- legacy

-- 7) Add protective uniqueness index (ignore if exists)
-- SQLite lacks IF NOT EXISTS for CREATE UNIQUE INDEX on older versions; use name check
-- Attempt create; ignore error if already exists
-- Note: Some SQLite shells support `CREATE UNIQUE INDEX IF NOT EXISTS` – keep simple here
CREATE UNIQUE INDEX IF NOT EXISTS idx_cra_unique
  ON company_role_assignments (company_id, role_id, context_type, context_id);

COMMIT;

-- Optional: Integrity checks
-- PRAGMA foreign_keys=ON;
-- PRAGMA integrity_check;
-- VACUUM;  -- run separately as it cannot be inside a transaction in some environments

