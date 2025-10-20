-- 007_remove_legacy_owner_role.sql
-- Purpose: Remove legacy 'owner' role_code in favor of unified 'developer' role_code
-- Safe/idempotent for SQLite. Assumes company_roles and company_role_assignments exist.
-- Version: 7

BEGIN TRANSACTION;

-- Ensure a 'developer' role exists (seed if missing)
INSERT INTO company_roles (role_code, role_label, description, is_active)
    SELECT 'developer', 'Owner / Developer', 'Owns or develops nuclear projects', 1
    WHERE NOT EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'developer');

-- Delete any 'owner' role assignments that would conflict with existing 'developer' assignments
-- (same company_id, context_type, context_id but different role)
DELETE FROM company_role_assignments
WHERE role_id IN (SELECT role_id FROM company_roles WHERE role_code = 'owner')
  AND EXISTS (
    SELECT 1 FROM company_role_assignments cra2
    WHERE cra2.company_id = company_role_assignments.company_id
      AND cra2.role_id IN (SELECT role_id FROM company_roles WHERE role_code = 'developer')
      AND cra2.context_type = company_role_assignments.context_type
      AND COALESCE(cra2.context_id, 0) = COALESCE(company_role_assignments.context_id, 0)
  );

-- Repoint remaining 'owner' assignments to 'developer' role
UPDATE company_role_assignments
SET role_id = (SELECT role_id FROM company_roles WHERE role_code = 'developer')
WHERE role_id IN (SELECT role_id FROM company_roles WHERE role_code = 'owner')
  AND EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'developer');

-- Remove the legacy 'owner' role row if present
DELETE FROM company_roles WHERE role_code = 'owner';

-- Update schema version
INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (7, datetime('now'), 'system', 'Remove legacy owner role in favor of developer role');

COMMIT;










