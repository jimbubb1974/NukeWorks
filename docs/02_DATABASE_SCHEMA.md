# 02_DATABASE_SCHEMA.md - Core Entity Tables (Unified Schema)

**Document Version:** 2.0
**Last Updated:** October 7, 2025
**Schema Version:** 6 (Unified Company Model)

**Related Documents:**
- `03_DATABASE_RELATIONSHIPS.md` - Junction tables (LEGACY - needs update)
- `04_DATA_DICTIONARY.md` - Field definitions and enums
- `05_PERMISSION_SYSTEM.md` - Permission-related tables
- `02_DATABASE_SCHEMA_LEGACY.md` - **ARCHIVED** - Pre-unification schema (v1.0)
- `company_unification_plan.md` - Design rationale for unified schema
- `company_refactor_status.md` - Migration status

---

## ⚠️ IMPORTANT: Schema Refactoring in Progress

This document describes the **NEW unified company schema** (schema version 5+).

**Current State (as of October 2025):**
- ✅ New unified tables exist in database (migration 005)
- ✅ New schema is actively used by dashboard, navigation, network diagrams
- ⚠️ Legacy tables still exist for backward compatibility
- ⚠️ Some code still writes to both old and new schemas
- 🎯 **Goal:** Complete migration to use ONLY the new schema

See `company_refactor_status.md` for current migration progress.

---

## Table of Contents

### Core Business Entities (NEW UNIFIED SCHEMA)
1. [Companies](#companies) - **NEW** - Unified company table
2. [Company_Roles](#company_roles) - **NEW** - Role catalog
3. [Company_Role_Assignments](#company_role_assignments) - **NEW** - Company roles with context
4. [Client_Profiles](#client_profiles) - **NEW** - CRM extension for clients
5. [Person_Company_Affiliations](#person_company_affiliations) - **NEW** - Personnel affiliations

### Legacy Tables (DEPRECATED - To Be Removed)
- ~~Technology_Vendors~~ - Use Companies with role='vendor'
- ~~Owners_Developers~~ - Use Companies with role='developer'
- ~~Operators~~ - Use Companies with role='operator'
- ~~Constructors~~ - Use Companies with role='constructor'
- ~~Offtakers~~ - Use Companies with role='offtaker'

### Other Core Tables (Unchanged)
6. [Products](#products) - Reactor designs
7. [Projects](#projects) - Nuclear project sites
8. [Personnel](#personnel) - People (internal & external)
9. [Users](#users) - Application users

### Support Tables (Unchanged)
10. [Contact_Log](#contact_log)
11. [Roundtable_History](#roundtable_history)
12. [Confidential_Field_Flags](#confidential_field_flags)
13. [Audit_Log](#audit_log)
14. [Database_Snapshots](#database_snapshots)
15. [System_Settings](#system_settings)
16. [Schema_Version](#schema_version)

---

## Format Convention

Each table follows this structure:
- **Purpose** - What this table represents
- **SQL Definition** - Complete CREATE TABLE statement
- **Field Reference** - Table of all fields with descriptions
- **Relationships** - Foreign keys and related tables
- **Business Rules** - Constraints and validation
- **Indexes** - Recommended indexes for performance

---

# NEW UNIFIED SCHEMA

## Companies

**Purpose:** Central table for ALL organizations (vendors, owners, operators, constructors, clients, etc.)

Replaces the legacy separate tables for each company type. A company can have multiple roles assigned via the `company_role_assignments` table.

**SQL Definition:**
```sql
CREATE TABLE companies (
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
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| company_id | INTEGER | No | Auto | Primary key, unique identifier |
| company_name | TEXT | No | - | Company name (e.g., "NuScale Power", "Duke Energy") |
| company_type | TEXT | Yes | NULL | General type (e.g., "Technology Provider", "Utility", "IPP") |
| sector | TEXT | Yes | NULL | Industry sector |
| website | TEXT | Yes | NULL | Company website URL |
| headquarters_country | TEXT | Yes | NULL | HQ country |
| headquarters_region | TEXT | Yes | NULL | HQ region/state |
| is_mpr_client | BOOLEAN | No | 0 | Whether this company is an MPR client |
| is_internal | BOOLEAN | No | 0 | Whether this is your own organization |
| notes | TEXT | Yes | NULL | Freeform notes |
| created_by | INTEGER | Yes | - | FK to Users - who created this record |
| created_date | TIMESTAMP | No | NOW | When record was created |
| modified_by | INTEGER | Yes | - | FK to Users - who last modified |
| modified_date | TIMESTAMP | Yes | - | When last modified |

**Relationships:**
- Has many: CompanyRoleAssignments (1:N) - defines roles this company plays
- Has many: PersonCompanyAffiliations (1:N) - personnel who work here
- Has one: ClientProfile (1:1) - if is_mpr_client = true
- Has many: InternalExternalLinks (1:N) - relationship mappings

**Business Rules:**
- company_name should be unique (indexed)
- Companies can have multiple roles (vendor, operator, developer all at once)
- Roles are assigned via `company_role_assignments` table
- If is_mpr_client = true, should have entry in `client_profiles`
- All text fields should be trimmed before save

**Indexes:**
```sql
CREATE UNIQUE INDEX uq_companies_name ON companies(company_name);
CREATE INDEX idx_companies_name ON companies(company_name);
CREATE INDEX idx_companies_type ON companies(company_type);
CREATE INDEX idx_companies_mpr_client ON companies(is_mpr_client);
CREATE INDEX idx_companies_created ON companies(created_date);
```

**Migration Note:**
- Data migrated from legacy tables via `scripts/backfill_companies.py`
- Legacy sync functions in `app/services/company_sync.py` maintain both schemas during transition

---

## Company_Roles

**Purpose:** Catalog of roles that companies can play (vendor, operator, developer, etc.)

This is a reference table with predefined roles. Supports future extensibility.

**SQL Definition:**
```sql
CREATE TABLE company_roles (
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
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| role_id | INTEGER | No | Auto | Primary key |
| role_code | TEXT | No | - | Unique code (e.g., 'vendor', 'operator', 'developer') |
| role_label | TEXT | No | - | Display name (e.g., 'Technology Vendor') |
| description | TEXT | Yes | NULL | Role description |
| is_active | BOOLEAN | No | 1 | Whether this role is currently used |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Predefined Roles:**
```sql
INSERT INTO company_roles (role_code, role_label, description, is_active) VALUES
('vendor', 'Technology Vendor', 'Provides nuclear technology/products', 1),
('constructor', 'Constructor', 'Provides EPC or construction services', 1),
('developer', 'Owner / Developer', 'Owns or develops nuclear projects', 1),
('operator', 'Operator', 'Operates nuclear facilities', 1),
('offtaker', 'Off-taker', 'Purchases energy from nuclear projects', 1),
('client', 'MPR Client', 'Engages MPR for consulting services', 1);
```

**Relationships:**
- Has many: CompanyRoleAssignments (1:N)

**Business Rules:**
- role_code must be unique and lowercase
- Cannot delete roles that have active assignments
- Use is_active = false to deprecate roles instead of deleting

**Indexes:**
```sql
CREATE INDEX idx_company_roles_active ON company_roles(is_active);
CREATE INDEX idx_company_roles_label ON company_roles(role_label);
```

---

## Company_Role_Assignments

**Purpose:** Assign roles to companies, optionally scoped to specific contexts (projects, etc.)

This table enables:
- A company to have multiple roles (e.g., Holtec is both a vendor and an operator)
- Roles to be context-specific (e.g., "NuScale is the vendor for Project X")
- Temporal tracking (role start/end dates)

**SQL Definition:**
```sql
CREATE TABLE company_role_assignments (
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
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| assignment_id | INTEGER | No | Auto | Primary key |
| company_id | INTEGER | No | - | FK to companies |
| role_id | INTEGER | No | - | FK to company_roles |
| context_type | TEXT | Yes | NULL | Context type (e.g., 'Project', NULL for general) |
| context_id | INTEGER | Yes | NULL | Context ID (e.g., project_id if context_type='Project') |
| is_primary | BOOLEAN | No | 0 | Whether this is the primary role for this context |
| start_date | DATE | Yes | NULL | When role assignment began |
| end_date | DATE | Yes | NULL | When role assignment ended |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Freeform notes about this assignment |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Context Types:**
- `NULL` - General role (e.g., "NuScale is a vendor in general")
- `'Project'` - Project-specific (e.g., "NuScale is the vendor for Project X")
- Future: Could add 'Agreement', 'Contract', etc.

**Relationships:**
- Belongs to: Companies (N:1)
- Belongs to: CompanyRoles (N:1)
- Context relationship (polymorphic via context_type/context_id)

**Business Rules:**
- Unique constraint on (company_id, role_id, context_type, context_id)
- If context_type is NULL, context_id must be NULL (general role)
- If context_type is set, context_id must be set (specific context)
- end_date must be after start_date if both are set
- Can mark individual assignments as confidential

**Indexes:**
```sql
CREATE INDEX idx_company_role_company ON company_role_assignments(company_id);
CREATE INDEX idx_company_role_role ON company_role_assignments(role_id);
CREATE INDEX idx_company_role_context ON company_role_assignments(context_type, context_id);
CREATE INDEX idx_company_role_primary ON company_role_assignments(is_primary);
CREATE INDEX idx_company_role_confidential ON company_role_assignments(is_confidential);
```

**Usage Examples:**
```sql
-- General role: NuScale is a technology vendor
INSERT INTO company_role_assignments (company_id, role_id, context_type, context_id)
SELECT 42, 1, NULL, NULL;

-- Project-specific: NuScale is the vendor for Project 15
INSERT INTO company_role_assignments (company_id, role_id, context_type, context_id, is_primary)
SELECT 42, 1, 'Project', 15, 1;

-- Multi-role: Holtec is both vendor AND operator
INSERT INTO company_role_assignments (company_id, role_id) VALUES (50, 1); -- vendor
INSERT INTO company_role_assignments (company_id, role_id) VALUES (50, 4); -- operator
```

---

## Client_Profiles

**Purpose:** Extended CRM data for companies that are MPR clients

This is an extension table (1:1 with companies where is_mpr_client = true). Contains internal assessment and relationship tracking.

**SQL Definition:**
```sql
CREATE TABLE client_profiles (
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
```

**Field Reference:**

| Field | Type | Null | Access | Description |
|-------|------|------|--------|-------------|
| company_id | INTEGER | No | All | PK/FK to companies |
| **Internal Assessment (NED Team Only)** | | | | |
| relationship_strength | TEXT | Yes | NED | Strong, Good, Needs Attention, At Risk, New |
| relationship_notes | TEXT | Yes | NED | Internal assessment notes |
| client_priority | TEXT | Yes | NED | High, Medium, Low, Strategic, Opportunistic |
| client_status | TEXT | Yes | NED | Active, Warm, Cold, Prospective |
| **Contact Tracking (All Users)** | | | | |
| last_contact_date | DATE | Yes | All | Date of last contact |
| last_contact_type | TEXT | Yes | All | In-person, Phone, Email, Video |
| last_contact_by | INTEGER | Yes | All | FK to Personnel (internal) |
| next_planned_contact_date | DATE | Yes | All | Date of next planned contact |
| next_planned_contact_type | TEXT | Yes | All | Type of next contact |
| next_planned_contact_assigned_to | INTEGER | Yes | All | FK to Personnel (internal) |
| **Audit Fields** | | | | |
| created_by | INTEGER | Yes | All | FK to Users |
| created_date | TIMESTAMP | No | All | Creation timestamp |
| modified_by | INTEGER | Yes | All | FK to Users |
| modified_date | TIMESTAMP | Yes | All | Last modified timestamp |

**Relationships:**
- Belongs to: Companies (1:1)
- References: Personnel (for contacts)

**Business Rules:**
- Only exists for companies where is_mpr_client = true
- Internal assessment fields (relationship_strength, etc.) visible to NED Team only
- Contact tracking fields visible to all users
- See `05_PERMISSION_SYSTEM.md` for access control logic

**Indexes:**
```sql
CREATE INDEX idx_client_profiles_priority ON client_profiles(client_priority);
CREATE INDEX idx_client_profiles_status ON client_profiles(client_status);
CREATE INDEX idx_client_profiles_last_contact ON client_profiles(last_contact_date);
```

---

## Person_Company_Affiliations

**Purpose:** Link personnel to companies they work for

Replaces the old polymorphic organization_type/organization_id pattern in personnel table. Provides:
- Many-to-many personnel↔company relationships
- Title/department tracking
- Primary affiliation designation
- Temporal tracking (start/end dates)

**SQL Definition:**
```sql
CREATE TABLE person_company_affiliations (
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
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| affiliation_id | INTEGER | No | Auto | Primary key |
| person_id | INTEGER | No | - | FK to personnel |
| company_id | INTEGER | No | - | FK to companies |
| title | TEXT | Yes | NULL | Job title at this company |
| department | TEXT | Yes | NULL | Department within company |
| is_primary | BOOLEAN | No | 0 | Whether this is person's primary affiliation |
| start_date | DATE | Yes | NULL | When affiliation began |
| end_date | DATE | Yes | NULL | When affiliation ended (NULL = current) |
| notes | TEXT | Yes | NULL | Freeform notes |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Relationships:**
- Belongs to: Personnel (N:1)
- Belongs to: Companies (N:1)

**Business Rules:**
- A person can have multiple affiliations (consultant at multiple companies)
- Only one affiliation per person should have is_primary = true
- end_date = NULL means currently affiliated
- Unique constraint prevents duplicate (person, company, title, start_date)

**Indexes:**
```sql
CREATE INDEX idx_person_company_person ON person_company_affiliations(person_id);
CREATE INDEX idx_person_company_company ON person_company_affiliations(company_id);
CREATE INDEX idx_person_company_primary ON person_company_affiliations(is_primary);
```

**Migration Note:**
- Migrated from old PersonnelEntityRelationship via `scripts/backfill_personnel_affiliations.py`

---

# OTHER CORE TABLES (Mostly Unchanged)

## Products

**Purpose:** Specific reactor designs/models

**Note:** Still references technology_vendors in current implementation. Should eventually reference companies with role='vendor'.

**SQL Definition:**
```sql
CREATE TABLE products (
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
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES technology_vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);
```

**TODO:** Update vendor_id FK to reference companies table instead.

---

## Projects

**Purpose:** Nuclear project sites and deployments

**SQL Definition:**
```sql
CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    location TEXT,
    project_status TEXT,
    licensing_approach TEXT,
    configuration TEXT,
    project_schedule TEXT,
    latitude REAL,
    longitude REAL,
    capex REAL,
    opex REAL,
    fuel_cost REAL,
    lcoe REAL,
    cod DATE,
    mpr_project_id TEXT,
    notes TEXT,
    firm_involvement TEXT,
    primary_firm_contact INTEGER,
    last_project_interaction_date DATE,
    last_project_interaction_by INTEGER,
    project_health TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (primary_firm_contact) REFERENCES personnel(personnel_id),
    FOREIGN KEY (last_project_interaction_by) REFERENCES personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);
```

**Relationships:**
- Company roles via company_role_assignments (context_type='Project')
- Legacy: Still has project_vendor_relationships, project_owner_relationships, etc.

**Migration Status:**
- ✅ New code creates company_role_assignments for project relationships
- ⚠️ Legacy relationship tables still exist for backward compatibility

---

## Personnel

**Purpose:** People - both internal team members and external contacts

**SQL Definition:**
```sql
CREATE TABLE personnel (
    personnel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role TEXT,
    personnel_type TEXT,
    organization_id INTEGER,
    organization_type TEXT,
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (modified_by) REFERENCES users(user_id)
);
```

**Migration Status:**
- ⚠️ Still has organization_id/organization_type (legacy polymorphic pattern)
- ✅ New affiliations use person_company_affiliations table
- 📋 TODO: Deprecate organization_id/organization_type fields after full migration

---

## Users

**Purpose:** Application users with authentication and permissions

**SQL Definition:**
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    has_confidential_access BOOLEAN DEFAULT 0,
    is_ned_team BOOLEAN DEFAULT 0,
    is_admin BOOLEAN DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    last_db_path TEXT,
    last_db_display_name TEXT
);
```

**New in Schema v6:**
- last_db_path - User's last selected database (per-session DB selection feature)
- last_db_display_name - Friendly name of last selected database

---

# SUPPORT TABLES (Unchanged)

## Contact_Log, Roundtable_History, Confidential_Field_Flags, Audit_Log, Database_Snapshots, System_Settings, Schema_Version

**Status:** These tables remain unchanged from legacy schema.

See `02_DATABASE_SCHEMA_LEGACY.md` for detailed specifications.

**TODO:** Update Contact_Log to reference companies table instead of entity_type/entity_id polymorphism.

---

# DEPRECATED LEGACY TABLES

The following tables still exist in the database but should NOT be used in new code:

## ❌ technology_vendors
**Replacement:** `companies` with `company_role_assignments.role_code = 'vendor'`

## ❌ owners_developers
**Replacement:** `companies` with `company_role_assignments.role_code = 'developer'`

## ❌ operators
**Replacement:** `companies` with `company_role_assignments.role_code = 'operator'`

## ❌ constructors
**Replacement:** `companies` with `company_role_assignments.role_code = 'constructor'`

## ❌ offtakers
**Replacement:** `companies` with `company_role_assignments.role_code = 'offtaker'`

## ❌ Legacy Relationship Tables
- ❌ vendor_supplier_relationships
- ❌ owner_vendor_relationships
- ❌ project_vendor_relationships
- ❌ project_constructor_relationships
- ❌ project_operator_relationships
- ❌ project_owner_relationships
- ❌ project_offtaker_relationships
- ❌ vendor_preferred_constructors

**Replacement:** All project relationships now use `company_role_assignments` with `context_type='Project'`

**Deprecation Timeline:**
1. **Current:** Both schemas exist, some code writes to both
2. **Phase 2 (In Progress):** Complete code migration to use only new schema
3. **Phase 3 (Future):** Remove legacy tables entirely (after 3-6 months of stability)

---

# QUERY EXAMPLES

## Get all vendors
```sql
SELECT c.* FROM companies c
JOIN company_role_assignments cra ON c.company_id = cra.company_id
JOIN company_roles cr ON cra.role_id = cr.role_id
WHERE cr.role_code = 'vendor'
AND cra.context_type IS NULL; -- General role, not project-specific
```

## Get all companies involved in a project
```sql
SELECT c.*, cr.role_label, cra.is_primary
FROM companies c
JOIN company_role_assignments cra ON c.company_id = cra.company_id
JOIN company_roles cr ON cra.role_id = cr.role_id
WHERE cra.context_type = 'Project'
AND cra.context_id = ?; -- project_id
```

## Get a company's personnel
```sql
SELECT p.* FROM personnel p
JOIN person_company_affiliations pca ON p.personnel_id = pca.person_id
WHERE pca.company_id = ?
AND pca.end_date IS NULL; -- Current employees only
```

## Get multi-role companies
```sql
SELECT c.company_name, GROUP_CONCAT(cr.role_label, ', ') as roles
FROM companies c
JOIN company_role_assignments cra ON c.company_id = cra.company_id
JOIN company_roles cr ON cra.role_id = cr.role_id
WHERE cra.context_type IS NULL
GROUP BY c.company_id
HAVING COUNT(DISTINCT cr.role_id) > 1;
```

---

# MIGRATION HELPERS

## Service Functions

**File:** `app/services/company_query.py`
- `get_companies_by_role(role_code)` - Get all companies with a specific role
- `get_company_roles(company_id)` - Get all roles for a company
- `get_companies_for_project(project_id)` - Get all companies on a project

**File:** `app/services/company_sync.py` (TRANSITIONAL)
- Legacy sync functions that write to both old and new schemas
- Used during migration period
- Will be removed after full migration

## Scripts

**File:** `scripts/backfill_all.py`
- Master script to migrate all legacy data to new schema

**File:** `scripts/validate_company_migration.py`
- Validate migration completeness and data integrity

---

# SUMMARY STATISTICS

**Total Tables:** 16 (new schema) + 13 (legacy, deprecated)

**New Unified Schema Tables:** 5
- companies
- company_roles
- company_role_assignments
- client_profiles
- person_company_affiliations

**Core Business Tables (unchanged):** 4
- products
- projects
- personnel
- users

**Support Tables:** 7
- contact_log, roundtable_history, confidential_field_flags, audit_log, database_snapshots, system_settings, schema_version

**Legacy Tables (deprecated):** 13
- 5 entity tables (vendors, owners, operators, constructors, offtakers)
- 8 relationship junction tables

---

# NEXT STEPS

1. ✅ Complete schema documentation (this document)
2. 📋 Create migration completion plan
3. 📋 Update all routes to use unified schema
4. 📋 Remove legacy route files
5. 📋 Update `03_DATABASE_RELATIONSHIPS.md`
6. 📋 Remove legacy tables (after validation period)

---

**Document End**
