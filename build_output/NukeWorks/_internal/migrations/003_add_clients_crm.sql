-- migrations/003_add_clients_crm.sql
-- Description: Add Clients table and CRM features for roundtable meetings
-- Version: 3
-- Date: 2025-10-05
-- Author: NukeWorks Development Team

-- IMPORTANT: This migration runs within a transaction
-- If any statement fails, entire migration is rolled back

BEGIN TRANSACTION;

-- ============================================================================
-- CREATE CLIENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    client_type TEXT,  -- Utility, IPP, Government, Consulting, Other
    notes TEXT,

    -- MPR Relationship
    mpr_primary_poc INTEGER,  -- FK to personnel (internal)
    mpr_secondary_poc INTEGER,  -- FK to personnel (internal)

    -- Contact Tracking (All Users)
    last_contact_date DATE,
    last_contact_type TEXT,  -- In-person, Phone, Email, Video
    last_contact_by INTEGER,  -- FK to personnel (internal)
    last_contact_notes TEXT,
    next_planned_contact_date DATE,
    next_planned_contact_type TEXT,
    next_planned_contact_assigned_to INTEGER,  -- FK to personnel (internal)

    -- Internal Assessment (NED Team Only)
    relationship_strength TEXT,  -- Strong, Good, Needs Attention, At Risk, New
    relationship_notes TEXT,  -- Internal strategy notes
    client_priority TEXT,  -- High, Medium, Low, Strategic, Opportunistic
    client_status TEXT,  -- Active, Warm, Cold, Prospective

    -- Standard audit fields
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,

    FOREIGN KEY (mpr_primary_poc) REFERENCES personnel(personnel_id),
    FOREIGN KEY (mpr_secondary_poc) REFERENCES personnel(personnel_id),
    FOREIGN KEY (last_contact_by) REFERENCES personnel(personnel_id),
    FOREIGN KEY (next_planned_contact_assigned_to) REFERENCES personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(client_name);
CREATE INDEX IF NOT EXISTS idx_clients_priority ON clients(client_priority);
CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(client_status);
CREATE INDEX IF NOT EXISTS idx_clients_mpr_poc ON clients(mpr_primary_poc);
CREATE INDEX IF NOT EXISTS idx_clients_created ON clients(created_date);

-- ============================================================================
-- CREATE CLIENT RELATIONSHIP TABLES
-- ============================================================================

-- Link Clients to Owners/Developers (when a client IS an owner/developer)
CREATE TABLE IF NOT EXISTS client_owner_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (owner_id) REFERENCES owners_developers(owner_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(client_id, owner_id)
);

CREATE INDEX IF NOT EXISTS idx_client_owner_client ON client_owner_relationships(client_id);
CREATE INDEX IF NOT EXISTS idx_client_owner_owner ON client_owner_relationships(owner_id);
CREATE INDEX IF NOT EXISTS idx_client_owner_conf ON client_owner_relationships(is_confidential);

-- Link Clients to Projects (direct relationship)
CREATE TABLE IF NOT EXISTS client_project_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    relationship_type TEXT,  -- Lead, Partner, Consultant, Advisor
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(client_id, project_id)
);

CREATE INDEX IF NOT EXISTS idx_client_project_client ON client_project_relationships(client_id);
CREATE INDEX IF NOT EXISTS idx_client_project_project ON client_project_relationships(project_id);
CREATE INDEX IF NOT EXISTS idx_client_project_conf ON client_project_relationships(is_confidential);

-- Link Clients to Technology Vendors (client interest in specific technologies)
CREATE TABLE IF NOT EXISTS client_vendor_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (vendor_id) REFERENCES technology_vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(client_id, vendor_id)
);

CREATE INDEX IF NOT EXISTS idx_client_vendor_client ON client_vendor_relationships(client_id);
CREATE INDEX IF NOT EXISTS idx_client_vendor_vendor ON client_vendor_relationships(vendor_id);
CREATE INDEX IF NOT EXISTS idx_client_vendor_conf ON client_vendor_relationships(is_confidential);

-- Link Clients to Operators (when a client IS an operator)
CREATE TABLE IF NOT EXISTS client_operator_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    operator_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (operator_id) REFERENCES operators(operator_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(client_id, operator_id)
);

CREATE INDEX IF NOT EXISTS idx_client_operator_client ON client_operator_relationships(client_id);
CREATE INDEX IF NOT EXISTS idx_client_operator_operator ON client_operator_relationships(operator_id);
CREATE INDEX IF NOT EXISTS idx_client_operator_conf ON client_operator_relationships(is_confidential);

-- Link Clients to Personnel (key personnel at the client organization)
CREATE TABLE IF NOT EXISTS client_personnel_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    personnel_id INTEGER NOT NULL,  -- FK to personnel (external contacts)
    role_at_client TEXT,  -- CEO, VP Nuclear, Engineering Director, etc.
    is_primary_contact BOOLEAN DEFAULT 0 NOT NULL,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(client_id, personnel_id)
);

CREATE INDEX IF NOT EXISTS idx_client_personnel_client ON client_personnel_relationships(client_id);
CREATE INDEX IF NOT EXISTS idx_client_personnel_personnel ON client_personnel_relationships(personnel_id);
CREATE INDEX IF NOT EXISTS idx_client_personnel_primary ON client_personnel_relationships(is_primary_contact);
CREATE INDEX IF NOT EXISTS idx_client_personnel_conf ON client_personnel_relationships(is_confidential);

-- ============================================================================
-- ENHANCE ROUNDTABLE_HISTORY FOR CRM
-- ============================================================================

-- Add structured fields for roundtable meetings
-- Note: The existing 'discussion' and 'action_items' fields remain for general notes
ALTER TABLE roundtable_history ADD COLUMN next_steps TEXT;
ALTER TABLE roundtable_history ADD COLUMN client_near_term_focus TEXT;
ALTER TABLE roundtable_history ADD COLUMN mpr_work_targets TEXT;

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (3, datetime('now'), 'system', 'Add Clients table and CRM features for roundtable meetings');

-- ============================================================================
-- COMMIT TRANSACTION
-- ============================================================================

COMMIT;
