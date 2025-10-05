-- migrations/001_initial_schema.sql
-- Description: Initial NukeWorks database schema
-- Version: 1
-- Date: 2025-01-04
-- Author: NukeWorks Development Team

-- IMPORTANT: This migration runs within a transaction
-- If any statement fails, entire migration is rolled back

BEGIN TRANSACTION;

-- ============================================================================
-- CORE ENTITY TABLES
-- ============================================================================

-- Users table (authentication and permissions)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    has_confidential_access BOOLEAN DEFAULT 0 NOT NULL,
    is_ned_team BOOLEAN DEFAULT 0 NOT NULL,
    is_admin BOOLEAN DEFAULT 0 NOT NULL,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    last_login TIMESTAMP,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Technology Vendors table
CREATE TABLE IF NOT EXISTS technology_vendors (
    vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_vendors_name ON technology_vendors(vendor_name);
CREATE INDEX IF NOT EXISTS idx_vendors_created ON technology_vendors(created_date);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    vendor_id INTEGER NOT NULL,
    reactor_type TEXT,
    thermal_capacity REAL,
    thermal_efficiency REAL,
    burnup REAL,
    design_status TEXT,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES technology_vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_products_vendor ON products(vendor_id);
CREATE INDEX IF NOT EXISTS idx_products_type ON products(reactor_type);

-- Owners/Developers table (with CRM fields)
CREATE TABLE IF NOT EXISTS owners_developers (
    owner_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    company_type TEXT,
    target_customers TEXT,
    engagement_level TEXT,
    notes TEXT,
    last_contact_date DATE,
    last_contact_type TEXT,
    relationship_strength TEXT,
    relationship_notes TEXT,
    client_priority TEXT,
    client_status TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_owners_name ON owners_developers(company_name);
CREATE INDEX IF NOT EXISTS idx_owners_status ON owners_developers(client_status);
CREATE INDEX IF NOT EXISTS idx_owners_priority ON owners_developers(client_priority);

-- Constructors table
CREATE TABLE IF NOT EXISTS constructors (
    constructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_constructors_name ON constructors(company_name);

-- Operators table
CREATE TABLE IF NOT EXISTS operators (
    operator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_operators_name ON operators(company_name);

-- Projects table (with financial fields)
CREATE TABLE IF NOT EXISTS projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    location TEXT,
    project_status TEXT,
    licensing_approach TEXT,
    configuration TEXT,
    project_schedule TEXT,
    cod DATE,
    capex REAL,
    opex REAL,
    fuel_cost REAL,
    lcoe REAL,
    notes TEXT,
    firm_involvement TEXT,
    project_health TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(project_name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(project_status);
CREATE INDEX IF NOT EXISTS idx_projects_location ON projects(location);
CREATE INDEX IF NOT EXISTS idx_projects_cod ON projects(cod);

-- Personnel table
CREATE TABLE IF NOT EXISTS personnel (
    personnel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role TEXT,
    personnel_type TEXT,
    organization_type TEXT,
    organization_id INTEGER,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_personnel_name ON personnel(full_name);
CREATE INDEX IF NOT EXISTS idx_personnel_email ON personnel(email);
CREATE INDEX IF NOT EXISTS idx_personnel_type ON personnel(personnel_type);
CREATE INDEX IF NOT EXISTS idx_personnel_org ON personnel(organization_type, organization_id);

-- Contact Log table (CRM)
CREATE TABLE IF NOT EXISTS contact_log (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    contact_date DATE NOT NULL,
    contact_type TEXT,
    contacted_by INTEGER NOT NULL,
    contact_person_id INTEGER,
    contact_person_freetext TEXT,
    summary TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    follow_up_needed BOOLEAN DEFAULT 0 NOT NULL,
    follow_up_date DATE,
    follow_up_assigned_to INTEGER,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (contacted_by) REFERENCES personnel(personnel_id),
    FOREIGN KEY (contact_person_id) REFERENCES personnel(personnel_id),
    FOREIGN KEY (follow_up_assigned_to) REFERENCES personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_contact_log_entity ON contact_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_contact_log_date ON contact_log(contact_date);
CREATE INDEX IF NOT EXISTS idx_contact_log_followup ON contact_log(follow_up_needed, follow_up_date);
CREATE INDEX IF NOT EXISTS idx_contact_log_confidential ON contact_log(is_confidential);

-- Roundtable History table (NED Team only)
CREATE TABLE IF NOT EXISTS roundtable_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    meeting_date DATE NOT NULL,
    discussion TEXT,
    action_items TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_roundtable_entity ON roundtable_history(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_roundtable_date ON roundtable_history(meeting_date);

-- Confidential Field Flags table
CREATE TABLE IF NOT EXISTS confidential_field_flags (
    flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    is_confidential BOOLEAN DEFAULT 1 NOT NULL,
    set_by INTEGER,
    set_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (set_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_confidential_flags_record ON confidential_field_flags(table_name, record_id);

-- Audit Log table
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    changed_fields TEXT,
    old_values TEXT,
    new_values TEXT,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- Database Snapshots table
CREATE TABLE IF NOT EXISTS database_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_user_id INTEGER,
    snapshot_type TEXT,
    file_path TEXT NOT NULL,
    description TEXT,
    snapshot_size_bytes INTEGER,
    is_retained BOOLEAN DEFAULT 0 NOT NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON database_snapshots(snapshot_timestamp);
CREATE INDEX IF NOT EXISTS idx_snapshots_type ON database_snapshots(snapshot_type);
CREATE INDEX IF NOT EXISTS idx_snapshots_retained ON database_snapshots(is_retained);

-- System Settings table
CREATE TABLE IF NOT EXISTS system_settings (
    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    setting_type TEXT,
    description TEXT,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_system_settings_name ON system_settings(setting_name);

-- Schema Version table
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    applied_by TEXT,
    description TEXT
);

-- ============================================================================
-- JUNCTION TABLES (Relationships)
-- ============================================================================

-- Vendor-Supplier Relationships
CREATE TABLE IF NOT EXISTS vendor_supplier_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    component_type TEXT,
    notes TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES technology_vendors(vendor_id),
    FOREIGN KEY (supplier_id) REFERENCES technology_vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(vendor_id, supplier_id)
);

CREATE INDEX IF NOT EXISTS idx_vendor_supplier_vendor ON vendor_supplier_relationships(vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_supplier_supplier ON vendor_supplier_relationships(supplier_id);
CREATE INDEX IF NOT EXISTS idx_vendor_supplier_conf ON vendor_supplier_relationships(is_confidential);

-- Owner-Vendor Relationships
CREATE TABLE IF NOT EXISTS owner_vendor_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    relationship_type TEXT,
    notes TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners_developers(owner_id),
    FOREIGN KEY (vendor_id) REFERENCES technology_vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(owner_id, vendor_id)
);

CREATE INDEX IF NOT EXISTS idx_owner_vendor_owner ON owner_vendor_relationships(owner_id);
CREATE INDEX IF NOT EXISTS idx_owner_vendor_vendor ON owner_vendor_relationships(vendor_id);
CREATE INDEX IF NOT EXISTS idx_owner_vendor_type ON owner_vendor_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_owner_vendor_conf ON owner_vendor_relationships(is_confidential);

-- Project-Vendor Relationships
CREATE TABLE IF NOT EXISTS project_vendor_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    notes TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (vendor_id) REFERENCES technology_vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(project_id, vendor_id)
);

CREATE INDEX IF NOT EXISTS idx_project_vendor_project ON project_vendor_relationships(project_id);
CREATE INDEX IF NOT EXISTS idx_project_vendor_vendor ON project_vendor_relationships(vendor_id);
CREATE INDEX IF NOT EXISTS idx_project_vendor_conf ON project_vendor_relationships(is_confidential);

-- Project-Constructor Relationships
CREATE TABLE IF NOT EXISTS project_constructor_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    constructor_id INTEGER NOT NULL,
    notes TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(project_id, constructor_id)
);

CREATE INDEX IF NOT EXISTS idx_project_constructor_project ON project_constructor_relationships(project_id);
CREATE INDEX IF NOT EXISTS idx_project_constructor_constructor ON project_constructor_relationships(constructor_id);
CREATE INDEX IF NOT EXISTS idx_project_constructor_conf ON project_constructor_relationships(is_confidential);

-- Project-Operator Relationships
CREATE TABLE IF NOT EXISTS project_operator_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    operator_id INTEGER NOT NULL,
    notes TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (operator_id) REFERENCES operators(operator_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(project_id, operator_id)
);

CREATE INDEX IF NOT EXISTS idx_project_operator_project ON project_operator_relationships(project_id);
CREATE INDEX IF NOT EXISTS idx_project_operator_operator ON project_operator_relationships(operator_id);
CREATE INDEX IF NOT EXISTS idx_project_operator_conf ON project_operator_relationships(is_confidential);

-- Project-Owner Relationships
CREATE TABLE IF NOT EXISTS project_owner_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    notes TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (owner_id) REFERENCES owners_developers(owner_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(project_id, owner_id)
);

CREATE INDEX IF NOT EXISTS idx_project_owner_project ON project_owner_relationships(project_id);
CREATE INDEX IF NOT EXISTS idx_project_owner_owner ON project_owner_relationships(owner_id);
CREATE INDEX IF NOT EXISTS idx_project_owner_conf ON project_owner_relationships(is_confidential);

-- Vendor Preferred Constructor
CREATE TABLE IF NOT EXISTS vendor_preferred_constructor (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    constructor_id INTEGER NOT NULL,
    preference_reason TEXT,
    notes TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES technology_vendors(vendor_id),
    FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(vendor_id, constructor_id)
);

CREATE INDEX IF NOT EXISTS idx_vendor_pref_constructor_vendor ON vendor_preferred_constructor(vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_pref_constructor_constructor ON vendor_preferred_constructor(constructor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_pref_constructor_conf ON vendor_preferred_constructor(is_confidential);

-- Personnel-Entity Relationships (polymorphic)
CREATE TABLE IF NOT EXISTS personnel_entity_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    personnel_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    relationship_role TEXT,
    notes TEXT,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(personnel_id, entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_personnel_entity_personnel ON personnel_entity_relationships(personnel_id);
CREATE INDEX IF NOT EXISTS idx_personnel_entity_entity ON personnel_entity_relationships(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_personnel_entity_conf ON personnel_entity_relationships(is_confidential);

-- Entity Team Members (CRM assignments)
CREATE TABLE IF NOT EXISTS entity_team_members (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    personnel_id INTEGER NOT NULL,
    assignment_type TEXT,
    assigned_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id),
    UNIQUE(entity_type, entity_id, personnel_id)
);

CREATE INDEX IF NOT EXISTS idx_entity_team_entity ON entity_team_members(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_team_personnel ON entity_team_members(personnel_id);

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (1, datetime('now'), 'system', 'Initial schema creation - complete NukeWorks database');

-- ============================================================================
-- COMMIT TRANSACTION
-- ============================================================================

COMMIT;
