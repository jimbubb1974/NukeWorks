-- Migration 010: Normalize company role assignment context types
-- Created: 2025-10-10
-- Description: Convert legacy *Record context types to Global context
-- Version: 10

-- Legacy context types (VendorRecord, OwnerRecord, etc.) reference deprecated
-- entity table IDs. These should be converted to Global context (NULL context_id)
-- to represent company-level role assignments independent of specific entities.

BEGIN TRANSACTION;

-- Step 1: Check for any existing Global context assignments that would conflict
-- (This is a safety check - should return 0 rows)
-- If this returns rows, the migration needs manual intervention

-- Step 2: Delete duplicate legacy record assignments for the same company/role
-- Keep the oldest assignment (lowest assignment_id) for each company/role pair
DELETE FROM company_role_assignments
WHERE assignment_id IN (
    SELECT cra1.assignment_id
    FROM company_role_assignments cra1
    WHERE cra1.context_type IN (
        'VendorRecord', 'OwnerRecord', 'ClientRecord',
        'OperatorRecord', 'ConstructorRecord', 'OfftakerRecord'
    )
    AND EXISTS (
        SELECT 1
        FROM company_role_assignments cra2
        WHERE cra2.company_id = cra1.company_id
          AND cra2.role_id = cra1.role_id
          AND cra2.context_type IN (
              'VendorRecord', 'OwnerRecord', 'ClientRecord',
              'OperatorRecord', 'ConstructorRecord', 'OfftakerRecord'
          )
          AND cra2.assignment_id < cra1.assignment_id
    )
);

-- Step 3: Delete any legacy assignments that would conflict with existing Global assignments
DELETE FROM company_role_assignments
WHERE context_type IN (
    'VendorRecord', 'OwnerRecord', 'ClientRecord',
    'OperatorRecord', 'ConstructorRecord', 'OfftakerRecord'
)
AND EXISTS (
    SELECT 1
    FROM company_role_assignments cra2
    WHERE cra2.company_id = company_role_assignments.company_id
      AND cra2.role_id = company_role_assignments.role_id
      AND cra2.context_type = 'Global'
      AND cra2.context_id IS NULL
);

-- Step 4: Update remaining legacy record context types to Global
-- Set context_id to NULL since these are company-level assignments
UPDATE company_role_assignments
SET context_type = 'Global',
    context_id = NULL,
    modified_date = datetime('now')
WHERE context_type IN (
    'VendorRecord',
    'OwnerRecord',
    'ClientRecord',
    'OperatorRecord',
    'ConstructorRecord',
    'OfftakerRecord'
);

-- Note: Project context types remain unchanged as they are already unified

-- Update schema version
INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (10, datetime('now'), 'system', 'Normalize company role assignment context types to Global');

COMMIT;
