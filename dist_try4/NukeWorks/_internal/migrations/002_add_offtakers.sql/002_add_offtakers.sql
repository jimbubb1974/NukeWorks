-- migrations/002_add_offtakers.sql
-- Description: Add energy off-takers and project linkage tables
-- Version: 2
-- Date: 2025-01-09
-- Author: NukeWorks Development Team

-- IMPORTANT: This migration runs within a transaction
-- If any statement fails, entire migration is rolled back

BEGIN TRANSACTION;

-- ============================================================================
-- CREATE OFFTAKERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS offtakers (
    offtaker_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_name TEXT NOT NULL,
    sector TEXT,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_offtaker_name ON offtakers(organization_name);
CREATE INDEX IF NOT EXISTS idx_offtaker_created ON offtakers(created_date);

-- ============================================================================
-- CREATE PROJECT-OFFTAKER RELATIONSHIP TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_offtaker_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    offtaker_id INTEGER NOT NULL,
    agreement_type TEXT,
    contracted_volume TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (offtaker_id) REFERENCES offtakers(offtaker_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(project_id, offtaker_id)
);

CREATE INDEX IF NOT EXISTS idx_project_offtaker_project ON project_offtaker_relationships(project_id);
CREATE INDEX IF NOT EXISTS idx_project_offtaker_offtaker ON project_offtaker_relationships(offtaker_id);
CREATE INDEX IF NOT EXISTS idx_project_offtaker_conf ON project_offtaker_relationships(is_confidential);

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (2, datetime('now'), 'system', 'Add energy off-takers and project linkage tables');

-- ============================================================================
-- COMMIT TRANSACTION
-- ============================================================================

COMMIT;
