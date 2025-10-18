-- Migration: Add personnel_relationships table
-- Purpose: Enable linking internal MPR personnel with external contacts
-- Date: 2025-10-10
-- Version: 8

BEGIN TRANSACTION;

-- Create personnel_relationships table
CREATE TABLE IF NOT EXISTS personnel_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    internal_personnel_id INTEGER NOT NULL,
    external_personnel_id INTEGER NOT NULL,
    relationship_type TEXT,  -- e.g., 'Primary Contact', 'Technical Contact', 'Business Contact'
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    modified_by INTEGER,
    FOREIGN KEY (internal_personnel_id) REFERENCES internal_personnel(personnel_id) ON DELETE CASCADE,
    FOREIGN KEY (external_personnel_id) REFERENCES external_personnel(personnel_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_personnel_relationships_internal ON personnel_relationships(internal_personnel_id);
CREATE INDEX IF NOT EXISTS idx_personnel_relationships_external ON personnel_relationships(external_personnel_id);
CREATE INDEX IF NOT EXISTS idx_personnel_relationships_type ON personnel_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_personnel_relationships_active ON personnel_relationships(is_active);

-- Prevent duplicate relationships
CREATE UNIQUE INDEX IF NOT EXISTS idx_personnel_relationships_unique
ON personnel_relationships(internal_personnel_id, external_personnel_id);

-- Update schema version
INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (8, datetime('now'), 'system', 'Add personnel_relationships table');

COMMIT;




