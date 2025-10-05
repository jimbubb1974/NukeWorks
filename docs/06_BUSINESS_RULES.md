# 06_BUSINESS_RULES.md

**Document:** Business Rules & Data Validation  
**Version:** 1.0  
**Last Updated:** December 4, 2025  
**Related Documents:** `02_DATABASE_SCHEMA.md`, `04_DATA_DICTIONARY.md`, `05_PERMISSION_SYSTEM.md`

---

## Table of Contents

1. [Overview](#overview)
2. [Data Validation Rules](#data-validation-rules)
3. [Business Logic Rules](#business-logic-rules)
4. [Relationship Rules](#relationship-rules)
5. [Permission-Based Rules](#permission-based-rules)
6. [Workflow Rules](#workflow-rules)
7. [Data Integrity Rules](#data-integrity-rules)

---

## 1. Overview

This document defines the business rules, validation logic, and constraints that govern data entry, modification, and relationships within NukeWorks. These rules ensure data consistency, integrity, and alignment with business requirements.

### Rule Categories

- **Validation Rules:** Field-level data type and format validation
- **Business Logic Rules:** Domain-specific constraints and requirements
- **Relationship Rules:** Rules governing entity relationships
- **Permission-Based Rules:** Access control and visibility rules
- **Workflow Rules:** State transitions and process flows
- **Data Integrity Rules:** Referential integrity and consistency

---

## 2. Data Validation Rules

### 2.1 Common Field Validation

#### Required Fields

**Technology_Vendors:**
- `vendor_name` - REQUIRED, non-empty string

**Products:**
- `product_name` - REQUIRED, non-empty string
- `vendor_id` - REQUIRED, must reference existing vendor

**Owners_Developers:**
- `company_name` - REQUIRED, non-empty string

**Projects:**
- `project_name` - REQUIRED, non-empty string

**Personnel:**
- `full_name` - REQUIRED, non-empty string

**Users:**
- `username` - REQUIRED, unique, non-empty
- `email` - REQUIRED, unique, valid email format
- `password_hash` - REQUIRED, non-empty

#### String Field Validation

```python
def validate_string_field(value, field_name, max_length=255, required=True):
    """
    Standard string field validation
    
    Rules:
    - Strip leading/trailing whitespace
    - Check if empty when required
    - Validate max length
    - No control characters except newlines (for notes fields)
    """
    if value is None:
        if required:
            raise ValidationError(f"{field_name} is required")
        return None
    
    value = value.strip()
    
    if required and len(value) == 0:
        raise ValidationError(f"{field_name} cannot be empty")
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length}")
    
    # Check for invalid characters (except newlines for text areas)
    if any(ord(c) < 32 and c not in ['\n', '\r', '\t'] for c in value):
        raise ValidationError(f"{field_name} contains invalid characters")
    
    return value
```

#### Numeric Field Validation

```python
def validate_numeric_field(value, field_name, min_value=None, max_value=None, allow_null=True):
    """
    Numeric field validation
    
    Rules:
    - Allow NULL if allow_null=True
    - Must be valid number (int or float)
    - Check min/max bounds if specified
    - No negative values for capacity, cost fields (unless explicitly allowed)
    """
    if value is None:
        if not allow_null:
            raise ValidationError(f"{field_name} is required")
        return None
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number")
    
    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")
    
    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}")
    
    return value
```

**Specific Numeric Field Rules:**

- **thermal_capacity:** Must be positive (> 0) if provided
- **thermal_efficiency:** Range 0-100 (percentage)
- **burnup:** Must be positive if provided
- **capex, opex, fuel_cost, lcoe:** Must be positive if provided

#### Date Field Validation

```python
def validate_date_field(value, field_name, allow_future=True, allow_past=True):
    """
    Date field validation
    
    Rules:
    - Must be valid date format (YYYY-MM-DD)
    - Check future/past constraints
    - COD (Commercial Operation Date) can be in future
    - Contact dates typically in past or present
    """
    if value is None:
        return None
    
    try:
        date_obj = datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError(f"{field_name} must be in YYYY-MM-DD format")
    
    today = date.today()
    
    if not allow_future and date_obj > today:
        raise ValidationError(f"{field_name} cannot be in the future")
    
    if not allow_past and date_obj < today:
        raise ValidationError(f"{field_name} cannot be in the past")
    
    return date_obj
```

**Specific Date Field Rules:**

- **cod (Commercial Operation Date):** Can be future date
- **last_contact_date:** Must be past or present
- **next_planned_contact_date:** Can be future date
- **created_date, modified_date:** System-managed, always valid

#### Email Validation

```python
def validate_email(email, field_name="email"):
    """
    Email validation
    
    Rules:
    - Basic format: user@domain.tld
    - Valid characters only
    - Not case-sensitive (store lowercase)
    """
    if email is None:
        return None
    
    email = email.strip().lower()
    
    # Basic email regex
    pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError(f"{field_name} must be a valid email address")
    
    return email
```

#### Phone Validation

```python
def validate_phone(phone, field_name="phone"):
    """
    Phone validation
    
    Rules:
    - Allow various formats: (555) 123-4567, 555-123-4567, +1-555-123-4567
    - Store in consistent format
    - International numbers allowed
    """
    if phone is None:
        return None
    
    phone = phone.strip()
    
    # Remove common separators for validation
    digits = re.sub(r'[^0-9+]', '', phone)
    
    if len(digits) < 10:
        raise ValidationError(f"{field_name} must contain at least 10 digits")
    
    return phone  # Store as entered (preserves formatting)
```

### 2.2 Enumerated Field Validation

**company_type (Owners_Developers):**
```python
VALID_COMPANY_TYPES = ['IOU', 'COOP', 'Public Power', 'IPP', 'Other']

def validate_company_type(value):
    if value is None:
        return None
    if value not in VALID_COMPANY_TYPES:
        raise ValidationError(f"company_type must be one of: {', '.join(VALID_COMPANY_TYPES)}")
    return value
```

**engagement_level (Owners_Developers):**
```python
VALID_ENGAGEMENT_LEVELS = ['Intrigued', 'Interested', 'Invested', 'Inservice']

def validate_engagement_level(value):
    if value is None:
        return None
    if value not in VALID_ENGAGEMENT_LEVELS:
        raise ValidationError(f"engagement_level must be one of: {', '.join(VALID_ENGAGEMENT_LEVELS)}")
    return value
```

**project_status (Projects):**
```python
VALID_PROJECT_STATUSES = ['Conceptual', 'Planning', 'Design', 'Licensing', 
                          'Construction', 'Commissioning', 'Operating', 
                          'Decommissioned', 'Cancelled', 'On Hold']

def validate_project_status(value):
    if value is None:
        return None
    if value not in VALID_PROJECT_STATUSES:
        raise ValidationError(f"project_status must be one of: {', '.join(VALID_PROJECT_STATUSES)}")
    return value
```

**licensing_approach (Projects):**
```python
VALID_LICENSING_APPROACHES = ['Research Reactor', 'Part 50', 'Part 52']

def validate_licensing_approach(value):
    if value is None:
        return None
    if value not in VALID_LICENSING_APPROACHES:
        raise ValidationError(f"licensing_approach must be one of: {', '.join(VALID_LICENSING_APPROACHES)}")
    return value
```

**contact_type (Contact_Log):**
```python
VALID_CONTACT_TYPES = ['In-person', 'Phone', 'Email', 'Video', 'Conference']

def validate_contact_type(value):
    if value is None:
        return None
    if value not in VALID_CONTACT_TYPES:
        raise ValidationError(f"contact_type must be one of: {', '.join(VALID_CONTACT_TYPES)}")
    return value
```

**relationship_type (Owner_Vendor_Relationships):**
```python
VALID_RELATIONSHIP_TYPES = ['MOU', 'Development_Agreement', 'Delivery_Contract', 'Other']

def validate_relationship_type(value):
    if value is None:
        return None
    if value not in VALID_RELATIONSHIP_TYPES:
        raise ValidationError(f"relationship_type must be one of: {', '.join(VALID_RELATIONSHIP_TYPES)}")
    return value
```

---

## 3. Business Logic Rules

### 3.1 Entity Creation Rules

#### Technology Vendors

**Rule BL-TV-001:** Vendor names must be unique
```python
def validate_unique_vendor_name(vendor_name, vendor_id=None):
    """
    Ensure vendor name is unique
    vendor_id is provided when updating (exclude self from check)
    """
    query = "SELECT vendor_id FROM Technology_Vendors WHERE LOWER(vendor_name) = LOWER(?)"
    params = [vendor_name]
    
    if vendor_id is not None:
        query += " AND vendor_id != ?"
        params.append(vendor_id)
    
    existing = db.execute(query, params).fetchone()
    
    if existing:
        raise ValidationError(f"Vendor '{vendor_name}' already exists")
```

#### Products

**Rule BL-PR-001:** Product name must be unique within a vendor
```python
def validate_unique_product_name(product_name, vendor_id, product_id=None):
    """
    Product names must be unique per vendor
    """
    query = """
        SELECT product_id FROM Products 
        WHERE LOWER(product_name) = LOWER(?) AND vendor_id = ?
    """
    params = [product_name, vendor_id]
    
    if product_id is not None:
        query += " AND product_id != ?"
        params.append(product_id)
    
    existing = db.execute(query, params).fetchone()
    
    if existing:
        raise ValidationError(f"Product '{product_name}' already exists for this vendor")
```

**Rule BL-PR-002:** Vendor must exist before adding products
```python
def validate_vendor_exists(vendor_id):
    """
    Vendor must exist in database
    """
    vendor = db.execute("SELECT vendor_id FROM Technology_Vendors WHERE vendor_id = ?", 
                       [vendor_id]).fetchone()
    
    if not vendor:
        raise ValidationError(f"Vendor with ID {vendor_id} does not exist")
```

#### Projects

**Rule BL-PJ-001:** Project names should be unique (warning, not error)
```python
def check_duplicate_project_name(project_name, project_id=None):
    """
    Check for duplicate project names
    Return warning rather than error (allowed but discouraged)
    """
    query = "SELECT project_id, project_name FROM Projects WHERE LOWER(project_name) = LOWER(?)"
    params = [project_name]
    
    if project_id is not None:
        query += " AND project_id != ?"
        params.append(project_id)
    
    existing = db.execute(query, params).fetchone()
    
    if existing:
        return f"Warning: A project named '{project_name}' already exists"
    
    return None
```

**Rule BL-PJ-002:** COD must be after today for non-operating projects
```python
def validate_cod_for_status(cod, project_status):
    """
    COD validation based on project status
    """
    if cod is None:
        return  # COD is optional
    
    today = date.today()
    
    if project_status in ['Conceptual', 'Planning', 'Design', 'Licensing', 'Construction']:
        if cod <= today:
            raise ValidationError("Commercial Operation Date must be in the future for non-operating projects")
    
    elif project_status == 'Operating':
        if cod > today:
            raise ValidationError("Commercial Operation Date must be in the past for operating projects")
```

### 3.2 CRM-Specific Rules

#### Contact Logging

**Rule BL-CL-001:** Contact date cannot be in the future
```python
def validate_contact_date(contact_date):
    """
    Contact logs are historical records
    """
    today = date.today()
    
    if contact_date > today:
        raise ValidationError("Contact date cannot be in the future")
```

**Rule BL-CL-002:** Either contact_person_id or contact_person_freetext required
```python
def validate_contact_person(contact_person_id, contact_person_freetext):
    """
    At least one method of identifying the contact person is required
    """
    if contact_person_id is None and (contact_person_freetext is None or contact_person_freetext.strip() == ''):
        raise ValidationError("Contact person must be specified (select from list or enter name)")
```

**Rule BL-CL-003:** Follow-up date must be in future if specified
```python
def validate_follow_up_date(follow_up_date):
    """
    Follow-up dates are for future actions
    """
    if follow_up_date is None:
        return
    
    today = date.today()
    
    if follow_up_date <= today:
        raise ValidationError("Follow-up date should be in the future")
```

#### Roundtable History

**Rule BL-RT-001:** Maximum N roundtable entries per entity
```python
def enforce_roundtable_limit(entity_type, entity_id):
    """
    Keep only the most recent N roundtable entries per entity
    N is configured in System_Settings (default: 3)
    """
    limit = get_system_setting('roundtable_history_limit', default=3)
    
    # Get count of existing entries
    count = db.execute("""
        SELECT COUNT(*) as cnt FROM Roundtable_History 
        WHERE entity_type = ? AND entity_id = ?
    """, [entity_type, entity_id]).fetchone()['cnt']
    
    if count >= limit:
        # Delete oldest entries to make room
        db.execute("""
            DELETE FROM Roundtable_History 
            WHERE history_id IN (
                SELECT history_id FROM Roundtable_History
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY meeting_date ASC
                LIMIT ?
            )
        """, [entity_type, entity_id, count - limit + 1])
```

**Rule BL-RT-002:** Meeting date cannot be in the future
```python
def validate_meeting_date(meeting_date):
    """
    Roundtable entries are for past meetings
    """
    today = date.today()
    
    if meeting_date > today:
        raise ValidationError("Meeting date cannot be in the future")
```

### 3.3 User Management Rules

**Rule BL-US-001:** Username must be unique (case-insensitive)
```python
def validate_unique_username(username, user_id=None):
    """
    Usernames are case-insensitive unique
    """
    query = "SELECT user_id FROM Users WHERE LOWER(username) = LOWER(?)"
    params = [username]
    
    if user_id is not None:
        query += " AND user_id != ?"
        params.append(user_id)
    
    existing = db.execute(query, params).fetchone()
    
    if existing:
        raise ValidationError(f"Username '{username}' is already taken")
```

**Rule BL-US-002:** Email must be unique
```python
def validate_unique_email(email, user_id=None):
    """
    Email addresses must be unique
    """
    query = "SELECT user_id FROM Users WHERE LOWER(email) = LOWER(?)"
    params = [email]
    
    if user_id is not None:
        query += " AND user_id != ?"
        params.append(user_id)
    
    existing = db.execute(query, params).fetchone()
    
    if existing:
        raise ValidationError(f"Email '{email}' is already registered")
```

**Rule BL-US-003:** Password strength requirements
```python
def validate_password_strength(password):
    """
    Password must meet minimum security requirements
    
    Rules:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - Cannot contain username (checked elsewhere)
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit")
    
    # Optional: Check against common passwords list
    if password.lower() in COMMON_PASSWORDS:
        raise ValidationError("Password is too common. Please choose a stronger password")
```

**Rule BL-US-004:** Cannot delete last admin user
```python
def validate_can_delete_user(user_id):
    """
    Prevent deletion of last admin user
    """
    user = get_user(user_id)
    
    if user.is_admin:
        admin_count = db.execute("SELECT COUNT(*) as cnt FROM Users WHERE is_admin = 1 AND is_active = 1").fetchone()['cnt']
        
        if admin_count <= 1:
            raise ValidationError("Cannot delete the last administrator account")
```

**Rule BL-US-005:** Cannot remove admin rights from last admin
```python
def validate_can_remove_admin_rights(user_id):
    """
    Prevent removing admin rights from last admin user
    """
    admin_count = db.execute("SELECT COUNT(*) as cnt FROM Users WHERE is_admin = 1 AND is_active = 1").fetchone()['cnt']
    
    if admin_count <= 1:
        raise ValidationError("Cannot remove admin rights from the last administrator")
```

---

## 4. Relationship Rules

### 4.1 General Relationship Rules

**Rule RL-001:** Both entities must exist before creating relationship
```python
def validate_relationship_entities_exist(entity1_type, entity1_id, entity2_type, entity2_id):
    """
    Both entities must exist in their respective tables
    """
    # Check entity 1
    table1 = get_table_name_for_entity_type(entity1_type)
    id_column1 = get_id_column_for_entity_type(entity1_type)
    
    exists1 = db.execute(f"SELECT {id_column1} FROM {table1} WHERE {id_column1} = ?", 
                        [entity1_id]).fetchone()
    
    if not exists1:
        raise ValidationError(f"{entity1_type} with ID {entity1_id} does not exist")
    
    # Check entity 2
    table2 = get_table_name_for_entity_type(entity2_type)
    id_column2 = get_id_column_for_entity_type(entity2_type)
    
    exists2 = db.execute(f"SELECT {id_column2} FROM {table2} WHERE {id_column2} = ?", 
                        [entity2_id]).fetchone()
    
    if not exists2:
        raise ValidationError(f"{entity2_type} with ID {entity2_id} does not exist")
```

**Rule RL-002:** Prevent duplicate relationships
```python
def validate_no_duplicate_relationship(relationship_table, entity1_id_col, entity1_id, 
                                      entity2_id_col, entity2_id, relationship_id=None):
    """
    Prevent creating duplicate relationships between same two entities
    """
    query = f"""
        SELECT relationship_id FROM {relationship_table} 
        WHERE {entity1_id_col} = ? AND {entity2_id_col} = ?
    """
    params = [entity1_id, entity2_id]
    
    if relationship_id is not None:
        query += " AND relationship_id != ?"
        params.append(relationship_id)
    
    existing = db.execute(query, params).fetchone()
    
    if existing:
        raise ValidationError("This relationship already exists")
```

**Rule RL-003:** Cannot create self-relationships (vendor to same vendor)
```python
def validate_no_self_relationship(entity1_id, entity2_id, relationship_type):
    """
    Prevent entity from having relationship with itself
    Applies to Vendor_Supplier_Relationships
    """
    if entity1_id == entity2_id:
        raise ValidationError(f"Cannot create {relationship_type} relationship with the same entity")
```

### 4.2 Vendor-Supplier Rules

**Rule RL-VS-001:** Vendor-Supplier relationships must be between two vendors
```python
def validate_vendor_supplier_relationship(vendor_id, supplier_id):
    """
    Both IDs must reference valid Technology_Vendors
    """
    validate_vendor_exists(vendor_id)
    validate_vendor_exists(supplier_id)
    validate_no_self_relationship(vendor_id, supplier_id, "vendor-supplier")
```

### 4.3 Project Relationship Rules

**Rule RL-PJ-001:** A project can have only one primary vendor
```python
def validate_single_primary_vendor(project_id, new_vendor_id, relationship_id=None):
    """
    Check if project already has a primary vendor
    This is business logic - enforce through UI or application logic
    """
    # This could be a warning rather than hard constraint
    existing = db.execute("""
        SELECT vendor_id FROM Project_Vendor_Relationships 
        WHERE project_id = ? AND vendor_id != ? AND is_primary = 1
    """, [project_id, new_vendor_id]).fetchall()
    
    if len(existing) > 0:
        return f"Warning: Project already has a primary vendor. This will create a secondary relationship."
    
    return None
```

### 4.4 Personnel Relationship Rules

**Rule RL-PE-001:** Personnel must have valid organization reference
```python
def validate_personnel_organization(organization_id, organization_type):
    """
    If organization_id is specified, organization_type must be specified
    and the organization must exist
    """
    if organization_id is None:
        return  # No organization specified is valid
    
    if organization_type is None:
        raise ValidationError("organization_type must be specified when organization_id is provided")
    
    # Validate organization exists
    table_name = get_table_name_for_entity_type(organization_type)
    id_column = get_id_column_for_entity_type(organization_type)
    
    exists = db.execute(f"SELECT {id_column} FROM {table_name} WHERE {id_column} = ?", 
                       [organization_id]).fetchone()
    
    if not exists:
        raise ValidationError(f"{organization_type} with ID {organization_id} does not exist")
```

---

## 5. Permission-Based Rules

### 5.1 Data Modification Rules

**Rule PM-001:** Users can only edit data they can view
```python
def validate_can_edit_field(user, table_name, record_id, field_name):
    """
    User must have permission to view field before editing
    """
    if not can_view_field(user, table_name, record_id, field_name):
        raise PermissionError(f"You do not have permission to edit {field_name}")
```

**Rule PM-002:** Non-admin users cannot modify system-managed fields
```python
SYSTEM_MANAGED_FIELDS = ['created_by', 'created_date', 'modified_by', 'modified_date']

def validate_can_modify_field(user, field_name):
    """
    System-managed fields can only be set by the system
    """
    if field_name in SYSTEM_MANAGED_FIELDS and not user.is_admin:
        raise PermissionError(f"Cannot manually modify {field_name}")
```

**Rule PM-003:** Users can mark data as confidential if they can view it
```python
def validate_can_mark_confidential(user, table_name, record_id, field_name):
    """
    User must be able to view the field to mark it confidential
    """
    if not can_view_field(user, table_name, record_id, field_name):
        raise PermissionError("You do not have permission to modify confidentiality settings for this field")
```

**Rule PM-004:** Only NED Team members can edit CRM internal notes
```python
def validate_can_edit_ned_content(user):
    """
    Only NED Team members can edit relationship assessments and roundtable notes
    """
    if not can_view_ned_content(user):
        raise PermissionError("Only NED Team members can edit internal CRM notes")
```

### 5.2 Deletion Rules

**Rule PM-DEL-001:** Users can only delete entities they can fully view
```python
def validate_can_delete_entity(user, entity_type, entity_id):
    """
    User must have full access to entity to delete it
    Check all fields are viewable
    """
    # Get all fields for entity
    fields = get_all_fields_for_entity(entity_type, entity_id)
    
    for field_name in fields:
        if not can_view_field(user, entity_type, entity_id, field_name):
            raise PermissionError(f"Cannot delete {entity_type} - contains confidential data you cannot access")
```

**Rule PM-DEL-002:** Cannot delete entities with dependent relationships
```python
def validate_can_delete_with_dependencies(entity_type, entity_id):
    """
    Check for dependent relationships before deletion
    Offer to delete relationships or prevent deletion
    """
    # Check for dependent records
    dependencies = get_entity_dependencies(entity_type, entity_id)
    
    if dependencies:
        dependency_list = format_dependency_list(dependencies)
        raise ValidationError(f"Cannot delete {entity_type} - it has the following dependencies: {dependency_list}")
```

---

## 6. Workflow Rules

### 6.1 Project Workflow

**Rule WF-PJ-001:** Project status transitions
```python
VALID_STATUS_TRANSITIONS = {
    'Conceptual': ['Planning', 'Cancelled', 'On Hold'],
    'Planning': ['Design', 'Cancelled', 'On Hold'],
    'Design': ['Licensing', 'Cancelled', 'On Hold'],
    'Licensing': ['Construction', 'Cancelled', 'On Hold'],
    'Construction': ['Commissioning', 'Cancelled', 'On Hold'],
    'Commissioning': ['Operating', 'Cancelled'],
    'Operating': ['Decommissioned'],
    'On Hold': ['Conceptual', 'Planning', 'Design', 'Licensing', 'Construction', 'Cancelled'],
    'Cancelled': [],  # Terminal state
    'Decommissioned': []  # Terminal state
}

def validate_status_transition(current_status, new_status):
    """
    Validate project status transitions follow allowed workflow
    """
    if current_status == new_status:
        return  # No change
    
    allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])
    
    if new_status not in allowed_transitions:
        raise ValidationError(f"Invalid status transition from {current_status} to {new_status}")
```

### 6.2 Contact Workflow

**Rule WF-CL-001:** Completed follow-ups should update last contact
```python
def update_last_contact_from_followup(owner_id, follow_up_date):
    """
    When follow-up date passes, suggest updating last_contact_date
    This is typically done through UI prompts
    """
    if follow_up_date <= date.today():
        return {
            'suggestion': 'update_last_contact',
            'message': 'Follow-up date has passed. Would you like to log this as a completed contact?'
        }
```

---

## 7. Data Integrity Rules

### 7.1 Referential Integrity

**Rule DI-001:** Foreign key constraints must be enforced
```python
# Enable foreign keys in SQLite
db.execute("PRAGMA foreign_keys = ON")

# All foreign key relationships are defined in schema
# SQLite will enforce these constraints automatically when enabled
```

**Rule DI-002:** Cascade delete rules
```python
# Defined in schema, but document the logic:

CASCADE_DELETE_RULES = {
    'Technology_Vendors': {
        'Products': 'CASCADE',  # Delete products when vendor deleted
        'Vendor_Supplier_Relationships': 'CASCADE',
        'Owner_Vendor_Relationships': 'CASCADE',
        'Project_Vendor_Relationships': 'CASCADE',
        'Vendor_Preferred_Constructor': 'CASCADE'
    },
    'Projects': {
        'Project_Vendor_Relationships': 'CASCADE',
        'Project_Constructor_Relationships': 'CASCADE',
        'Project_Operator_Relationships': 'CASCADE',
        'Project_Owner_Relationships': 'CASCADE',
        'Contact_Log': 'CASCADE',
        'Roundtable_History': 'CASCADE'
    },
    'Personnel': {
        'Contact_Log': 'SET NULL',  # Keep log but clear person reference
        'Personnel_Entity_Relationships': 'CASCADE'
    }
}
```

### 7.2 Data Consistency Rules

**Rule DI-CON-001:** Timestamp consistency
```python
def validate_timestamp_consistency(created_date, modified_date):
    """
    modified_date must be >= created_date
    """
    if created_date and modified_date:
        if modified_date < created_date:
            raise ValidationError("Modified date cannot be before created date")
```

**Rule DI-CON-002:** Confidential field flag consistency
```python
def validate_confidential_flag_integrity(table_name, record_id):
    """
    Ensure confidential flags reference valid records
    Clean up orphaned flags when records are deleted
    """
    # Check if record exists
    id_column = get_id_column_for_table(table_name)
    exists = db.execute(f"SELECT {id_column} FROM {table_name} WHERE {id_column} = ?", 
                       [record_id]).fetchone()
    
    if not exists:
        # Delete orphaned confidential flags
        db.execute("""
            DELETE FROM Confidential_Field_Flags 
            WHERE table_name = ? AND record_id = ?
        """, [table_name, record_id])
```

### 7.3 Transaction Rules

**Rule DI-TX-001:** Multi-step operations must be atomic
```python
def create_project_with_relationships(project_data, relationships):
    """
    Creating a project with relationships must be atomic
    If any step fails, entire operation rolls back
    """
    try:
        db.begin_transaction()
        
        # Create project
        project_id = create_project(project_data)
        
        # Create relationships
        for rel in relationships:
            create_relationship(project_id, rel)
        
        db.commit()
        return project_id
        
    except Exception as e:
        db.rollback()
        raise e
```

---

## 8. Import Validation Rules

### 8.1 Import Data Validation

**Rule IM-001:** Validate all data before importing
```python
def validate_import_row(row, entity_type, row_number):
    """
    Validate each row before import
    Collect all errors for the row
    """
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS[entity_type]:
        if not row.get(field) or str(row[field]).strip() == '':
            errors.append(f"Row {row_number}: Missing required field '{field}'")
    
    # Validate field formats
    for field, value in row.items():
        try:
            validate_field_value(field, value, entity_type)
        except ValidationError as e:
            errors.append(f"Row {row_number}: {str(e)}")
    
    # Check for duplicates
    if entity_type == 'Technology_Vendors':
        try:
            validate_unique_vendor_name(row.get('vendor_name'))
        except ValidationError as e:
            errors.append(f"Row {row_number}: {str(e)}")
    
    return errors
```

**Rule IM-002:** Provide import preview with validation results
```python
def preview_import(import_data, entity_type):
    """
    Show preview of import with validation errors
    Allow user to correct before importing
    """
    preview = {
        'total_rows': len(import_data),
        'valid_rows': 0,
        'invalid_rows': 0,
        'errors': []
    }
    
    for idx, row in enumerate(import_data):
        errors = validate_import_row(row, entity_type, idx + 1)
        
        if errors:
            preview['invalid_rows'] += 1
            preview['errors'].extend(errors)
        else:
            preview['valid_rows'] += 1
    
    return preview
```

---

## 9. Audit Rules

**Rule AU-001:** Log all CREATE, UPDATE, DELETE operations
```python
def log_operation(user_id, operation, table_name, record_id, changes=None):
    """
    All data modifications must be logged
    """
    if operation in ['CREATE', 'UPDATE', 'DELETE']:
        create_audit_log_entry(
            user_id=user_id,
            action=operation,
            table_name=table_name,
            record_id=record_id,
            changes=changes
        )
```

**Rule AU-002:** Log permission changes
```python
def log_permission_change(admin_user_id, target_user_id, permission_type, old_value, new_value):
    """
    Permission changes must be logged
    """
    create_audit_log_entry(
        user_id=admin_user_id,
        action='UPDATE',
        table_name='Users',
        record_id=target_user_id,
        field_name=permission_type,
        old_value=str(old_value),
        new_value=str(new_value),
        notes=f"Permission change: {permission_type}"
    )
```

---

## 10. Snapshot Rules

**Rule SN-001:** Automated snapshots cannot be deleted by users
```python
def validate_can_delete_snapshot(user, snapshot):
    """
    Only manual snapshots or marked snapshots can be deleted
    Automated snapshots are managed by system
    """
    if snapshot.snapshot_type.startswith('AUTOMATED_') and not snapshot.is_retained:
        if not user.is_admin:
            raise PermissionError("Automated snapshots can only be deleted by administrators")
```

**Rule SN-002:** Verify snapshot integrity before restore
```python
def validate_snapshot_integrity(snapshot_path):
    """
    Verify snapshot file is valid SQLite database before restoring
    """
    try:
        test_conn = sqlite3.connect(snapshot_path)
        test_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        test_conn.close()
    except Exception as e:
        raise ValidationError(f"Snapshot file is corrupted or invalid: {str(e)}")
```

---

## 11. Summary of Key Business Rules

### Critical Rules
1. **Unique Constraints:** Vendor names, usernames, emails must be unique
2. **Required Fields:** vendor_name, product_name, company_name, project_name, full_name, username, email, password_hash
3. **Permission-Based Access:** Users can only view/edit data they have permission for
4. **Referential Integrity:** All foreign keys must reference valid records
5. **Audit Logging:** All CREATE, UPDATE, DELETE operations must be logged

### Important Rules
6. **Password Strength:** Minimum 8 characters, mixed case, digit required
7. **Date Validation:** Contact dates in past, follow-ups in future, COD based on project status
8. **Status Transitions:** Project status changes must follow valid workflow
9. **Roundtable Limits:** Keep only N most recent entries per entity
10. **Transaction Atomicity:** Multi-step operations must be atomic

### Validation Order
1. Required field validation
2. Data type validation
3. Format validation (email, phone, date)
4. Business rule validation (uniqueness, relationships)
5. Permission validation
6. Integrity validation (foreign keys, consistency)

---

## 12. Error Messages

### Standard Error Message Format
```python
def format_validation_error(field_name, error_type, details=None):
    """
    Consistent error message formatting
    """
    messages = {
        'required': f"{field_name} is required",
        'invalid_format': f"{field_name} has an invalid format",
        'out_of_range': f"{field_name} is out of valid range",
        'duplicate': f"{field_name} already exists",
        'not_found': f"{field_name} not found",
        'invalid_relationship': f"Invalid relationship: {details}"
    }
    
    message = messages.get(error_type, f"{field_name}: {error_type}")
    
    if details:
        message += f" ({details})"
    
    return message
```

### User-Friendly Error Messages
- Avoid technical jargon
- Provide actionable guidance
- Include field name in error
- Show what was expected vs. what was provided
- Suggest corrections when possible

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Dec 4, 2025 | Initial business rules specification | [Author] |

---

**END OF DOCUMENT**