-- migrations/005_company_unification.sql
-- Description: Introduce unified company schema and supporting relationship tables
-- Version: 5
-- Date: 2025-03-05
-- Author: NukeWorks Development Team

BEGIN TRANSACTION;

-- ============================================================================
-- COMPANIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    company_type TEXT,
    sector TEXT,
    website TEXT,
    headquarters_country TEXT,
    headquarters_region TEXT,
    is_mpr_client BOOLEAN DEFAULT 0 NOT NULL,
    is_internal BOOLEAN DEFAULT 0 NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_companies_name ON companies(company_name);
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(company_name);
CREATE INDEX IF NOT EXISTS idx_companies_type ON companies(company_type);
CREATE INDEX IF NOT EXISTS idx_companies_mpr_client ON companies(is_mpr_client);
CREATE INDEX IF NOT EXISTS idx_companies_created ON companies(created_date);

-- ============================================================================
-- COMPANY ROLES CATALOG
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code TEXT NOT NULL UNIQUE,
    role_label TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_company_roles_active ON company_roles(is_active);
CREATE INDEX IF NOT EXISTS idx_company_roles_label ON company_roles(role_label);

-- Seed core roles (idempotent inserts)
INSERT INTO company_roles (role_code, role_label, description, is_active)
    SELECT 'vendor', 'Technology Vendor', 'Provides nuclear technology/products', 1
    WHERE NOT EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'vendor');
INSERT INTO company_roles (role_code, role_label, description, is_active)
    SELECT 'constructor', 'Constructor', 'Provides EPC or construction services', 1
    WHERE NOT EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'constructor');
INSERT INTO company_roles (role_code, role_label, description, is_active)
    SELECT 'developer', 'Owner / Developer', 'Owns or develops nuclear projects', 1
    WHERE NOT EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'developer');
INSERT INTO company_roles (role_code, role_label, description, is_active)
    SELECT 'operator', 'Operator', 'Operates nuclear facilities', 1
    WHERE NOT EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'operator');
INSERT INTO company_roles (role_code, role_label, description, is_active)
    SELECT 'client', 'MPR Client', 'Engages MPR for consulting services', 1
    WHERE NOT EXISTS (SELECT 1 FROM company_roles WHERE role_code = 'client');

-- ============================================================================
-- COMPANY ROLE ASSIGNMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_role_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    context_type TEXT,
    context_id INTEGER,
    is_primary BOOLEAN DEFAULT 0 NOT NULL,
    start_date DATE,
    end_date DATE,
    is_confidential BOOLEAN DEFAULT 0 NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (role_id) REFERENCES company_roles(role_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(company_id, role_id, context_type, context_id)
);

CREATE INDEX IF NOT EXISTS idx_company_role_company ON company_role_assignments(company_id);
CREATE INDEX IF NOT EXISTS idx_company_role_role ON company_role_assignments(role_id);
CREATE INDEX IF NOT EXISTS idx_company_role_context ON company_role_assignments(context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_company_role_primary ON company_role_assignments(is_primary);
CREATE INDEX IF NOT EXISTS idx_company_role_confidential ON company_role_assignments(is_confidential);

-- ============================================================================
-- CLIENT PROFILES (CRM EXTENSION)
-- ============================================================================

CREATE TABLE IF NOT EXISTS client_profiles (
    company_id INTEGER PRIMARY KEY,
    relationship_strength TEXT,
    relationship_notes TEXT,
    client_priority TEXT,
    client_status TEXT,
    last_contact_date DATE,
    last_contact_type TEXT,
    last_contact_by INTEGER,
    next_planned_contact_date DATE,
    next_planned_contact_type TEXT,
    next_planned_contact_assigned_to INTEGER,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (last_contact_by) REFERENCES personnel(personnel_id),
    FOREIGN KEY (next_planned_contact_assigned_to) REFERENCES personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_client_profiles_priority ON client_profiles(client_priority);
CREATE INDEX IF NOT EXISTS idx_client_profiles_status ON client_profiles(client_status);
CREATE INDEX IF NOT EXISTS idx_client_profiles_last_contact ON client_profiles(last_contact_date);

-- ============================================================================
-- PERSON ↔ COMPANY AFFILIATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS person_company_affiliations (
    affiliation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    title TEXT,
    department TEXT,
    is_primary BOOLEAN DEFAULT 0 NOT NULL,
    start_date DATE,
    end_date DATE,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES personnel(personnel_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(person_id, company_id, title, start_date)
);

CREATE INDEX IF NOT EXISTS idx_person_company_person ON person_company_affiliations(person_id);
CREATE INDEX IF NOT EXISTS idx_person_company_company ON person_company_affiliations(company_id);
CREATE INDEX IF NOT EXISTS idx_person_company_primary ON person_company_affiliations(is_primary);

-- ============================================================================
-- INTERNAL ↔ EXTERNAL RELATIONSHIPS
-- ============================================================================

CREATE TABLE IF NOT EXISTS internal_external_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    internal_person_id INTEGER NOT NULL,
    external_person_id INTEGER NOT NULL,
    company_id INTEGER,
    relationship_type TEXT,
    relationship_strength TEXT,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (internal_person_id) REFERENCES personnel(personnel_id),
    FOREIGN KEY (external_person_id) REFERENCES personnel(personnel_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id),
    UNIQUE(internal_person_id, external_person_id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_internal_external_internal ON internal_external_links(internal_person_id);
CREATE INDEX IF NOT EXISTS idx_internal_external_external ON internal_external_links(external_person_id);
CREATE INDEX IF NOT EXISTS idx_internal_external_company ON internal_external_links(company_id);

-- Update schema version
INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (5, datetime('now'), 'system', 'Introduce unified company schema and supporting relationship tables');

COMMIT;
