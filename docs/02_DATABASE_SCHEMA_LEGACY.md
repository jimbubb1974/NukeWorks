# 02_DATABASE_SCHEMA.md - Core Entity Tables

**Document Version:** 1.0  
**Last Updated:** December 4, 2025

**Related Documents:**
- `03_DATABASE_RELATIONSHIPS.md` - Junction tables
- `04_DATA_DICTIONARY.md` - Field definitions and enums
- `05_PERMISSION_SYSTEM.md` - Permission-related tables

---

## Table of Contents

1. [Technology_Vendors](#technology_vendors)
2. [Products](#products)
3. [Owners_Developers](#owners_developers)
4. [Operators](#operators)
5. [Constructors](#constructors)
6. [Projects](#projects)
7. [Personnel](#personnel)
8. [Users](#users)
9. [Contact_Log](#contact_log)
10. [Roundtable_History](#roundtable_history)
11. [Confidential_Field_Flags](#confidential_field_flags)
12. [Audit_Log](#audit_log)
13. [Database_Snapshots](#database_snapshots)
14. [System_Settings](#system_settings)
15. [Schema_Version](#schema_version)

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

## Technology_Vendors

**Purpose:** Track nuclear technology vendors and reactor developers

**SQL Definition:**
```sql
CREATE TABLE Technology_Vendors (
    vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| vendor_id | INTEGER | No | Auto | Primary key, unique identifier |
| vendor_name | TEXT | No | - | Company name (e.g., "NuScale Power", "X-energy") |
| notes | TEXT | Yes | NULL | Freeform notes about the vendor |
| created_by | INTEGER | Yes | - | FK to Users - who created this record |
| created_date | TIMESTAMP | No | NOW | When record was created |
| modified_by | INTEGER | Yes | - | FK to Users - who last modified |
| modified_date | TIMESTAMP | Yes | - | When last modified |

**Relationships:**
- Has many: Products (1:N)
- Has many: Owner_Vendor_Relationships (N:N via junction table)
- Has many: Vendor_Supplier_Relationships (N:N via junction table)
- Has many: Vendor_Preferred_Constructor (N:N via junction table)
- Has many: Project_Vendor_Relationships (N:N via junction table)

**Business Rules:**
- vendor_name should be unique (consider adding UNIQUE constraint)
- Cannot delete if Products exist or active relationships exist
- All text fields should be trimmed before save

**Indexes:**
```sql
CREATE INDEX idx_vendors_name ON Technology_Vendors(vendor_name);
CREATE INDEX idx_vendors_created ON Technology_Vendors(created_date);
```

---

## Products

**Purpose:** Specific reactor designs/models offered by vendors

**SQL Definition:**
```sql
CREATE TABLE Products (
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
    FOREIGN KEY (vendor_id) REFERENCES Technology_Vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| product_id | INTEGER | No | Auto | Primary key |
| product_name | TEXT | No | - | Model name (e.g., "Xe-100", "BWRX-300") |
| vendor_id | INTEGER | No | - | FK to Technology_Vendors |
| reactor_type | TEXT | Yes | NULL | Type (e.g., "PWR", "BWR", "SMR", "Micro") |
| thermal_capacity | REAL | Yes | NULL | Thermal output in MW |
| thermal_efficiency | REAL | Yes | NULL | Efficiency as percentage (e.g., 33.5) |
| burnup | REAL | Yes | NULL | Fuel burnup in GWd/MTU |
| design_status | TEXT | Yes | NULL | Status (e.g., "Conceptual", "Licensed", "Operating") |
| notes | TEXT | Yes | NULL | Freeform notes |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Relationships:**
- Belongs to: Technology_Vendors (N:1)

**Business Rules:**
- Each product must have a valid vendor_id
- thermal_capacity, thermal_efficiency, burnup must be positive if provided
- design_status should match enum values (see Data Dictionary)

**Indexes:**
```sql
CREATE INDEX idx_products_vendor ON Products(vendor_id);
CREATE INDEX idx_products_type ON Products(reactor_type);
```

---

## Owners_Developers

**Purpose:** Organizations that own or develop nuclear projects (utilities, IPPs, etc.)

**SQL Definition:**
```sql
CREATE TABLE Owners_Developers (
    owner_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    company_type TEXT,
    target_customers TEXT,
    engagement_level TEXT,
    notes TEXT,
    -- CRM Fields: Contact Tracking (Visible to All Users)
    primary_poc INTEGER,
    secondary_poc INTEGER,
    last_contact_date DATE,
    last_contact_type TEXT,
    last_contact_by INTEGER,
    last_contact_notes TEXT,
    next_planned_contact_date DATE,
    next_planned_contact_type TEXT,
    next_planned_contact_assigned_to INTEGER,
    -- CRM Fields: Internal Assessment (NED Team Only)
    relationship_strength TEXT,
    relationship_notes TEXT,
    client_priority TEXT,
    client_status TEXT,
    -- Standard audit fields
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (primary_poc) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (secondary_poc) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (last_contact_by) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (next_planned_contact_assigned_to) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Access | Description |
|-------|------|------|--------|-------------|
| owner_id | INTEGER | No | All | Primary key |
| company_name | TEXT | No | All | Company name |
| company_type | TEXT | Yes | All | IOU, COOP, Public Power, IPP |
| target_customers | TEXT | Yes | All | Market focus |
| engagement_level | TEXT | Yes | All | Intrigued, Interested, Invested, Inservice |
| notes | TEXT | Yes | All | Freeform notes |
| **CRM: Contact Tracking** | | | **All** | |
| primary_poc | INTEGER | Yes | All | FK to Personnel (internal) |
| secondary_poc | INTEGER | Yes | All | FK to Personnel (internal) |
| last_contact_date | DATE | Yes | All | Date of last contact |
| last_contact_type | TEXT | Yes | All | In-person, Phone, Email, Video |
| last_contact_by | INTEGER | Yes | All | FK to Personnel (internal) |
| last_contact_notes | TEXT | Yes | All | Summary of last contact |
| next_planned_contact_date | DATE | Yes | All | Date of next planned contact |
| next_planned_contact_type | TEXT | Yes | All | Type of next contact |
| next_planned_contact_assigned_to | INTEGER | Yes | All | FK to Personnel (internal) |
| **CRM: Internal Assessment** | | | **NED Team** | |
| relationship_strength | TEXT | Yes | NED | Strong, Good, Needs Attention, At Risk, New |
| relationship_notes | TEXT | Yes | NED | Internal assessment notes |
| client_priority | TEXT | Yes | NED | High, Medium, Low, Strategic, Opportunistic |
| client_status | TEXT | Yes | NED | Active, Warm, Cold, Prospective |
| **Audit Fields** | | | **All** | |
| created_by | INTEGER | Yes | All | FK to Users |
| created_date | TIMESTAMP | No | All | Creation timestamp |
| modified_by | INTEGER | Yes | All | FK to Users |
| modified_date | TIMESTAMP | Yes | All | Last modified timestamp |

**Relationships:**
- Has many: Project_Owner_Relationships (N:N via junction)
- Has many: Owner_Vendor_Relationships (N:N via junction)
- Has many: Contact_Log entries (1:N)
- Has many: Roundtable_History entries (1:N)
- Has many: Entity_Team_Members (1:N)

**Business Rules:**
- primary_poc and secondary_poc must reference Internal personnel only
- Contact tracking fields visible to all users
- Internal assessment fields (relationship_strength, etc.) visible to NED Team only
- See `05_PERMISSION_SYSTEM.md` for access control logic

**Indexes:**
```sql
CREATE INDEX idx_owners_name ON Owners_Developers(company_name);
CREATE INDEX idx_owners_priority ON Owners_Developers(client_priority);
CREATE INDEX idx_owners_poc ON Owners_Developers(primary_poc);
```

---

## Operators

**Purpose:** Companies that operate nuclear facilities

**SQL Definition:**
```sql
CREATE TABLE Operators (
    operator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| operator_id | INTEGER | No | Auto | Primary key |
| company_name | TEXT | No | - | Operator company name |
| notes | TEXT | Yes | NULL | Freeform notes |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Relationships:**
- Has many: Project_Operator_Relationships (N:N via junction)

**Business Rules:**
- company_name should be unique

**Indexes:**
```sql
CREATE INDEX idx_operators_name ON Operators(company_name);
```

---

## Constructors

**Purpose:** Construction companies that build nuclear facilities

**SQL Definition:**
```sql
CREATE TABLE Constructors (
    constructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| constructor_id | INTEGER | No | Auto | Primary key |
| company_name | TEXT | No | - | Constructor company name |
| notes | TEXT | Yes | NULL | Freeform notes |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Relationships:**
- Has many: Project_Constructor_Relationships (N:N via junction)
- Has many: Vendor_Preferred_Constructor (N:N via junction)

**Business Rules:**
- company_name should be unique

**Indexes:**
```sql
CREATE INDEX idx_constructors_name ON Constructors(company_name);
```

---

## Projects

**Purpose:** Specific nuclear project sites and deployments

**SQL Definition:**
```sql
CREATE TABLE Projects (
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
    -- Firm Involvement
    firm_involvement TEXT,
    primary_firm_contact INTEGER,
    last_project_interaction_date DATE,
    last_project_interaction_by INTEGER,
    project_health TEXT,
    -- Audit fields
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (primary_firm_contact) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (last_project_interaction_by) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Confidential? | Description |
|-------|------|------|---------|---------------|-------------|
| project_id | INTEGER | No | Auto | No | Primary key |
| project_name | TEXT | No | - | No | Project name |
| location | TEXT | Yes | NULL | No | Geographic location |
| project_status | TEXT | Yes | NULL | No | Planning, Design, Licensing, etc. |
| licensing_approach | TEXT | Yes | NULL | No | Research Reactor, Part 50, Part 52 |
| configuration | TEXT | Yes | NULL | No | Project configuration details |
| project_schedule | TEXT | Yes | NULL | No | Schedule information |
| latitude | REAL | Yes | NULL | No | Decimal degrees latitude (WGS84) |
| longitude | REAL | Yes | NULL | No | Decimal degrees longitude (WGS84) |
| capex | REAL | Yes | NULL | Optional | Capital expenditure |
| opex | REAL | Yes | NULL | Optional | Operating expenditure |
| fuel_cost | REAL | Yes | NULL | Optional | Fuel cost |
| lcoe | REAL | Yes | NULL | Optional | Levelized cost of energy |
| cod | DATE | Yes | NULL | No | Commercial operation date |
| mpr_project_id | TEXT | Yes | NULL | No | Link to external MPR project files |
| notes | TEXT | Yes | NULL | No | Freeform notes |
| firm_involvement | TEXT | Yes | NULL | No | Your firm's role |
| primary_firm_contact | INTEGER | Yes | NULL | No | FK to Personnel (internal) |
| last_project_interaction_date | DATE | Yes | NULL | No | Last interaction date |
| last_project_interaction_by | INTEGER | Yes | NULL | No | FK to Personnel (internal) |
| project_health | TEXT | Yes | NULL | No | On track, Delayed, At risk, Stalled |
| created_by | INTEGER | Yes | - | No | FK to Users |
| created_date | TIMESTAMP | No | NOW | No | Creation timestamp |
| modified_by | INTEGER | Yes | - | No | FK to Users |
| modified_date | TIMESTAMP | Yes | - | No | Last modified timestamp |

**Relationships:**
- Has many: Project_Vendor_Relationships (N:N via junction)
- Has many: Project_Constructor_Relationships (N:N via junction)
- Has many: Project_Operator_Relationships (N:N via junction)
- Has many: Project_Owner_Relationships (N:N via junction)

**Business Rules:**
- Financial fields (capex, opex, fuel_cost, lcoe) can be marked confidential per-record
- Latitude/longitude should reflect project site centroid; provide both values when available
- Use Confidential_Field_Flags table to mark specific fields as confidential
- cod (commercial operation date) should be future date if project not operational
- mpr_project_id is for display only - application doesn't auto-open files

**Indexes:**
```sql
CREATE INDEX idx_projects_name ON Projects(project_name);
CREATE INDEX idx_projects_status ON Projects(project_status);
CREATE INDEX idx_projects_location ON Projects(location);
CREATE INDEX idx_projects_cod ON Projects(cod);
CREATE INDEX idx_projects_lat_lon ON Projects(latitude, longitude);
```

---

## Personnel

**Purpose:** People - both internal team members and external contacts

**SQL Definition:**
```sql
CREATE TABLE Personnel (
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
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| personnel_id | INTEGER | No | Auto | Primary key |
| full_name | TEXT | No | - | Person's full name |
| email | TEXT | Yes | NULL | Email address |
| phone | TEXT | Yes | NULL | Phone number |
| role | TEXT | Yes | NULL | Job title/role |
| personnel_type | TEXT | Yes | NULL | Internal, Client_Contact, Vendor_Contact, etc. |
| organization_id | INTEGER | Yes | NULL | FK to parent organization (if external) |
| organization_type | TEXT | Yes | NULL | Owner, Vendor, Constructor, etc. |
| is_active | BOOLEAN | No | 1 | Whether person is still active |
| notes | TEXT | Yes | NULL | Freeform notes |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Relationships:**
- Referenced by: Owners_Developers (primary_poc, secondary_poc)
- Referenced by: Contact_Log (contacted_by, contact_person_id)
- Has many: Personnel_Entity_Relationships (N:N via junction)
- Has many: Entity_Team_Members (1:N)

**Business Rules:**
- personnel_type values: Internal, Client_Contact, Vendor_Contact, Constructor_Contact, Operator_Contact
- Internal personnel: organization_id and organization_type should be NULL
- External personnel: organization_id should reference appropriate entity
- POCs (primary/secondary) must be personnel_type = 'Internal'

**Indexes:**
```sql
CREATE INDEX idx_personnel_name ON Personnel(full_name);
CREATE INDEX idx_personnel_type ON Personnel(personnel_type);
CREATE INDEX idx_personnel_email ON Personnel(email);
CREATE INDEX idx_personnel_active ON Personnel(is_active);
```

---

## Users

**Purpose:** Application users with authentication and permissions

**SQL Definition:**
```sql
CREATE TABLE Users (
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
    is_active BOOLEAN DEFAULT 1
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| user_id | INTEGER | No | Auto | Primary key |
| username | TEXT | No | - | Login username (unique) |
| email | TEXT | No | - | Email address (unique) |
| password_hash | TEXT | No | - | Bcrypt hashed password |
| full_name | TEXT | Yes | NULL | User's full name |
| has_confidential_access | BOOLEAN | No | 0 | Tier 1: Can view confidential business data |
| is_ned_team | BOOLEAN | No | 0 | Tier 2: Can view internal CRM notes |
| is_admin | BOOLEAN | No | 0 | Administrator privileges |
| created_date | TIMESTAMP | No | NOW | Account creation date |
| last_login | TIMESTAMP | Yes | NULL | Last login timestamp |
| is_active | BOOLEAN | No | 1 | Account active status |

**Relationships:**
- Referenced by: Most tables (created_by, modified_by)
- Referenced by: Audit_Log (user_id)
- Referenced by: Database_Snapshots (created_by_user_id)

**Business Rules:**
- username and email must be unique
- password_hash must never be exposed in API or UI
- has_confidential_access and is_ned_team are independent permissions
- is_admin grants full access (overrides other permissions)
- is_active = 0 disables account (cannot login)

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_users_username ON Users(username);
CREATE UNIQUE INDEX idx_users_email ON Users(email);
CREATE INDEX idx_users_active ON Users(is_active);
```

**Security Notes:**
- Always use bcrypt or Werkzeug security for password hashing
- Minimum password length: 8 characters
- Session timeout: 8 hours of inactivity
- See `19_SECURITY.md` for complete security requirements

---

## Contact_Log

**Purpose:** Track interactions with clients (Owner/Developers)

**SQL Definition:**
```sql
CREATE TABLE Contact_Log (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    contact_date DATE NOT NULL,
    contact_type TEXT,
    contacted_by INTEGER NOT NULL,
    contact_person_id INTEGER,
    contact_person_freetext TEXT,
    summary TEXT,
    is_confidential BOOLEAN DEFAULT 0,
    follow_up_needed BOOLEAN DEFAULT 0,
    follow_up_date DATE,
    follow_up_assigned_to INTEGER,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (contacted_by) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (contact_person_id) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (follow_up_assigned_to) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| contact_id | INTEGER | No | Auto | Primary key |
| entity_type | TEXT | No | - | Currently "Owner" only |
| entity_id | INTEGER | No | - | FK to Owner/Developer |
| contact_date | DATE | No | - | Date of contact |
| contact_type | TEXT | Yes | NULL | In-person, Phone, Email, Video, Conference |
| contacted_by | INTEGER | No | - | FK to Personnel (internal team member) |
| contact_person_id | INTEGER | Yes | NULL | FK to Personnel (client contact if in system) |
| contact_person_freetext | TEXT | Yes | NULL | Client contact name if not in Personnel |
| summary | TEXT | Yes | NULL | Summary of interaction |
| is_confidential | BOOLEAN | No | 0 | Hide from users without confidential access |
| follow_up_needed | BOOLEAN | No | 0 | Follow-up required |
| follow_up_date | DATE | Yes | NULL | When to follow up |
| follow_up_assigned_to | INTEGER | Yes | NULL | FK to Personnel (internal) |
| created_by | INTEGER | Yes | - | FK to Users |
| created_date | TIMESTAMP | No | NOW | Creation timestamp |
| modified_by | INTEGER | Yes | - | FK to Users |
| modified_date | TIMESTAMP | Yes | - | Last modified timestamp |

**Relationships:**
- Belongs to: Owners_Developers (via entity_id when entity_type = 'Owner')

**Business Rules:**
- entity_type currently only supports "Owner" (client contacts only)
- contacted_by must be Internal personnel
- Either contact_person_id OR contact_person_freetext should be populated
- is_confidential flag separate from NED Team access (Tier 1 vs Tier 2)
- contact_date cannot be in the future

**Indexes:**
```sql
CREATE INDEX idx_contact_log_entity ON Contact_Log(entity_type, entity_id);
CREATE INDEX idx_contact_log_date ON Contact_Log(contact_date);
CREATE INDEX idx_contact_log_by ON Contact_Log(contacted_by);
CREATE INDEX idx_contact_log_followup ON Contact_Log(follow_up_needed, follow_up_date);
```

---

## Roundtable_History

**Purpose:** Store internal meeting notes about clients (NED Team only)

**SQL Definition:**
```sql
CREATE TABLE Roundtable_History (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    meeting_date DATE NOT NULL,
    discussion TEXT,
    action_items TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Access | Description |
|-------|------|------|--------|-------------|
| history_id | INTEGER | No | NED | Primary key |
| entity_type | TEXT | No | NED | Entity type (Owner, Project, etc.) |
| entity_id | INTEGER | No | NED | FK to specific entity |
| meeting_date | DATE | No | NED | Date of roundtable meeting |
| discussion | TEXT | Yes | NED | Meeting discussion notes |
| action_items | TEXT | Yes | NED | Action items from meeting |
| created_by | INTEGER | Yes | NED | FK to Users |
| created_date | TIMESTAMP | No | NED | Creation timestamp |

**Relationships:**
- Belongs to: Owners_Developers (via entity_id when entity_type = 'Owner')

**Business Rules:**
- **NED Team access only** - entire table restricted
- Application maintains maximum N entries per entity (N from System_Settings)
- When limit reached, oldest entry is permanently deleted
- Default limit: 3 entries per entity
- No modified_by/modified_date - entries are append-only

**Indexes:**
```sql
CREATE INDEX idx_roundtable_entity ON Roundtable_History(entity_type, entity_id);
CREATE INDEX idx_roundtable_date ON Roundtable_History(meeting_date);
```

**Maintenance Query:**
```sql
-- Query to find entries to delete when limit exceeded
SELECT history_id 
FROM Roundtable_History 
WHERE entity_type = ? AND entity_id = ?
ORDER BY meeting_date ASC
LIMIT (COUNT(*) - ?)  -- Keep last N entries
```

---

## Confidential_Field_Flags

**Purpose:** Mark specific fields as confidential on a per-record basis

**SQL Definition:**
```sql
CREATE TABLE Confidential_Field_Flags (
    flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    is_confidential BOOLEAN DEFAULT 1,
    marked_by INTEGER,
    marked_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (marked_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| flag_id | INTEGER | No | Auto | Primary key |
| table_name | TEXT | No | - | Table containing the field (e.g., "Projects") |
| record_id | INTEGER | No | - | ID of specific record |
| field_name | TEXT | No | - | Field name (e.g., "capex") |
| is_confidential | BOOLEAN | No | 1 | Whether field is confidential |
| marked_by | INTEGER | Yes | - | FK to Users who marked it |
| marked_date | TIMESTAMP | No | NOW | When it was marked |

**Relationships:**
- None (generic table for flagging any field)

**Business Rules:**
- Used for Tier 1 confidentiality (business data)
- Combination of (table_name, record_id, field_name) should be unique
- If no flag exists, field is assumed public
- Users without has_confidential_access see "[Confidential - Access Restricted]"

**Common Fields That Get Flagged:**
- Projects: capex, opex, fuel_cost, lcoe
- Any financial or sensitive business data

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_conf_flags_unique 
ON Confidential_Field_Flags(table_name, record_id, field_name);
CREATE INDEX idx_conf_flags_table ON Confidential_Field_Flags(table_name);
```

**Usage Example:**
```sql
-- Mark Project 45's CAPEX as confidential
INSERT INTO Confidential_Field_Flags 
(table_name, record_id, field_name, marked_by)
VALUES ('Projects', 45, 'capex', 1);

-- Check if field is confidential
SELECT is_confidential 
FROM Confidential_Field_Flags 
WHERE table_name = 'Projects' 
AND record_id = 45 
AND field_name = 'capex';
```

---

## Audit_Log

**Purpose:** Track all CREATE, UPDATE, DELETE operations

**SQL Definition:**
```sql
CREATE TABLE Audit_Log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id INTEGER,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| log_id | INTEGER | No | Auto | Primary key |
| user_id | INTEGER | Yes | - | FK to Users who performed action |
| timestamp | TIMESTAMP | No | NOW | When action occurred |
| action | TEXT | No | - | CREATE, UPDATE, DELETE |
| table_name | TEXT | No | - | Table that was modified |
| record_id | INTEGER | Yes | - | ID of record modified |
| field_name | TEXT | Yes | NULL | Specific field (for UPDATE) |
| old_value | TEXT | Yes | NULL | Previous value (for UPDATE/DELETE) |
| new_value | TEXT | Yes | NULL | New value (for CREATE/UPDATE) |
| notes | TEXT | Yes | NULL | Additional context |

**Relationships:**
- Belongs to: Users (user performing action)

**Business Rules:**
- Log all CREATE, UPDATE, DELETE operations
- Do NOT log READ operations
- Values stored as TEXT (serialize complex types to JSON)
- Logs never deleted (permanent record)
- Admin-only access to full audit log

**Indexes:**
```sql
CREATE INDEX idx_audit_user ON Audit_Log(user_id);
CREATE INDEX idx_audit_timestamp ON Audit_Log(timestamp);
CREATE INDEX idx_audit_table ON Audit_Log(table_name);
CREATE INDEX idx_audit_record ON Audit_Log(table_name, record_id);
CREATE INDEX idx_audit_action ON Audit_Log(action);
```

**Usage Example:**
```sql
-- Log an UPDATE operation
INSERT INTO Audit_Log 
(user_id, action, table_name, record_id, field_name, old_value, new_value)
VALUES (1, 'UPDATE', 'Projects', 45, 'capex', '40000000', '50000000');

-- Log a CREATE operation
INSERT INTO Audit_Log 
(user_id, action, table_name, record_id, new_value)
VALUES (1, 'CREATE', 'Vendors', 123, '{"vendor_name": "NewVendor", ...}');
```

---

## Database_Snapshots

**Purpose:** Track database backup/snapshot metadata

**SQL Definition:**
```sql
CREATE TABLE Database_Snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    snapshot_type TEXT,
    file_path TEXT NOT NULL,
    description TEXT,
    snapshot_size_bytes INTEGER,
    is_retained BOOLEAN DEFAULT 0,
    FOREIGN KEY (created_by_user_id) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| snapshot_id | INTEGER | No | Auto | Primary key |
| snapshot_timestamp | TIMESTAMP | No | NOW | When snapshot was created |
| created_by_user_id | INTEGER | Yes | NULL | FK to Users (NULL if automated) |
| snapshot_type | TEXT | Yes | NULL | MANUAL, AUTOMATED_DAILY, AUTOMATED_WEEKLY |
| file_path | TEXT | No | - | Full path to snapshot file |
| description | TEXT | Yes | NULL | User description (for manual) |
| snapshot_size_bytes | INTEGER | Yes | NULL | File size in bytes |
| is_retained | BOOLEAN | No | 0 | Mark as important (prevent auto-delete) |

**Relationships:**
- Belongs to: Users (creator, if manual)

**Business Rules:**
- Automated snapshots have created_by_user_id = NULL
- Snapshots with is_retained = 1 are never auto-deleted
- Snapshot cleanup based on System_Settings (retention_days, max_snapshots)
- file_path should be absolute path to .sqlite file

**Indexes:**
```sql
CREATE INDEX idx_snapshots_timestamp ON Database_Snapshots(snapshot_timestamp);
CREATE INDEX idx_snapshots_type ON Database_Snapshots(snapshot_type);
CREATE INDEX idx_snapshots_retained ON Database_Snapshots(is_retained);
```

**Cleanup Logic:**
- Delete snapshots older than retention_days (unless is_retained = 1)
- Keep only max_snapshots most recent (unless is_retained = 1)

---

## System_Settings

**Purpose:** Store configurable application settings

**SQL Definition:**
```sql
CREATE TABLE System_Settings (
    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type TEXT,
    description TEXT,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| setting_id | INTEGER | No | Auto | Primary key |
| setting_name | TEXT | No | - | Unique setting name |
| setting_value | TEXT | Yes | NULL | Setting value (as text) |
| setting_type | TEXT | Yes | NULL | integer, boolean, text, date |
| description | TEXT | Yes | NULL | Human-readable description |
| modified_by | INTEGER | Yes | - | FK to Users who last modified |
| modified_date | TIMESTAMP | Yes | - | When last modified |

**Relationships:**
- None

**Initial Settings to Populate:**
```sql
INSERT INTO System_Settings (setting_name, setting_value, setting_type, description) VALUES
('company_name', 'MPR Associates', 'text', 'Company name for reports'),
('company_logo_path', '', 'text', 'Path to company logo file'),
('roundtable_history_limit', '3', 'integer', 'Number of roundtable entries to keep per entity'),
('auto_snapshot_enabled', 'true', 'boolean', 'Enable automated database snapshots'),
('daily_snapshot_time', '02:00', 'text', 'Time for daily snapshots (HH:MM 24-hour)'),
('snapshot_retention_days', '30', 'integer', 'Days to keep automated snapshots'),
('max_snapshots', '10', 'integer', 'Maximum number of snapshots to keep'),
('confidential_watermark_enabled', 'true', 'boolean', 'Add CONFIDENTIAL watermark to reports'),
('confidential_watermark_text', 'CONFIDENTIAL', 'text', 'Watermark text for reports');
```

**Business Rules:**
- setting_name must be unique
- setting_type guides parsing (convert string to appropriate type)
- Admin-only write access

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_settings_name ON System_Settings(setting_name);
```

---

## Schema_Version

**Purpose:** Track database schema version for migrations

**SQL Definition:**
```sql
CREATE TABLE Schema_Version (
    version INTEGER PRIMARY KEY,
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by TEXT,
    description TEXT
);
```

**Field Reference:**

| Field | Type | Null | Default | Description |
|-------|------|------|---------|-------------|
| version | INTEGER | No | - | Schema version number (1, 2, 3...) |
| applied_date | TIMESTAMP | No | NOW | When migration was applied |
| applied_by | TEXT | Yes | NULL | Who/what applied it ('system', username) |
| description | TEXT | Yes | NULL | Description of migration |

**Relationships:**
- None

**Business Rules:**
- Single row per version
- version numbers sequential starting at 1
- First entry: (1, NOW, 'system', 'Initial schema creation')
- Never delete entries - permanent record of migrations

**Initial Entry:**
```sql
INSERT INTO Schema_Version (version, applied_date, applied_by, description)
VALUES (1, CURRENT_TIMESTAMP, 'system', 'Initial schema creation');
```

**Usage:**
```sql
-- Get current schema version
SELECT MAX(version) FROM Schema_Version;

-- Check if version 5 has been applied
SELECT COUNT(*) FROM Schema_Version WHERE version = 5;
```

---

## Complete Schema Creation Script

**File: `schema_v1.sql`**

```sql
-- NukeWorks Database Schema v1.0
-- Initial schema creation

BEGIN TRANSACTION;

-- Core Entity Tables
CREATE TABLE Technology_Vendors (...);
CREATE TABLE Products (...);
CREATE TABLE Owners_Developers (...);
CREATE TABLE Operators (...);
CREATE TABLE Constructors (...);
CREATE TABLE Projects (...);
CREATE TABLE Personnel (...);

-- User & Permission Tables
CREATE TABLE Users (...);
CREATE TABLE Confidential_Field_Flags (...);

-- CRM Tables
CREATE TABLE Contact_Log (...);
CREATE TABLE Roundtable_History (...);

-- System Tables
CREATE TABLE Audit_Log (...);
CREATE TABLE Database_Snapshots (...);
CREATE TABLE System_Settings (...);
CREATE TABLE Schema_Version (...);

-- Indexes (see individual table sections above)
-- ...

-- Initial System Settings
INSERT INTO System_Settings (...) VALUES (...);

-- Initial Schema Version
INSERT INTO Schema_Version (version, applied_by, description)
VALUES (1, 'system', 'Initial schema creation');

COMMIT;
```

---

## Summary Statistics

**Total Tables:** 15

**Core Business Entities:** 7
- Technology_Vendors
- Products  
- Owners_Developers
- Operators
- Constructors
- Projects
- Personnel

**Relationship Tables:** (See `03_DATABASE_RELATIONSHIPS.md`)

**Support Tables:** 8
- Users
- Confidential_Field_Flags
- Contact_Log
- Roundtable_History
- Audit_Log
- Database_Snapshots
- System_Settings
- Schema_Version

---

## Next Steps

1. Review `03_DATABASE_RELATIONSHIPS.md` for junction tables
2. Review `04_DATA_DICTIONARY.md` for enums and validation rules
3. Review `05_PERMISSION_SYSTEM.md` for access control logic
4. Begin implementation with schema creation script

---

**Document End**
