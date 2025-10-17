# 05_PERMISSION_SYSTEM.md - Access Control & Confidentiality

**Document Version:** 1.0  
**Last Updated:** December 4, 2025

**Related Documents:**
- `02_DATABASE_SCHEMA.md` - Users table, Confidential_Field_Flags table
- `03_DATABASE_RELATIONSHIPS.md` - Relationship confidentiality
- `04_DATA_DICTIONARY.md` - Encrypted fields and validation
- `ENCRYPTION_IMPLEMENTATION_STATUS.md` - Encryption phases and status
- `19_SECURITY.md` - Security best practices

---

## Overview

NukeWorks implements a **two-tier confidentiality system** that controls access to different types of sensitive information:

- **Tier 1: Business Data Confidentiality** - Protects sensitive business information (financial data, confidential relationships)
- **Tier 2: Internal Team Notes (NED Team)** - Protects internal strategy and assessment notes

These two tiers are **independent** - a user can have either, both, or neither permission.

---

## Table of Contents

1. [Permission Tiers](#permission-tiers)
2. [User Permission Levels](#user-permission-levels)
3. [Tier 1: Business Data Confidentiality](#tier-1-business-data-confidentiality)
4. [Tier 2: NED Team Access](#tier-2-ned-team-access)
5. [Encryption & Field-Level Access Control](#encryption--field-level-access-control) ⭐ NEW
6. [Permission Checking Functions](#permission-checking-functions)
7. [Display Logic](#display-logic)
8. [Admin Permissions](#admin-permissions)
9. [Permission Management UI](#permission-management-ui)
10. [Security Considerations](#security-considerations)

---

## Permission Tiers

### Tier 1: Business Data Confidentiality

**Purpose:** Control access to sensitive business information

**Grants Access To:**
- Financial data marked as confidential (CAPEX, OPEX, fuel costs, LCOE)
- Relationships marked as confidential (vendor-supplier, project-constructor, etc.)
- Contact log entries marked as confidential
- Any field flagged in Confidential_Field_Flags table

**Database Field:** `Users.has_confidential_access`

**Examples of Tier 1 Data:**
- Project Alpha's CAPEX of $50M (if flagged confidential)
- Vendor X's relationship with Supplier Y (if flagged confidential)
- Constructor negotiation details (if flagged confidential)

### Tier 2: Internal Team Notes (NED Team)

**Purpose:** Control access to internal strategy and client assessment notes

**Grants Access To:**
- Client relationship assessments (relationship_strength, client_priority, client_status)
- Relationship notes (internal strategy)
- Roundtable discussion history
- Action items from roundtable meetings

**Database Field:** `Users.is_ned_team`

**Examples of Tier 2 Data:**
- "Client relationship needs attention - competitor offering lower price"
- Monthly roundtable discussion notes
- Internal assessment: "Strategic priority - allocate more resources"

### Independence of Tiers

```
User Permission Matrix:

┌─────────────────────┬─────────────────┬──────────────────┐
│ User Type           │ Tier 1          │ Tier 2           │
│                     │ (Confidential)  │ (NED Team)       │
├─────────────────────┼─────────────────┼──────────────────┤
│ Regular User        │ No              │ No               │
│ Business Analyst    │ Yes             │ No               │
│ Strategy Team       │ No              │ Yes              │
│ Senior Manager      │ Yes             │ Yes              │
│ Administrator       │ Yes (override)  │ Yes (override)   │
└─────────────────────┴─────────────────┴──────────────────┘
```

---

## User Permission Levels

### Regular User

**Permissions:**
- View all public data
- View public relationships
- View contact tracking (dates, types, non-confidential notes)
- Create/edit/delete data they have access to
- Cannot see: Confidential business data, NED Team notes

**Database Values:**
```sql
has_confidential_access = 0
is_ned_team = 0
is_admin = 0
```

### User with Confidential Access

**Permissions:**
- All Regular User permissions
- View confidential business data (financial info, confidential relationships)
- View confidential contact log entries
- Cannot see: NED Team notes

**Database Values:**
```sql
has_confidential_access = 1
is_ned_team = 0
is_admin = 0
```

### NED Team Member

**Permissions:**
- All Regular User permissions
- View internal client assessments (relationship strength, priority, status)
- View roundtable discussion history
- View relationship notes (internal strategy)
- May or may not have Confidential Access (independent)

**Database Values:**
```sql
has_confidential_access = 0 or 1  -- Independent
is_ned_team = 1
is_admin = 0
```

### Administrator

**Permissions:**
- Full access to all data (overrides all restrictions)
- User management (create, edit, delete users)
- Permission assignment
- System settings management
- Snapshot management
- View complete audit logs

**Database Values:**
```sql
has_confidential_access = 1  -- Typically, but overridden by is_admin
is_ned_team = 1              -- Typically, but overridden by is_admin
is_admin = 1
```

---

## Tier 1: Business Data Confidentiality

### Field-Level Confidentiality

**Mechanism:** Confidential_Field_Flags table

**How It Works:**
1. User marks specific field as confidential during data entry
2. Record created in Confidential_Field_Flags table
3. Application checks this table before displaying field values
4. Users without confidential access see "[Confidential - Access Restricted]"

**Example:**
```sql
-- Mark Project 45's CAPEX as confidential
INSERT INTO Confidential_Field_Flags 
(table_name, record_id, field_name, is_confidential, marked_by)
VALUES ('Projects', 45, 'capex', 1, 1);
```

**Checking Logic:**
```python
def can_view_field(user, table_name, record_id, field_name):
    """
    Check if user can view a specific field
    
    Returns: Boolean
    """
    # Check if field is flagged as confidential
    flag = db.query(Confidential_Field_Flags).filter_by(
        table_name=table_name,
        record_id=record_id,
        field_name=field_name
    ).first()
    
    # If no flag exists, field is public
    if not flag or not flag.is_confidential:
        return True
    
    # Field is confidential - check user permission
    return user.has_confidential_access or user.is_admin
```

**Display Logic:**
```python
def get_field_display_value(user, entity, field_name):
    """
    Get display value for a field, respecting confidentiality
    
    Returns: String (actual value or restriction message)
    """
    actual_value = getattr(entity, field_name)
    
    if can_view_field(user, entity.__tablename__, entity.id, field_name):
        return actual_value
    else:
        return "[Confidential - Access Restricted]"
```

### Relationship-Level Confidentiality

**Mechanism:** `is_confidential` boolean flag on junction tables

**How It Works:**
1. User marks relationship as confidential during creation
2. `is_confidential` flag set to 1 in junction table
3. Application filters relationships in queries
4. Users without confidential access don't see the relationship at all

**Example:**
```sql
-- Mark Project-Constructor relationship as confidential
INSERT INTO Project_Constructor_Relationships 
(project_id, constructor_id, is_confidential, notes, created_by)
VALUES (45, 12, 1, 'In contract negotiations', 1);
```

**Checking Logic:**
```python
def can_view_relationship(user, relationship):
    """
    Check if user can view a specific relationship
    
    Returns: Boolean
    """
    if not relationship.is_confidential:
        return True
    
    return user.has_confidential_access or user.is_admin
```

**Query Pattern:**
```python
def get_visible_relationships(user, project_id):
    """
    Get all visible relationships for a project
    """
    relationships = db.query(Project_Vendor_Relationships).filter_by(
        project_id=project_id
    )
    
    # Filter based on user permissions
    if not (user.has_confidential_access or user.is_admin):
        relationships = relationships.filter_by(is_confidential=False)
    
    return relationships.all()
```

### Common Fields That Can Be Confidential

**Projects:**
- capex (Capital Expenditure)
- opex (Operating Expenditure)
- fuel_cost
- lcoe (Levelized Cost of Energy)
- Any field user deems sensitive

**Any Table:**
- Users can mark any field as confidential
- No predefined list - flexible per deployment

### Bulk Confidentiality Operations

**Mark Multiple Fields:**
```python
def mark_all_financial_fields_confidential(project_id, user_id):
    """
    Mark all financial fields of a project as confidential
    """
    financial_fields = ['capex', 'opex', 'fuel_cost', 'lcoe']
    
    for field in financial_fields:
        db.add(Confidential_Field_Flags(
            table_name='Projects',
            record_id=project_id,
            field_name=field,
            is_confidential=True,
            marked_by=user_id
        ))
    
    db.commit()
```

---

## Tier 2: NED Team Access

### What NED Team Can Access

**In Owners_Developers Table:**
- `relationship_strength` - Assessment of relationship quality
- `relationship_notes` - Internal strategy notes
- `client_priority` - Priority ranking (High, Medium, Low, Strategic)
- `client_status` - Engagement status (Active, Warm, Cold, Prospective)

**In Roundtable_History Table:**
- `discussion` - Meeting discussion notes
- `action_items` - Action items from roundtable

**Note:** Contact tracking fields (last_contact_date, etc.) are visible to ALL users

### Checking Logic

```python
def can_view_ned_content(user):
    """
    Check if user can view NED Team content
    
    Returns: Boolean
    """
    return user.is_ned_team or user.is_admin
```

### Query Patterns

**Retrieving Owner with NED Fields:**
```python
def get_owner_for_display(user, owner_id):
    """
    Get owner with appropriate field visibility
    """
    owner = db.query(Owners_Developers).get(owner_id)
    
    if not can_view_ned_content(user):
        # Redact NED Team fields
        owner.relationship_strength = None
        owner.relationship_notes = "[Access Restricted - NED Team Only]"
        owner.client_priority = None
        owner.client_status = None
    
    return owner
```

**Retrieving Roundtable History:**
```python
def get_roundtable_history(user, entity_type, entity_id):
    """
    Get roundtable history entries (NED Team only)
    """
    if not can_view_ned_content(user):
        return []  # Return empty list if no access
    
    return db.query(Roundtable_History).filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(Roundtable_History.meeting_date.desc()).limit(3).all()
```

### Display Behavior

**For Non-NED Users:**

In UI, show:
```
CLIENT RELATIONSHIP MANAGEMENT
───────────────────────────────────────────────────────────
[Contact tracking section - VISIBLE]

INTERNAL ASSESSMENT [Access Restricted - NED Team Only]
───────────────────────────────────────────────────────────
This section is only visible to NED Team members.

ROUNDTABLE DISCUSSION [Access Restricted - NED Team Only]
───────────────────────────────────────────────────────────
This section is only visible to NED Team members.
```

**For NED Team Members:**

In UI, show full content:
```
INTERNAL ASSESSMENT (NED Team Only)
───────────────────────────────────────────────────────────
Client Priority:      [High ▼]
Client Status:        [Active ▼]
Relationship:         [Needs Attention ▼]

Relationship Notes:   [Large text area with internal notes]

ROUNDTABLE DISCUSSION (NED Team Only)
───────────────────────────────────────────────────────────
[Full roundtable history displayed]
```

### No Field-by-Field Flagging

**Important:** NED Team content is NOT flagged field-by-field. Access is all-or-nothing based on user's `is_ned_team` flag.

This differs from Tier 1, where individual fields can be marked confidential.

---

## Encryption & Field-Level Access Control

### Per-Field Encryption Overview

In addition to permission-based access control, NukeWorks implements **per-field encryption** at the database level. This provides an additional layer of protection where sensitive fields are encrypted and only decrypted for authorized users.

**Key Distinction:**
- **Permissions** (this document): Control who can see data based on user roles
- **Encryption**: Protects data at rest and enforces decryption-time access checks

### How Encryption Works with Permissions

**Step 1: Permission Check**
- First, permission system checks if user is authorized to view the field category
- Example: Is user `has_confidential_access=True`?

**Step 2: Encryption/Decryption**
- If permitted, encrypted value is decrypted before display
- If not permitted, placeholder text shown (no decryption attempted)

**Example Access Flow for Project.capex (Financial Data):**
```
User requests Project financials
↓
Permission check: has_confidential_access=True?
├─ YES → Decrypt capex_encrypted → Display $50,000,000
└─ NO → Display "[Confidential]" (no decryption)
```

### Active Encryption Implementation

**Phase 3a: Project Financial Fields (LIVE)**

Financial fields in Projects table are encrypted:

| Field | Encryption Key | Required Permission | Encrypted Column |
|-------|---|---|---|
| capex | 'confidential' | `has_confidential_access=True` | capex_encrypted |
| opex | 'confidential' | `has_confidential_access=True` | opex_encrypted |
| fuel_cost | 'confidential' | `has_confidential_access=True` | fuel_cost_encrypted |
| lcoe | 'confidential' | `has_confidential_access=True` | lcoe_encrypted |

**Display Behavior:**
```python
# If user has confidential access AND is decrypting
user.has_confidential_access=True → project.capex = 50000000 (actual value)

# If user lacks confidential access
user.has_confidential_access=False → project.capex = "[Confidential]" (placeholder)
```

### Planned Encryption (Phases 3b-3e)

See `ENCRYPTION_IMPLEMENTATION_STATUS.md` for details on:

- **Phase 3b: ClientProfile NED Team Fields** (relationship_strength, notes, priority, status)
  - Encryption key: 'ned_team'
  - Required permission: `is_ned_team=True`

- **Phase 3c: RoundtableHistory NED Team Fields** (discussion, action_items, next_steps, etc.)
  - Encryption key: 'ned_team'
  - Required permission: `is_ned_team=True`

- **Phase 3d: CompanyRoleAssignment Notes** (conditional)
  - Encryption key: 'confidential'
  - Required permission: `has_confidential_access=True` (if is_confidential=True)

- **Phase 3e: InternalExternalLink NED Team Fields**
  - Encryption key: 'ned_team'
  - Required permission: `is_ned_team=True`

### Implementation Details

**Database Storage:**
- Encrypted fields stored as BLOB type (binary data)
- Original plaintext columns retained for backward compatibility (not yet removed)
- Both columns present during transition period

**Permission Integration:**
```python
# Encryption system checks permission at decryption time
class EncryptedField:
    def __get__(self, obj, type=None):
        if not self.user_has_permission():
            return self.placeholder  # e.g., "[Confidential]"

        encrypted_value = getattr(obj, self.storage_column)
        return decrypt(encrypted_value, self.key)

# Permission check uses same user permission flags
def user_has_permission(self):
    user = current_user
    if self.key == 'confidential':
        return user.has_confidential_access or user.is_admin
    elif self.key == 'ned_team':
        return user.is_ned_team or user.is_admin
```

### Security Benefits

**Double Protection:**
1. **Permission layer**: Users must have appropriate permission flags to be authorized
2. **Encryption layer**: Even if data accessed directly, remains encrypted without key
3. **Access audit**: Decryption attempts logged with user, timestamp, field

**At-Rest Security:**
- Encrypted data in database is gibberish without decryption key
- Database backups contain encrypted data
- Improves compliance (SOC2, ISO27001, etc.)

### Access Control Example: Combined Permissions + Encryption

**Scenario: Viewing Project Financial Data**

**User: jdoe (has_confidential_access=True, is_ned_team=False)**
- Viewing Project Alpha details
- capex_encrypted column exists (BLOB of encrypted $50M)
- Permission check: ✅ has_confidential_access=True
- Decryption: ✅ Allowed
- **Result:** Sees actual CAPEX value ($50,000,000)

**User: slee (has_confidential_access=False, is_ned_team=True)**
- Viewing same Project Alpha details
- capex_encrypted column exists (BLOB of encrypted $50M)
- Permission check: ❌ has_confidential_access=False
- Decryption: ❌ Prevented
- **Result:** Sees placeholder ("[Confidential]")

### Best Practices

**For Developers:**
1. **Use property access**: Access encrypted fields through EncryptedField properties, not columns directly
2. **Check permissions early**: Permission checks happen at read time, not query time
3. **Handle placeholders**: UI must handle placeholder text gracefully
4. **Never log encrypted values**: Logs show field name, not actual values

**For Administrators:**
1. **Manage permission flags**: Grant `has_confidential_access` to appropriate users
2. **Monitor encryption**: Check logs for decryption attempts
3. **Backup keys safely**: Keep encryption keys secure and backed up
4. **Test access**: Regularly verify permission logic working correctly

### Troubleshooting

**User sees "[Confidential]" but claims they should have access:**
1. Check user `has_confidential_access` flag in Users table
2. Verify permission change replicated to all servers (if distributed)
3. Check encryption system logs for errors
4. Try clearing user session cache

**Decryption errors in logs:**
1. Check encryption key hasn't been rotated
2. Verify BLOB column data not corrupted
3. Check database backup/restore completed successfully

---

## Permission Checking Functions

### Core Permission Functions

```python
# permission_helpers.py

def can_view_field(user, table_name, record_id, field_name):
    """
    Tier 1: Check if user can view a specific field value
    """
    flag = get_confidential_flag(table_name, record_id, field_name)
    
    if not flag or not flag.is_confidential:
        return True
    
    return user.has_confidential_access or user.is_admin


def can_view_relationship(user, relationship):
    """
    Tier 1: Check if user can view a relationship
    """
    if not relationship.is_confidential:
        return True
    
    return user.has_confidential_access or user.is_admin


def can_view_ned_content(user):
    """
    Tier 2: Check if user can view NED Team content
    """
    return user.is_ned_team or user.is_admin


def can_edit_entity(user, entity):
    """
    Check if user can edit an entity
    Rule: Can edit if can view all non-confidential fields
    """
    # Admins can always edit
    if user.is_admin:
        return True
    
    # Users can edit entities they can fully see
    # (Implementation depends on whether entity has confidential fields)
    return True  # Basic rule: if you can see it, you can edit it


def can_change_confidentiality(user, table_name, record_id, field_name):
    """
    Check if user can change confidentiality flag
    Rule: Can change if can currently view the field
    """
    return can_view_field(user, table_name, record_id, field_name)


def can_manage_users(user):
    """
    Check if user can manage other users
    """
    return user.is_admin


def can_manage_snapshots(user):
    """
    Check if user can create/restore snapshots
    """
    return user.is_admin


def can_view_audit_log(user):
    """
    Check if user can view full audit log
    """
    return user.is_admin
```

### Flask Decorator Examples

```python
from functools import wraps
from flask import abort
from flask_login import current_user

def confidential_access_required(f):
    """
    Decorator: Require Tier 1 confidential access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.has_confidential_access or current_user.is_admin):
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


def ned_team_required(f):
    """
    Decorator: Require Tier 2 NED Team access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_ned_team or current_user.is_admin):
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator: Require administrator access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function
```

### Usage in Routes

```python
@app.route('/projects/<int:project_id>')
@login_required
def view_project(project_id):
    """View project details with appropriate field filtering"""
    project = db.query(Projects).get_or_404(project_id)
    
    # Filter fields based on permissions
    display_project = filter_confidential_fields(current_user, project)
    
    return render_template('project_detail.html', project=display_project)


@app.route('/owners/<int:owner_id>/crm')
@login_required
@ned_team_required
def view_owner_crm(owner_id):
    """View CRM details (NED Team only)"""
    owner = db.query(Owners_Developers).get_or_404(owner_id)
    roundtable_history = get_roundtable_history(current_user, 'Owner', owner_id)
    
    return render_template('owner_crm.html', 
                         owner=owner, 
                         roundtable_history=roundtable_history)


@app.route('/admin/users')
@login_required
@admin_required
def manage_users():
    """User management (Admin only)"""
    users = db.query(Users).all()
    return render_template('admin_users.html', users=users)
```

---

## Display Logic

### Field Display Logic

```python
def get_display_value(user, entity, field_name):
    """
    Get display value for a field with permission checking
    """
    # Check if this is a NED Team field
    ned_fields = ['relationship_strength', 'relationship_notes', 
                  'client_priority', 'client_status']
    
    if field_name in ned_fields:
        if not can_view_ned_content(user):
            return "[Access Restricted - NED Team Only]"
    
    # Check if field is marked confidential (Tier 1)
    if not can_view_field(user, entity.__tablename__, entity.id, field_name):
        return "[Confidential - Access Restricted]"
    
    # User has access - return actual value
    return getattr(entity, field_name)
```

### Relationship Display Logic

```python
def get_visible_relationships(user, relationships):
    """
    Filter relationships based on user permissions
    """
    visible = []
    hidden_count = 0
    
    for rel in relationships:
        if can_view_relationship(user, rel):
            visible.append(rel)
        else:
            hidden_count += 1
    
    return visible, hidden_count
```

### Network Diagram Display Logic

```python
def serialize_network_for_user(user):
    """
    Serialize network data respecting user permissions
    """
    nodes = []
    edges = []
    
    # Get all entities (nodes) - these are always visible
    vendors = db.query(Technology_Vendors).all()
    for vendor in vendors:
        nodes.append({
            'id': f'vendor_{vendor.vendor_id}',
            'label': vendor.vendor_name,
            'group': 'vendor'
        })
    
    # Get relationships (edges) - filter by confidentiality
    relationships = db.query(Project_Vendor_Relationships).all()
    for rel in relationships:
        # Skip confidential relationships if user lacks access
        if rel.is_confidential and not (user.has_confidential_access or user.is_admin):
            continue
        
        edges.append({
            'from': f'project_{rel.project_id}',
            'to': f'vendor_{rel.vendor_id}',
            'label': 'Technology'
        })
    
    return {'nodes': nodes, 'edges': edges}
```

### Report Display Logic

```python
def generate_project_report(user, project_id):
    """
    Generate project report with confidentiality filtering
    """
    project = db.query(Projects).get(project_id)
    
    # Build report data
    report_data = {
        'project_name': project.project_name,
        'location': project.location,
        'status': project.project_status,
    }
    
    # Financial data - check confidentiality
    if can_view_field(user, 'Projects', project_id, 'capex'):
        report_data['capex'] = project.capex
    else:
        report_data['capex'] = '[Confidential]'
    
    # Relationships - filter confidential
    vendors = get_visible_relationships(user, project.vendors)
    report_data['vendors'] = vendors
    
    # Add watermark if report contains confidential data
    report_data['add_watermark'] = user.has_confidential_access
    
    return generate_pdf(report_data)
```

---

## Admin Permissions

### Admin Capabilities

Administrators have full override permissions:

```python
def is_admin(user):
    """Check if user is administrator"""
    return user.is_admin

# Admins can:
# - View all data (confidential and NED Team content)
# - Create, edit, delete any entity
# - Manage users and permissions
# - Create and restore snapshots
# - View complete audit logs
# - Modify system settings
# - Access admin-only UI sections
```

### Admin Override Logic

```python
# In permission checking functions, always check is_admin first:

def can_view_field(user, table_name, record_id, field_name):
    if user.is_admin:
        return True  # Admin override
    
    # ... rest of logic

def can_view_ned_content(user):
    if user.is_admin:
        return True  # Admin override
    
    return user.is_ned_team
```

---

## Permission Management UI

### User Management Interface

```
═══════════════════════════════════════════════════════════
USER MANAGEMENT (Admin Only)
═══════════════════════════════════════════════════════════

[+ Add User]  Search: [_________]

Username    Email           Permissions              Active
──────────────────────────────────────────────────────────
jsmith      john@co.com     Admin, NED, Conf         ✓
jdoe        jane@co.com     NED, Confidential        ✓
slee        sarah@co.com    NED, Confidential        ✓
bwilson     bob@co.com      Confidential             ✓
mjones      mary@co.com     (None)                   ✓

[Click user to edit permissions]
```

### Edit User Permissions

```
┌─────────────────────────────────────────────────────────┐
│ EDIT USER: Jane Doe                                      │
├─────────────────────────────────────────────────────────┤
│ Username:         jdoe                                    │
│ Email:            jane@company.com                        │
│ Full Name:        Jane Doe                                │
│                                                          │
│ PERMISSIONS:                                             │
│                                                          │
│ [✓] Confidential Access (Tier 1)                        │
│     Can view confidential business data (financial       │
│     information, confidential relationships)             │
│                                                          │
│ [✓] NED Team Member (Tier 2)                            │
│     Can view internal CRM/meeting notes and client       │
│     assessments                                          │
│                                                          │
│ [ ] Administrator                                         │
│     Full system access and user management               │
│                                                          │
│ Status: ● Active                                         │
│                                                          │
│ [Save Changes] [Reset Password] [Deactivate User]       │
└─────────────────────────────────────────────────────────┘
```

### Permission Scrubbing Tool

```
═══════════════════════════════════════════════════════════
PERMISSION SCRUBBING TOOL (Admin Only)
═══════════════════════════════════════════════════════════

View: [All Confidential Items ▼]
Entity Type: [All ▼]  Field Type: [All ▼]  Sort: [Date ▼]

Entity      Item Type     Details       Marked By    [Action]
────────────────────────────────────────────────────────────
Project A   Field         CAPEX         john@co.com  [Public]
Project A   Relationship  Constructor   jane@co.com  [Public]
Vendor X    Field         Cost          admin        [Public]
Owner B     Relationship  Vendor Y      john@co.com  [Public]

[Bulk Actions: Select All] [Toggle Selected to Public/Confidential]
```

---

## Security Considerations

### Password Security

- All passwords hashed with bcrypt
- Minimum 8 characters, uppercase, lowercase, number required
- Never expose password_hash in API or UI
- See `19_SECURITY.md` for complete requirements

### Session Security

- Sessions expire after 8 hours inactivity
- Secure session tokens
- CSRF protection on all forms
- See `19_SECURITY.md`

### Permission Escalation Prevention

```python
def update_user_permissions(admin_user, target_user_id, permissions):
    """
    Update user permissions - admin only
    """
    # Verify admin
    if not admin_user.is_admin:
        raise PermissionError("Only admins can modify permissions")
    
    # Prevent self-demotion
    if admin_user.user_id == target_user_id and not permissions.get('is_admin'):
        raise PermissionError("Cannot remove your own admin privileges")
    
    # Update permissions
    target_user = db.query(Users).get(target_user_id)
    target_user.has_confidential_access = permissions.get('has_confidential_access', False)
    target_user.is_ned_team = permissions.get('is_ned_team', False)
    target_user.is_admin = permissions.get('is_admin', False)
    
    db.commit()
    
    # Log permission change
    log_audit_event(admin_user.user_id, 'UPDATE', 'Users', 
                    target_user_id, 'permissions', None, permissions)
```

### Audit All Permission Changes

Every permission change should be logged:

```python
# When marking field as confidential
log_audit_event(user_id, 'CREATE', 'Confidential_Field_Flags', 
                flag_id, None, None, {'table': table_name, 'field': field_name})

# When changing user permissions
log_audit_event(admin_id, 'UPDATE', 'Users', user_id, 
                'has_confidential_access', old_value, new_value)
```

---

## Testing Permission Logic

### Unit Test Examples

```python
def test_field_confidentiality():
    """Test field-level confidentiality"""
    # Setup
    user_no_access = create_test_user(has_confidential_access=False)
    user_with_access = create_test_user(has_confidential_access=True)
    project = create_test_project(capex=50000000)
    mark_field_confidential('Projects', project.id, 'capex')
    
    # Test
    assert not can_view_field(user_no_access, 'Projects', project.id, 'capex')
    assert can_view_field(user_with_access, 'Projects', project.id, 'capex')
    
    # Test display
    assert get_display_value(user_no_access, project, 'capex') == "[Confidential - Access Restricted]"
    assert get_display_value(user_with_access, project, 'capex') == 50000000


def test_ned_team_access():
    """Test NED Team content access"""
    # Setup
    ned_user = create_test_user(is_ned_team=True)
    regular_user = create_test_user(is_ned_team=False)
    owner = create_test_owner(relationship_notes="Strategic priority")
    
    # Test
    assert can_view_ned_content(ned_user)
    assert not can_view_ned_content(regular_user)
    
    # Test retrieval
    history_ned = get_roundtable_history(ned_user, 'Owner', owner.id)
    history_regular = get_roundtable_history(regular_user, 'Owner', owner.id)
    
    assert len(history_ned) > 0
    assert len(history_regular) == 0


def test_relationship_confidentiality():
    """Test relationship confidentiality"""
    # Setup
    user_no_access = create_test_user(has_confidential_access=False)
    user_with_access = create_test_user(has_confidential_access=True)
    rel = create_test_relationship(is_confidential=True)
    
    # Test
    assert not can_view_relationship(user_no_access, rel)
    assert can_view_relationship(user_with_access, rel)
    
    # Test filtering
    all_rels = [rel, create_test_relationship(is_confidential=False)]
    visible_no_access, hidden = get_visible_relationships(user_no_access, all_rels)
    visible_with_access, _ = get_visible_relationships(user_with_access, all_rels)
    
    assert len(visible_no_access) == 1
    assert len(visible_with_access) == 2
    assert hidden == 1
```

---

## Summary

### Permission Matrix

| User Type | Public Data | Confidential Business | NED Team Notes | Admin Functions |
|-----------|-------------|----------------------|----------------|-----------------|
| Regular | ✓ | ✗ | ✗ | ✗ |
| Confidential Access | ✓ | ✓ | ✗ | ✗ |
| NED Team | ✓ | ✗ | ✓ | ✗ |
| NED + Confidential | ✓ | ✓ | ✓ | ✗ |
| Administrator | ✓ | ✓ | ✓ | ✓ |

### Key Principles

1. **Two independent tiers** - Confidential Access and NED Team are separate
2. **Opt-in sensitivity** - Data is public by default, must be explicitly marked
3. **Admin override** - Admins always have full access
4. **Complete hiding** - Confidential relationships completely hidden (not shown as "locked")
5. **User empowerment** - Users who can see data can edit it and change confidentiality

---

**Document End**