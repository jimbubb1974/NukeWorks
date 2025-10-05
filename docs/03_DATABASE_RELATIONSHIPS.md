# 03_DATABASE_RELATIONSHIPS.md - Junction Tables & Relationships

**Document Version:** 1.0  
**Last Updated:** December 4, 2025

**Related Documents:**
- `02_DATABASE_SCHEMA.md` - Core entity tables
- `04_DATA_DICTIONARY.md` - Field definitions
- `05_PERMISSION_SYSTEM.md` - Confidentiality on relationships

---

## Overview

This document defines all many-to-many (N:N) relationships using junction tables. Each junction table includes:
- Foreign keys to both entities
- Confidentiality flag (`is_confidential`)
- Optional metadata (notes, relationship type)
- Standard audit fields

**Confidentiality Note:** Relationships can be marked confidential independently of the entities they connect. See `05_PERMISSION_SYSTEM.md` for access control logic.

---

## Table of Contents

1. [Vendor_Supplier_Relationships](#vendor_supplier_relationships)
2. [Owner_Vendor_Relationships](#owner_vendor_relationships)
3. [Project_Vendor_Relationships](#project_vendor_relationships)
4. [Project_Constructor_Relationships](#project_constructor_relationships)
5. [Project_Operator_Relationships](#project_operator_relationships)
6. [Project_Owner_Relationships](#project_owner_relationships)
7. [Vendor_Preferred_Constructor](#vendor_preferred_constructor)
8. [Personnel_Entity_Relationships](#personnel_entity_relationships)
9. [Entity_Team_Members](#entity_team_members)
10. [Relationship Summary](#relationship_summary)

---

## Vendor_Supplier_Relationships

**Purpose:** Track which vendors supply components to other vendors

**Connects:** Technology_Vendors (vendor) ↔ Technology_Vendors (supplier)

**SQL Definition:**
```sql
CREATE TABLE Vendor_Supplier_Relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    component_type TEXT,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES Technology_Vendors(vendor_id),
    FOREIGN KEY (supplier_id) REFERENCES Technology_Vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| relationship_id | INTEGER | No | Auto | Primary key |
| vendor_id | INTEGER | No | - | FK to Technology_Vendors (the vendor) |
| supplier_id | INTEGER | No | - | FK to Technology_Vendors (the supplier) |
| component_type | TEXT | Yes | NULL | major_component, minor_component, etc. |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Freeform notes about the relationship |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Business Rules:**
- Typically one vendor per project (technology provider)
- Multiple vendors possible if project uses hybrid technology
- Combination of (project_id, vendor_id) should be unique

**Indexes:**
```sql
CREATE INDEX idx_project_vendor_project ON Project_Vendor_Relationships(project_id);
CREATE INDEX idx_project_vendor_vendor ON Project_Vendor_Relationships(vendor_id);
CREATE INDEX idx_project_vendor_conf ON Project_Vendor_Relationships(is_confidential);
```

**Example:**
```sql
-- Project Alpha uses TechVendor X's technology (public)
INSERT INTO Project_Vendor_Relationships 
(project_id, vendor_id, is_confidential, created_by)
VALUES (1, 3, 0, 1);
```

---

## Project_Constructor_Relationships

**Purpose:** Track which construction companies are building projects

**Connects:** Projects ↔ Constructors

**SQL Definition:**
```sql
CREATE TABLE Project_Constructor_Relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    constructor_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    FOREIGN KEY (constructor_id) REFERENCES Constructors(constructor_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| relationship_id | INTEGER | No | Auto | Primary key |
| project_id | INTEGER | No | - | FK to Projects |
| constructor_id | INTEGER | No | - | FK to Constructors |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Construction details, contract type |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Business Rules:**
- One or more constructors per project
- Can distinguish primary vs. secondary constructor in notes
- Combination of (project_id, constructor_id) should be unique

**Indexes:**
```sql
CREATE INDEX idx_project_constructor_project ON Project_Constructor_Relationships(project_id);
CREATE INDEX idx_project_constructor_constructor ON Project_Constructor_Relationships(constructor_id);
CREATE INDEX idx_project_constructor_conf ON Project_Constructor_Relationships(is_confidential);
```

**Example:**
```sql
-- Project Alpha uses Constructor D (confidential - in negotiations)
INSERT INTO Project_Constructor_Relationships 
(project_id, constructor_id, is_confidential, notes, created_by)
VALUES (1, 4, 1, 'In contract negotiations', 1);
```

---

## Project_Operator_Relationships

**Purpose:** Track which companies will operate projects

**Connects:** Projects ↔ Operators

**SQL Definition:**
```sql
CREATE TABLE Project_Operator_Relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    operator_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    FOREIGN KEY (operator_id) REFERENCES Operators(operator_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| relationship_id | INTEGER | No | Auto | Primary key |
| project_id | INTEGER | No | - | FK to Projects |
| operator_id | INTEGER | No | - | FK to Operators |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Operating agreement details |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Business Rules:**
- Typically one operator per project
- Operator may be same as owner/developer
- Combination of (project_id, operator_id) should be unique

**Indexes:**
```sql
CREATE INDEX idx_project_operator_project ON Project_Operator_Relationships(project_id);
CREATE INDEX idx_project_operator_operator ON Project_Operator_Relationships(operator_id);
CREATE INDEX idx_project_operator_conf ON Project_Operator_Relationships(is_confidential);
```

---

## Project_Owner_Relationships

**Purpose:** Track which owners/developers own projects

**Connects:** Projects ↔ Owners_Developers

**SQL Definition:**
```sql
CREATE TABLE Project_Owner_Relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    FOREIGN KEY (owner_id) REFERENCES Owners_Developers(owner_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| relationship_id | INTEGER | No | Auto | Primary key |
| project_id | INTEGER | No | - | FK to Projects |
| owner_id | INTEGER | No | - | FK to Owners_Developers |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| notes | TEXT | Yes | NULL | Ownership details, partnership structure |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Business Rules:**
- One or more owners per project (consortiums, partnerships)
- Typically one primary owner
- Combination of (project_id, owner_id) should be unique

**Indexes:**
```sql
CREATE INDEX idx_project_owner_project ON Project_Owner_Relationships(project_id);
CREATE INDEX idx_project_owner_owner ON Project_Owner_Relationships(owner_id);
CREATE INDEX idx_project_owner_conf ON Project_Owner_Relationships(is_confidential);
```

---

## Vendor_Preferred_Constructor

**Purpose:** Track which constructors are preferred by vendors

**Connects:** Technology_Vendors ↔ Constructors

**SQL Definition:**
```sql
CREATE TABLE Vendor_Preferred_Constructor (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    constructor_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0,
    preference_reason TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES Technology_Vendors(vendor_id),
    FOREIGN KEY (constructor_id) REFERENCES Constructors(constructor_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| relationship_id | INTEGER | No | Auto | Primary key |
| vendor_id | INTEGER | No | - | FK to Technology_Vendors |
| constructor_id | INTEGER | No | - | FK to Constructors |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| preference_reason | TEXT | Yes | NULL | Why this constructor is preferred |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Business Rules:**
- Vendors can have multiple preferred constructors
- This is often confidential business strategy information
- Combination of (vendor_id, constructor_id) should be unique

**Indexes:**
```sql
CREATE INDEX idx_vendor_constructor_vendor ON Vendor_Preferred_Constructor(vendor_id);
CREATE INDEX idx_vendor_constructor_constructor ON Vendor_Preferred_Constructor(constructor_id);
CREATE INDEX idx_vendor_constructor_conf ON Vendor_Preferred_Constructor(is_confidential);
```

**Example:**
```sql
-- Vendor X prefers Constructor Y (confidential)
INSERT INTO Vendor_Preferred_Constructor 
(vendor_id, constructor_id, is_confidential, preference_reason, created_by)
VALUES (2, 3, 1, 'Previous successful projects, cost-effective', 1);
```

---

## Personnel_Entity_Relationships

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

### Complete Relationship Map

```
Technology_Vendors
├── Products (1:N)
├── Vendor_Supplier_Relationships (N:N with Technology_Vendors)
├── Owner_Vendor_Relationships (N:N with Owners_Developers)
├── Project_Vendor_Relationships (N:N with Projects)
├── Vendor_Preferred_Constructor (N:N with Constructors)
└── Personnel_Entity_Relationships (N:N with Personnel)

Owners_Developers
├── Owner_Vendor_Relationships (N:N with Technology_Vendors)
├── Project_Owner_Relationships (N:N with Projects)
├── Contact_Log (1:N)
├── Roundtable_History (1:N)
├── Entity_Team_Members (1:N with Personnel)
└── Personnel_Entity_Relationships (N:N with Personnel)

Projects
├── Project_Vendor_Relationships (N:N with Technology_Vendors)
├── Project_Constructor_Relationships (N:N with Constructors)
├── Project_Operator_Relationships (N:N with Operators)
├── Project_Owner_Relationships (N:N with Owners_Developers)
├── Entity_Team_Members (1:N with Personnel)
└── Personnel_Entity_Relationships (N:N with Personnel)

Constructors
├── Project_Constructor_Relationships (N:N with Projects)
├── Vendor_Preferred_Constructor (N:N with Technology_Vendors)
└── Personnel_Entity_Relationships (N:N with Personnel)

Operators
├── Project_Operator_Relationships (N:N with Projects)
└── Personnel_Entity_Relationships (N:N with Personnel)

Personnel
├── Personnel_Entity_Relationships (N:N with all entities)
├── Entity_Team_Members (N:N with all entities)
└── Referenced by Contact_Log, Owners_Developers POC fields
```

### Relationship Count by Type

| Relationship Type | Junction Table | Confidentiality |
|-------------------|----------------|-----------------|
| Vendor → Supplier | Vendor_Supplier_Relationships | Optional |
| Owner ↔ Vendor | Owner_Vendor_Relationships | Optional |
| Project → Vendor | Project_Vendor_Relationships | Optional |
| Project → Constructor | Project_Constructor_Relationships | Optional |
| Project → Operator | Project_Operator_Relationships | Optional |
| Project → Owner | Project_Owner_Relationships | Optional |
| Vendor → Constructor | Vendor_Preferred_Constructor | Optional |
| Personnel → Entity | Personnel_Entity_Relationships | Optional |
| Internal Personnel → Entity | Entity_Team_Members | No flag |

**Total Junction Tables:** 9

---

## Query Examples

### Get All Relationships for a Project

```sql
-- Get all vendors for Project 5
SELECT v.vendor_name, pvr.is_confidential, pvr.notes
FROM Project_Vendor_Relationships pvr
JOIN Technology_Vendors v ON pvr.vendor_id = v.vendor_id
WHERE pvr.project_id = 5
AND (pvr.is_confidential = 0 OR ? = 1);  -- ? = user has confidential access

-- Get all constructors for Project 5
SELECT c.company_name, pcr.is_confidential, pcr.notes
FROM Project_Constructor_Relationships pcr
JOIN Constructors c ON pcr.constructor_id = c.constructor_id
WHERE pcr.project_id = 5
AND (pcr.is_confidential = 0 OR ? = 1);

-- Get all personnel for Project 5
SELECT p.full_name, per.role_at_entity, per.is_confidential
FROM Personnel_Entity_Relationships per
JOIN Personnel p ON per.personnel_id = p.personnel_id
WHERE per.entity_type = 'Project' 
AND per.entity_id = 5
AND (per.is_confidential = 0 OR ? = 1);
```

### Get All Relationships for a Vendor

```sql
-- Get all suppliers for Vendor 3
SELECT s.vendor_name, vsr.component_type, vsr.is_confidential
FROM Vendor_Supplier_Relationships vsr
JOIN Technology_Vendors s ON vsr.supplier_id = s.vendor_id
WHERE vsr.vendor_id = 3
AND (vsr.is_confidential = 0 OR ? = 1);

-- Get all owners with agreements with Vendor 3
SELECT o.company_name, ovr.relationship_type, ovr.is_confidential
FROM Owner_Vendor_Relationships ovr
JOIN Owners_Developers o ON ovr.owner_id = o.owner_id
WHERE ovr.vendor_id = 3
AND (ovr.is_confidential = 0 OR ? = 1);

-- Get preferred constructors for Vendor 3
SELECT c.company_name, vpc.preference_reason, vpc.is_confidential
FROM Vendor_Preferred_Constructor vpc
JOIN Constructors c ON vpc.constructor_id = c.constructor_id
WHERE vpc.vendor_id = 3
AND (vpc.is_confidential = 0 OR ? = 1);
```

### Get Network Diagram Data

```sql
-- Get all visible relationships for network diagram
-- (Must respect confidentiality based on user permissions)

-- Example: Get all Project-Vendor relationships
SELECT 
    p.project_name,
    v.vendor_name,
    pvr.is_confidential
FROM Project_Vendor_Relationships pvr
JOIN Projects p ON pvr.project_id = p.project_id
JOIN Technology_Vendors v ON pvr.vendor_id = v.vendor_id
WHERE (pvr.is_confidential = 0 OR ? = 1)  -- User has confidential access
ORDER BY p.project_name;
```

### Count Relationships by Entity

```sql
-- Count all relationships for each vendor
SELECT 
    v.vendor_id,
    v.vendor_name,
    (SELECT COUNT(*) FROM Project_Vendor_Relationships WHERE vendor_id = v.vendor_id) as project_count,
    (SELECT COUNT(*) FROM Owner_Vendor_Relationships WHERE vendor_id = v.vendor_id) as owner_count,
    (SELECT COUNT(*) FROM Vendor_Supplier_Relationships WHERE vendor_id = v.vendor_id) as supplier_count,
    (SELECT COUNT(*) FROM Vendor_Preferred_Constructor WHERE vendor_id = v.vendor_id) as constructor_count
FROM Technology_Vendors v
ORDER BY v.vendor_name;
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

## Migration Considerations

When adding new relationship types in future:
1. Create new junction table following the pattern
2. Include is_confidential flag
3. Add appropriate indexes
4. Update network diagram serialization
5. Update permission checking logic

**Example future relationship:**
```sql
-- Hypothetical: Vendor partnerships
CREATE TABLE Vendor_Partnership_Relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id_1 INTEGER NOT NULL,
    vendor_id_2 INTEGER NOT NULL,
    partnership_type TEXT,
    is_confidential BOOLEAN DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (vendor_id_1) REFERENCES Technology_Vendors(vendor_id),
    FOREIGN KEY (vendor_id_2) REFERENCES Technology_Vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

---

## Next Steps

1. Review `04_DATA_DICTIONARY.md` for enum values and validation
2. Review `05_PERMISSION_SYSTEM.md` for access control implementation
3. Review `11_NETWORK_DIAGRAM.md` for relationship visualization
4. Implement relationship CRUD operations with permission checks

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