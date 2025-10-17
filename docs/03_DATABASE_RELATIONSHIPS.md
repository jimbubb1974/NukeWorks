# 03_DATABASE_RELATIONSHIPS.md - Junction Tables & Relationships

**Document Version:** 2.0
**Last Updated:** October 7, 2025

**Related Documents:**
- `02_DATABASE_SCHEMA.md` - Core entity tables
- `04_DATA_DICTIONARY.md` - Field definitions
- `05_PERMISSION_SYSTEM.md` - Confidentiality on relationships
- `docs/COMPANY_UNIFICATION.md` - Migration status and timeline
- `docs/ENCRYPTION_IMPLEMENTATION_STATUS.md` - Encryption implementation phases

---

## Overview

This document defines all many-to-many (N:N) relationships using junction tables. The system uses a **unified company schema** where a single `companies` table with role-based assignments replaces legacy entity-specific tables.

⚠️ **IMPORTANT: Migration Status (October 2025)**
- **Current State:** DUAL SCHEMA ACTIVE (intentional transition period)
- **Legacy Tables:** Still exist in database for backward compatibility
- **New Tables:** All active and used by current code
- **Timeline:** See `docs/COMPANY_UNIFICATION.md` for detailed migration plan and production rollout date

**Key Architectural Change (October 2025):**
- **Before:** Separate tables (Technology_Vendors, Owners_Developers, Operators, Constructors, Offtakers)
- **After:** Single `companies` table with `company_role_assignments` for flexible role management

Each junction table includes:
- Foreign keys to both entities
- Confidentiality flag (`is_confidential`)
- Optional metadata (notes, relationship type)
- Standard audit fields

**Confidentiality Note:** Relationships can be marked confidential independently of the entities they connect. See `05_PERMISSION_SYSTEM.md` for access control logic.

---

## Table of Contents

1. [Unified Company System](#unified-company-system)
2. [Company_Role_Assignments](#company_role_assignments) (Primary Relationship Table)
3. [Person_Company_Affiliations](#person_company_affiliations)
4. [Entity_Team_Members](#entity_team_members)
5. [Legacy Tables (Deprecated)](#legacy-tables-deprecated)
6. [Relationship Summary](#relationship_summary)
7. [Migration Notes](#migration-notes)

---

## Unified Company System

### Core Concept

The unified company system consolidates all organization types (vendors, owners, operators, constructors, offtakers) into a single `companies` table with flexible role-based relationships.

**Benefits:**
- Single source of truth for all companies
- Companies can have multiple roles (e.g., both vendor and operator)
- Simplified queries and reduced code duplication
- Easier to add new company types without schema changes

### Key Tables

1. **companies** - All organizations (replaces 5 legacy tables)
2. **company_roles** - Available roles (vendor, developer, operator, constructor, offtaker)
3. **company_role_assignments** - Polymorphic relationship table linking companies to any entity with a specific role

---

## Company_Role_Assignments

**Purpose:** Unified relationship table connecting companies to projects, personnel, and other entities in specific roles

**Connects:** Companies ↔ Any Entity (Projects, Personnel, etc.) with role context

**SQL Definition:**
```sql
CREATE TABLE company_role_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    context_type TEXT NOT NULL,
    context_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (role_id) REFERENCES company_roles(role_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| assignment_id | INTEGER | No | Auto | Primary key |
| company_id | INTEGER | No | - | FK to companies |
| role_id | INTEGER | No | - | FK to company_roles |
| context_type | TEXT | No | - | Entity type: 'Project', 'Personnel', etc. |
| context_id | INTEGER | No | - | ID of the specific entity |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Freeform notes about the relationship |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Polymorphic Relationship Pattern:**
- `context_type` specifies what kind of entity (e.g., 'Project', 'Personnel')
- `context_id` specifies which specific entity
- This allows one table to manage all company relationships

**Business Rules:**
- context_type must be one of: 'Project', 'Personnel', 'Company' (for supplier relationships)
- context_id must be valid ID for the specified context_type
- role_id determines the relationship type (vendor, developer, operator, etc.)
- Same company can have multiple roles on same project
- Combination of (company_id, role_id, context_type, context_id) should be unique

**Indexes:**
```sql
CREATE INDEX idx_company_role_assignment_company ON company_role_assignments(company_id);
CREATE INDEX idx_company_role_assignment_role ON company_role_assignments(role_id);
CREATE INDEX idx_company_role_assignment_context ON company_role_assignments(context_type, context_id);
CREATE INDEX idx_company_role_assignment_conf ON company_role_assignments(is_confidential);
```

**Examples:**
```sql
-- NuScale Power (company_id=1) is Technology Vendor (role_id=1) for Project 5
INSERT INTO company_role_assignments
(company_id, role_id, context_type, context_id, is_confidential, created_by)
VALUES (1, 1, 'Project', 5, 0, 1);

-- AtkinsRéalis (company_id=10) is Constructor (role_id=4) for Project 5
INSERT INTO company_role_assignments
(company_id, role_id, context_type, context_id, is_confidential, created_by)
VALUES (10, 4, 'Project', 5, 0, 1);

-- Ontario Power Generation (company_id=15) is Owner/Developer (role_id=2) for Project 5
INSERT INTO company_role_assignments
(company_id, role_id, context_type, context_id, is_confidential, created_by)
VALUES (15, 2, 'Project', 5, 0, 1);
```

---

## Person_Company_Affiliations

**Purpose:** Track personnel affiliations with companies (replaces Personnel_Entity_Relationships for company entities)

**Connects:** Personnel ↔ Companies

**SQL Definition:**
```sql
CREATE TABLE person_company_affiliations (
    affiliation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    personnel_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    role_at_company TEXT,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (personnel_id) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| affiliation_id | INTEGER | No | Auto | Primary key |
| personnel_id | INTEGER | No | - | FK to Personnel |
| company_id | INTEGER | No | - | FK to companies |
| role_at_company | TEXT | Yes | NULL | Person's role (e.g., "CEO", "VP Engineering") |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Additional details about affiliation |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Business Rules:**
- Same person can be affiliated with multiple companies
- role_at_company describes their position at the company
- Replaces legacy Personnel_Entity_Relationships for all company entity types
- Combination of (personnel_id, company_id, role_at_company) should be unique

**Indexes:**
```sql
CREATE INDEX idx_person_company_personnel ON person_company_affiliations(personnel_id);
CREATE INDEX idx_person_company_company ON person_company_affiliations(company_id);
CREATE INDEX idx_person_company_conf ON person_company_affiliations(is_confidential);
```

**Examples:**
```sql
-- John Doe is CEO of NuScale Power (company_id=1)
INSERT INTO person_company_affiliations
(personnel_id, company_id, role_at_company, is_confidential, created_by)
VALUES (10, 1, 'CEO', 0, 1);

-- Jane Smith is VP of Engineering at Ontario Power Generation (company_id=15)
INSERT INTO person_company_affiliations
(personnel_id, company_id, role_at_company, is_confidential, created_by)
VALUES (12, 15, 'VP of Engineering', 0, 1);
```

---

## Personnel_Entity_Relationships (Legacy - Still Active)

**Purpose:** Track which people are associated with which organizations/projects

**Connects:** Personnel ↔ Any Entity (polymorphic relationship)

**SQL Definition:**
```sql
CREATE TABLE Personnel_Entity_Relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    personnel_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    role_at_entity TEXT,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (personnel_id) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| relationship_id | INTEGER | No | Auto | Primary key |
| personnel_id | INTEGER | No | - | FK to Personnel |
| entity_type | TEXT | No | - | Vendor, Owner, Operator, Constructor, Project |
| entity_id | INTEGER | No | - | ID of the specific entity |
| role_at_entity | TEXT | Yes | NULL | Person's role (e.g., "CEO", "Project Manager") |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Additional details |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Business Rules:**
- entity_type must be one of: Vendor, Owner, Operator, Constructor, Project
- entity_id must be valid ID for the specified entity_type
- Same person can have relationships with multiple entities
- Combination of (personnel_id, entity_type, entity_id) should be unique

**Indexes:**
```sql
CREATE INDEX idx_personnel_entity_personnel ON Personnel_Entity_Relationships(personnel_id);
CREATE INDEX idx_personnel_entity_type ON Personnel_Entity_Relationships(entity_type, entity_id);
CREATE INDEX idx_personnel_entity_conf ON Personnel_Entity_Relationships(is_confidential);
```

**Example:**
```sql
-- John Doe is CEO of Vendor 5
INSERT INTO Personnel_Entity_Relationships 
(personnel_id, entity_type, entity_id, role_at_entity, is_confidential, created_by)
VALUES (10, 'Vendor', 5, 'CEO', 0, 1);

-- Jane Smith is Project Manager on Project 3
INSERT INTO Personnel_Entity_Relationships 
(personnel_id, entity_type, entity_id, role_at_entity, is_confidential, created_by)
VALUES (12, 'Project', 3, 'Project Manager', 0, 1);
```

---

## Entity_Team_Members

**Purpose:** Track internal team assignments to clients/projects (for CRM)

**Connects:** Personnel (internal only) ↔ Any Entity

**SQL Definition:**
```sql
CREATE TABLE Entity_Team_Members (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    personnel_id INTEGER NOT NULL,
    assignment_type TEXT,
    assigned_date DATE,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (personnel_id) REFERENCES Personnel(personnel_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| assignment_id | INTEGER | No | Auto | Primary key |
| entity_type | TEXT | No | - | Owner, Vendor, Project, etc. |
| entity_id | INTEGER | No | - | ID of the specific entity |
| personnel_id | INTEGER | No | - | FK to Personnel (must be Internal) |
| assignment_type | TEXT | Yes | NULL | Primary_POC, Secondary_POC, Team_Member |
| assigned_date | DATE | Yes | NULL | When assigned |
| is_active | BOOLEAN | No | 1 | Whether assignment is current |

**Business Rules:**
- personnel_id must reference Internal personnel only
- Used primarily for Owner/Developer entities (CRM tracking)
- assignment_type values:
  - Primary_POC: Primary point of contact
  - Secondary_POC: Secondary/backup contact
  - Team_Member: Supporting team member
- Same person can be assigned to multiple entities
- Set is_active = 0 to deactivate assignment (don't delete)

**Indexes:**
```sql
CREATE INDEX idx_team_members_entity ON Entity_Team_Members(entity_type, entity_id);
CREATE INDEX idx_team_members_personnel ON Entity_Team_Members(personnel_id);
CREATE INDEX idx_team_members_active ON Entity_Team_Members(is_active);
```

**Example:**
```sql
-- John Smith (personnel_id 5) is Primary POC for Owner 10
INSERT INTO Entity_Team_Members 
(entity_type, entity_id, personnel_id, assignment_type, assigned_date)
VALUES ('Owner', 10, 5, 'Primary_POC', '2025-01-15');

-- Sarah Lee (personnel_id 8) is Team Member for Owner 10
INSERT INTO Entity_Team_Members 
(entity_type, entity_id, personnel_id, assignment_type, assigned_date)
VALUES ('Owner', 10, 8, 'Team_Member', '2025-02-01');
```

---

## Relationship Summary

### Unified Schema Relationship Map

```
Companies (Unified)
├── Products (1:N) - for technology vendors
├── Company_Role_Assignments (N:N polymorphic)
│   ├── Projects (via context_type='Project')
│   ├── Personnel (via context_type='Personnel')
│   └── Other Companies (via context_type='Company' for supplier relationships)
├── Person_Company_Affiliations (N:N with Personnel)
├── Client_Profiles (1:1 extension for CRM)
├── Contact_Log (1:N)
└── Entity_Team_Members (1:N with Personnel)

Projects
├── Company_Role_Assignments (N:N with Companies)
│   ├── Technology Vendor role
│   ├── Owner/Developer role
│   ├── Operator role
│   ├── Constructor role
│   └── Offtaker role
├── Entity_Team_Members (1:N with Personnel)
└── Personnel_Entity_Relationships (N:N with Personnel) - for project personnel

Personnel
├── Person_Company_Affiliations (N:N with Companies)
├── Company_Role_Assignments (N:N polymorphic)
├── Personnel_Entity_Relationships (N:N polymorphic - for projects)
└── Entity_Team_Members (N:N for internal team assignments)
```

### Active Relationship Tables

| Relationship Type | Junction Table | Confidentiality | Status |
|-------------------|----------------|-----------------|--------|
| Company → Project (any role) | company_role_assignments | Optional | Active |
| Company → Company (supplier) | company_role_assignments | Optional | Active |
| Personnel → Company | person_company_affiliations | Optional | Active |
| Personnel → Project | Personnel_Entity_Relationships | Optional | Active |
| Internal Personnel → Entity | Entity_Team_Members | No flag | Active |

**Total Active Junction Tables:** 3 (down from 9!)

**Consolidated Functionality:**
- `company_role_assignments` replaces 5+ legacy relationship tables
- Polymorphic pattern allows one table to handle all company relationships
- Simpler schema, easier to maintain, more flexible

---

## Query Examples (Unified Schema)

### Get All Company Relationships for a Project

```sql
-- Get all companies for Project 5 (any role)
SELECT
    c.company_name,
    r.role_label,
    cra.is_confidential,
    cra.notes
FROM company_role_assignments cra
JOIN companies c ON cra.company_id = c.company_id
JOIN company_roles r ON cra.role_id = r.role_id
WHERE cra.context_type = 'Project'
AND cra.context_id = 5
AND (cra.is_confidential = 0 OR ? = 1);  -- ? = user has confidential access

-- Get just the technology vendor for Project 5
SELECT c.company_name, cra.notes
FROM company_role_assignments cra
JOIN companies c ON cra.company_id = c.company_id
JOIN company_roles r ON cra.role_id = r.role_id
WHERE cra.context_type = 'Project'
AND cra.context_id = 5
AND r.role_code = 'vendor'
AND (cra.is_confidential = 0 OR ? = 1);
```

### Get All Projects for a Company

```sql
-- Get all projects for Company 1 (any role)
SELECT
    p.project_name,
    r.role_label,
    cra.is_confidential,
    cra.notes
FROM company_role_assignments cra
JOIN projects p ON cra.context_id = p.project_id
JOIN company_roles r ON cra.role_id = r.role_id
WHERE cra.company_id = 1
AND cra.context_type = 'Project'
AND (cra.is_confidential = 0 OR ? = 1)
ORDER BY p.project_name;

-- Get all companies related to Company 1 (supplier relationships)
SELECT
    c.company_name,
    r.role_label,
    cra.notes
FROM company_role_assignments cra
JOIN companies c ON cra.context_id = c.company_id
JOIN company_roles r ON cra.role_id = r.role_id
WHERE cra.company_id = 1
AND cra.context_type = 'Company'
AND (cra.is_confidential = 0 OR ? = 1);
```

### Get Network Diagram Data

```sql
-- Get all visible project-company relationships for network diagram
SELECT
    p.project_name,
    c.company_name,
    r.role_label,
    cra.is_confidential
FROM company_role_assignments cra
JOIN projects p ON cra.context_id = p.project_id
JOIN companies c ON cra.company_id = c.company_id
JOIN company_roles r ON cra.role_id = r.role_id
WHERE cra.context_type = 'Project'
AND (cra.is_confidential = 0 OR ? = 1)  -- User has confidential access
ORDER BY p.project_name, c.company_name;
```

### Count Relationships by Company

```sql
-- Count all relationships for each company
SELECT
    c.company_id,
    c.company_name,
    (SELECT COUNT(*)
     FROM company_role_assignments
     WHERE company_id = c.company_id AND context_type = 'Project') as project_count,
    (SELECT COUNT(*)
     FROM company_role_assignments
     WHERE company_id = c.company_id AND context_type = 'Company') as supplier_count,
    (SELECT COUNT(*)
     FROM person_company_affiliations
     WHERE company_id = c.company_id) as personnel_count
FROM companies c
ORDER BY c.company_name;
```

### Get Personnel for a Company

```sql
-- Get all personnel affiliated with Company 1
SELECT
    p.full_name,
    pca.role_at_company,
    pca.is_confidential,
    pca.notes
FROM person_company_affiliations pca
JOIN personnel p ON pca.personnel_id = p.personnel_id
WHERE pca.company_id = 1
AND (pca.is_confidential = 0 OR ? = 1)
ORDER BY p.last_name, p.first_name;
```

---

## Confidentiality in Relationships

### Access Control Logic

For each relationship query, apply this filter:
```sql
WHERE (relationship.is_confidential = 0 OR user.has_confidential_access = 1 OR user.is_admin = 1)
```

### Display Behavior

**In Entity Detail Views:**
- Public relationships: Display normally
- Confidential relationships (no access): Hide completely, show count if any
  - Example: "2 additional relationships - confidential"

**In Network Diagram:**
- Public relationships: Show as edges
- Confidential relationships (no access): Completely hidden
  - Do NOT show as "locked" edges
  - User doesn't know relationship exists

**In Reports:**
- Public relationships: Include in report
- Confidential relationships (no access): Omit entirely
  - Note at bottom: "Some relationships may be omitted based on permissions"

---

## Data Integrity Rules

### Cascade Deletes

When deleting entities, handle relationships appropriately:

**Recommended approach: Prevent deletion if relationships exist**
```sql
-- Before deleting Vendor, check for relationships
SELECT COUNT(*) FROM Project_Vendor_Relationships WHERE vendor_id = ?;
SELECT COUNT(*) FROM Owner_Vendor_Relationships WHERE vendor_id = ?;
-- etc.

-- If count > 0, prevent deletion and show error
```

**Alternative: Cascade delete (use with caution)**
```sql
-- If entity deleted, automatically delete relationships
-- Add to foreign key constraints:
FOREIGN KEY (vendor_id) REFERENCES Technology_Vendors(vendor_id) ON DELETE CASCADE
```

### Duplicate Prevention

Each junction table should prevent duplicate relationships:
```sql
-- Add unique constraint on relevant columns
CREATE UNIQUE INDEX idx_project_vendor_unique 
ON Project_Vendor_Relationships(project_id, vendor_id);

CREATE UNIQUE INDEX idx_owner_vendor_unique 
ON Owner_Vendor_Relationships(owner_id, vendor_id, relationship_type);
```

---

## Migration Notes

### October 2025 Company Unification Migration

**Completed:** October 7, 2025
**Duration:** 4.6 hours (Phases 1-5)
**Status:** Successful - All tests passing

#### What Changed

**Phase 1: Schema Preparation**
- Created unified `companies` table
- Created `company_roles` lookup table
- Created `company_role_assignments` polymorphic relationship table
- Created `person_company_affiliations` table
- Data migrated from 5 legacy tables into unified schema

**Phase 2: Code Migration**
- Updated all application code to use unified schema
- Modified 6 route files (projects.py, admin.py, contact_log.py, personnel.py, network_diagram.py)
- Created unified helper functions in relationship_utils.py
- Network diagram refactored from 8 edge builders to 1
- Code reduction: -616 lines net

**Phase 3: Route Deprecation**
- Disabled 5 legacy blueprints (vendors, owners, operators, constructors, offtakers)
- All functionality now accessible via `/companies` with role filtering
- Legacy routes return 404

**Phase 4: Cleanup**
- Removed 5 dual-write sync functions from company_sync.py
- Code reduction: -313 lines
- Total cleanup: ~1,200 lines of legacy code removed

**Phase 5: Testing**
- 6 smoke tests completed successfully
- 47 companies accessible
- 85 role assignments working
- 31 project-company relationships functioning

#### Legacy Tables (Deprecated but Not Dropped)

These tables still exist in the database for reference but are no longer used by the application:

- `technology_vendors` → Use `companies` with role 'vendor'
- `owners_developers` → Use `companies` with role 'developer'
- `operators` → Use `companies` with role 'operator'
- `constructors` → Use `companies` with role 'constructor'
- `offtakers` → Use `companies` with role 'offtaker'
- `project_vendor_relationships` → Use `company_role_assignments` with context_type='Project', role='vendor'
- `project_owner_relationships` → Use `company_role_assignments` with context_type='Project', role='developer'
- `project_operator_relationships` → Use `company_role_assignments` with context_type='Project', role='operator'
- `project_constructor_relationships` → Use `company_role_assignments` with context_type='Project', role='constructor'
- `project_offtaker_relationships` → Use `company_role_assignments` with context_type='Project', role='offtaker'

**Note:** Legacy tables will be dropped in Phase 7 (3-6 months after migration) once stability is confirmed.

#### Backward Compatibility

**Preserved:**
- Legacy helper function names aliased to unified functions
- Entity type mapping for contact log and personnel routes
- All existing data accessible through new schema

**Broken:**
- Direct URLs to `/vendors`, `/owners`, etc. (return 404)
- Code imports from deleted route files
- Direct queries to legacy tables in custom scripts

#### Benefits Realized

1. **Simplified Schema**: 3 active junction tables instead of 9
2. **Code Reduction**: -1,200 lines of legacy code removed
3. **Flexibility**: Companies can now have multiple roles
4. **Maintainability**: Single source of truth for all companies
5. **Performance**: Simpler queries, better indexing

#### Future Considerations

**Adding New Company Roles:**
With the unified schema, adding new company types is trivial:
```sql
-- Add a new role (e.g., 'regulator')
INSERT INTO company_roles (role_code, role_label, role_description)
VALUES ('regulator', 'Regulatory Body', 'Government regulatory agencies');

-- Assign role to company for a project
INSERT INTO company_role_assignments
(company_id, role_id, context_type, context_id)
VALUES (25, 6, 'Project', 10);
```

No schema changes, no code changes, no new tables required!

---

## Next Steps

1. Review `04_DATA_DICTIONARY.md` for enum values and validation
2. Review `05_PERMISSION_SYSTEM.md` for access control implementation
3. Review `11_NETWORK_DIAGRAM.md` for relationship visualization
4. Implement relationship CRUD operations with permission checks
5. Consider Phase 7 cleanup after 3-6 months of stability

---

**Document End**
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Business Rules:**
- vendor_id and supplier_id can reference the same vendor (self-referential allowed)
- Combination of (vendor_id, supplier_id) should be unique
- If is_confidential = 1, hidden from users without confidential access
- Shown in network diagram only if user has access

**Indexes:**
```sql
CREATE INDEX idx_vendor_supplier_vendor ON Vendor_Supplier_Relationships(vendor_id);
CREATE INDEX idx_vendor_supplier_supplier ON Vendor_Supplier_Relationships(supplier_id);
CREATE INDEX idx_vendor_supplier_conf ON Vendor_Supplier_Relationships(is_confidential);
```

**Example:**
```sql
-- TechVendor A uses Supplier B for major components (confidential)
INSERT INTO Vendor_Supplier_Relationships 
(vendor_id, supplier_id, component_type, is_confidential, created_by)
VALUES (1, 5, 'major_component', 1, 1);
```

---

## Owner_Vendor_Relationships

**Purpose:** Track agreements between owners/developers and technology vendors

**Connects:** Owners_Developers ↔ Technology_Vendors

**SQL Definition:**
```sql
CREATE TABLE Owner_Vendor_Relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    relationship_type TEXT,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES Owners_Developers(owner_id),
    FOREIGN KEY (vendor_id) REFERENCES Technology_Vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| relationship_id | INTEGER | No | Auto | Primary key |
| owner_id | INTEGER | No | - | FK to Owners_Developers |
| vendor_id | INTEGER | No | - | FK to Technology_Vendors |
| relationship_type | TEXT | Yes | NULL | MOU, Development_Agreement, Delivery_Contract |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Agreement details, dates, terms |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Business Rules:**
- relationship_type values (see `04_DATA_DICTIONARY.md`):
  - MOU: Memorandum of Understanding (no money)
  - Development_Agreement: Development agreement (with money)
  - Delivery_Contract: Delivery contract (procurement orders/big money)
- Multiple relationships between same owner/vendor allowed (with different types)

**Indexes:**
```sql
CREATE INDEX idx_owner_vendor_owner ON Owner_Vendor_Relationships(owner_id);
CREATE INDEX idx_owner_vendor_vendor ON Owner_Vendor_Relationships(vendor_id);
CREATE INDEX idx_owner_vendor_type ON Owner_Vendor_Relationships(relationship_type);
CREATE INDEX idx_owner_vendor_conf ON Owner_Vendor_Relationships(is_confidential);
```

**Example:**
```sql
-- Owner A has MOU with Vendor B (public)
INSERT INTO Owner_Vendor_Relationships 
(owner_id, vendor_id, relationship_type, is_confidential, notes, created_by)
VALUES (1, 2, 'MOU', 0, 'Signed 2024-03-15, 2-year term', 1);
```

---

## Project_Vendor_Relationships

**Purpose:** Track which technology vendors are involved in projects

**Connects:** Projects ↔ Technology_Vendors

**SQL Definition:**
```sql
CREATE TABLE Project_Vendor_Relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    FOREIGN KEY (vendor_id) REFERENCES Technology_Vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| relationship_id | INTEGER | No | Auto | Primary key |
| project_id | INTEGER | No | - | FK to Projects |
| vendor_id | INTEGER | No | - | FK to Technology_Vendors |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Details about vendor's role |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |