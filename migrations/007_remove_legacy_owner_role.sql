-- 007_remove_legacy_owner_role.sql
-- Purpose: Remove legacy 'owner' role_code in favor of unified 'developer' role_code
-- Safe/idempotent for SQLite. Assumes company_roles and company_role_assignments exist.

BEGIN TRANSACTION;

-- Ensure a 'developer' role exists (seed if missing)
INSERT INTO company_roles (role_code, role_label, description, is_active)
    SELECT 'developer', 'Owner / Developer', 'Owns or develops nuclear projects', 1
    WHERE NOT EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'developer');

-- Repoint any assignments that still reference the legacy 'owner' role
UPDATE company_role_assignments
SET role_id = (SELECT role_id FROM company_roles WHERE role_code = 'developer')
WHERE role_id IN (SELECT role_id FROM company_roles WHERE role_code = 'owner')
  AND EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'developer');

-- Remove the legacy 'owner' role row if present
DELETE FROM company_roles WHERE role_code = 'owner';

COMMIT;


