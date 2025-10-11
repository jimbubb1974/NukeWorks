-- Migration 009: Remove sector, headquarters_region from companies table
-- Created: 2025-10-10
-- Description: Removes unused geographic and sector classification fields
-- Version: 9

-- Temporarily disable foreign key constraints for table recreation
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- SQLite doesn't support DROP COLUMN directly in older versions
-- We need to create a new table, copy data, drop old table, rename new table

-- Step 0: Clean up any previous failed migration attempts
DROP TABLE IF EXISTS companies_new;

-- Step 1: Create new companies table without sector and headquarters_region
CREATE TABLE companies_new (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    company_type TEXT,
    website TEXT,
    headquarters_country TEXT,
    is_mpr_client BOOLEAN NOT NULL DEFAULT 0,
    is_internal BOOLEAN NOT NULL DEFAULT 0,
    notes TEXT,
    created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    modified_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES users (user_id),
    FOREIGN KEY (modified_by) REFERENCES users (user_id),
    CONSTRAINT uq_companies_name UNIQUE (company_name)
);

-- Step 2: Copy data from old table to new table (excluding sector and headquarters_region)
INSERT INTO companies_new (
    company_id,
    company_name,
    company_type,
    website,
    headquarters_country,
    is_mpr_client,
    is_internal,
    notes,
    created_date,
    modified_date,
    created_by,
    modified_by
)
SELECT
    company_id,
    company_name,
    company_type,
    website,
    headquarters_country,
    is_mpr_client,
    is_internal,
    notes,
    COALESCE(created_date, CURRENT_TIMESTAMP),
    COALESCE(modified_date, CURRENT_TIMESTAMP),
    created_by,
    modified_by
FROM companies;

-- Step 3: Drop old table
DROP TABLE companies;

-- Step 4: Rename new table to companies
ALTER TABLE companies_new RENAME TO companies;

-- Step 5: Recreate indexes
CREATE INDEX idx_companies_name ON companies (company_name);
CREATE INDEX idx_companies_type ON companies (company_type);
CREATE INDEX idx_companies_mpr_client ON companies (is_mpr_client);

-- Re-enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Update schema version
INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (9, datetime('now'), 'system', 'Remove sector and headquarters_region from companies table');

COMMIT;
