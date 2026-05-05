-- Add Engineer as a first-class company role.
-- This is a data/catalog migration, not a schema migration.

BEGIN TRANSACTION;

INSERT INTO company_roles (role_code, role_label, description, is_active, created_date)
SELECT
    'engineer',
    'Engineer',
    'Provides engineering, design, architect-engineer, or owner''s engineer services for projects',
    1,
    datetime('now')
WHERE NOT EXISTS (
    SELECT 1 FROM company_roles WHERE role_code = 'engineer'
);

INSERT INTO schema_version (version, applied_date, applied_by, description)
SELECT
    20,
    datetime('now'),
    'system',
    'Add Engineer company role'
WHERE NOT EXISTS (
    SELECT 1 FROM schema_version WHERE version = 20
);

COMMIT;
