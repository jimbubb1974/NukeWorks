# 10_UI_VIEWS_ADMIN.md

**Document:** Administration UI Views  
**Version:** 1.0  
**Last Updated:** December 4, 2025  
**Related Documents:** `02_DATABASE_SCHEMA.md`, `05_PERMISSION_SYSTEM.md`, `14_AUDIT_SNAPSHOTS.md`

---

## Table of Contents

1. [Overview](#overview)
2. [Admin Navigation](#admin-navigation)
3. [User Management](#user-management)
4. [Permission Scrubbing Tool](#permission-scrubbing-tool)
5. [System Settings](#system-settings)
6. [Snapshot Management](#snapshot-management)
7. [Audit Log Viewer](#audit-log-viewer)
8. [Schema Information](#schema-information)

---

## 1. Overview

The Administration panel provides system management capabilities for administrators. Only users with `is_admin = TRUE` can access these views.

### Admin Panel Features

- **User Management** - Create, edit, deactivate users
- **Permission Scrubbing** - Review and modify confidentiality flags
- **System Settings** - Configure application behavior
- **Snapshot Management** - Create, restore, and manage backups
- **Audit Log** - Review all data modifications
- **Schema Information** - View database version and migration history

### Access Control

```python
@require_admin
def admin_panel():
    """
    Only administrators can access admin panel
    """
    if not current_user.is_admin:
        flash("Access denied - Administrator privileges required")
        return redirect(url_for('dashboard'))
    
    return render_template('admin/index.html')
```

---

## 2. Admin Navigation

### Main Admin Panel

```
╔══════════════════════════════════════════════════════════╗
ADMINISTRATION
╚══════════════════════════════════════════════════════════╝

[Users] [System Settings] [Snapshots] [Audit Log] [Schema]

Quick Stats:
┌────────────────────────────────────────────────────────┐
│  Total Users: 15          Active: 13      Inactive: 2 │
│  Confidential Items: 47   Last Backup: 2 hours ago    │
│  Database Size: 125 MB    Schema Version: 5           │
└────────────────────────────────────────────────────────┘

Recent Admin Actions:
──────────────────────────────────────────────────────────
Dec 4, 10:35  jsmith   Created user 'mjones'
Dec 4, 09:15  jsmith   Modified system setting 'snapshot_retention_days'
Dec 3, 16:20  admin    Created manual snapshot
```

### Navigation Tabs

```html
<div class="admin-nav">
    <a href="/admin/users" class="active">Users</a>
    <a href="/admin/settings">System Settings</a>
    <a href="/admin/snapshots">Snapshots</a>
    <a href="/admin/audit">Audit Log</a>
    <a href="/admin/schema">Schema</a>
</div>
```

---

## 3. User Management

### 3.1 User List View

```
╔══════════════════════════════════════════════════════════╗
USER MANAGEMENT
╚══════════════════════════════════════════════════════════╝

[+ Add User]  Search: [_________] 🔍  Filter: [All Users ▼]

Username    Full Name       Email           Permissions        Active  Actions
────────────────────────────────────────────────────────────────────────────────
jsmith      John Smith      john@co.com     Admin, NED, Conf   ✓      [Edit] [Deactivate]
jdoe        Jane Doe        jane@co.com     NED, Conf          ✓      [Edit] [Deactivate]
slee        Sarah Lee       sarah@co.com    NED, Conf          ✓      [Edit] [Deactivate]
bwilson     Bob Wilson      bob@co.com      Conf               ✓      [Edit] [Deactivate]
mjones      Mary Jones      mary@co.com     (None)             ✓      [Edit] [Deactivate]
rgarcia     Robert Garcia   rob@co.com      Conf               ✗      [Edit] [Reactivate]

Showing 6 of 15 users  [Previous] [1] [2] [3] [Next]

Permission Legend:
• Admin - Full system access
• NED - NED Team (internal CRM access)
• Conf - Confidential Access (business data)
```

### 3.2 Add/Edit User Form

```
╔══════════════════════════════════════════════════════════╗
ADD NEW USER
╚══════════════════════════════════════════════════════════╝

BASIC INFORMATION
────────────────────────────────────────────────────────────
Full Name:      [___________________________________]
Email:          [___________________________________]
Username:       [___________________________________]

Password:       [___________________________________]
Confirm:        [___________________________________]

Password Requirements:
• Minimum 8 characters
• At least one uppercase letter
• At least one lowercase letter
• At least one digit

PERMISSIONS
────────────────────────────────────────────────────────────
[ ] Administrator
    Full system access including user management

[ ] NED Team Member
    Access to internal CRM notes and roundtable discussions

[ ] Confidential Access
    Access to confidential business data (CAPEX, OPEX, etc.)

Note: Permissions are independent. A user can have any combination.

ACCOUNT STATUS
────────────────────────────────────────────────────────────
[✓] Active
    User can log in and access the system

[Cancel]  [Create User]
```

### 3.3 Edit User Modal

```
┌────────────────────────────────────────────────────────┐
│ EDIT USER: Jane Doe (jdoe)                            │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Full Name:      [Jane Doe]                            │
│ Email:          [jane.doe@company.com]                │
│ Username:       jdoe (cannot be changed)              │
│                                                        │
│ [Change Password]                                      │
│                                                        │
│ PERMISSIONS                                            │
│ ──────────────────────────────────────────────────────│
│ [ ] Administrator                                      │
│ [✓] NED Team Member                                    │
│ [✓] Confidential Access                                │
│                                                        │
│ ACCOUNT STATUS                                         │
│ ──────────────────────────────────────────────────────│
│ Status: ● Active                                       │
│ Created: Mar 15, 2025                                  │
│ Last Login: Dec 4, 2025 at 9:15 AM                    │
│                                                        │
│ [Cancel]  [Save Changes]                              │
└────────────────────────────────────────────────────────┘
```

### 3.4 Change Password Modal

```
┌────────────────────────────────────────────────────────┐
│ CHANGE PASSWORD FOR: jdoe                             │
├────────────────────────────────────────────────────────┤
│                                                        │
│ New Password:       [___________________________]      │
│ Confirm Password:   [___________________________]      │
│                                                        │
│ Password must:                                         │
│ • Be at least 8 characters                             │
│ • Contain uppercase and lowercase letters             │
│ • Contain at least one digit                           │
│                                                        │
│ [Cancel]  [Change Password]                           │
└────────────────────────────────────────────────────────┘
```

### 3.5 Deactivate User Confirmation

```
┌────────────────────────────────────────────────────────┐
│ DEACTIVATE USER                                        │
├────────────────────────────────────────────────────────┤
│ Are you sure you want to deactivate this user?        │
│                                                        │
│ User: Jane Doe (jdoe)                                  │
│                                                        │
│ Effects:                                               │
│ • User will no longer be able to log in                │
│ • User's data and audit history will be preserved     │
│ • User can be reactivated later if needed             │
│                                                        │
│ [Cancel]  [Deactivate]                                │
└────────────────────────────────────────────────────────┘
```

### 3.6 Delete User Warning

```
┌────────────────────────────────────────────────────────┐
│ ⚠️  CANNOT DELETE USER                                  │
├────────────────────────────────────────────────────────┤
│ This user cannot be deleted because:                   │
│                                                        │
│ ❌ User has created 45 entities                         │
│ ❌ User has 23 contact log entries                      │
│ ❌ User is referenced in audit log                      │
│                                                        │
│ Recommendation: Deactivate the user instead of         │
│ deleting. This preserves data integrity while          │
│ preventing future logins.                              │
│                                                        │
│ [Deactivate User Instead]  [Cancel]                   │
└────────────────────────────────────────────────────────┘
```

---

## 4. Permission Scrubbing Tool

### 4.1 Overview Screen

```
╔══════════════════════════════════════════════════════════╗
PERMISSION SCRUBBING TOOL
╚══════════════════════════════════════════════════════════╝

Review and modify confidentiality settings for all data.

SUMMARY
────────────────────────────────────────────────────────────
Total Confidential Items: 47
  • Fields: 32
  • Relationships: 15

By Entity Type:
  • Projects: 18 fields, 5 relationships
  • Owners: 8 fields, 7 relationships
  • Vendors: 6 fields, 3 relationships

[View All Confidential Items]  [Export Report]
```

### 4.2 Confidential Items List

```
╔══════════════════════════════════════════════════════════╗
CONFIDENTIAL ITEMS
╚══════════════════════════════════════════════════════════╝

View: [All Confidential Items ▼]  
Entity Type: [All ▼]  Item Type: [All ▼]
Sort: [Date Marked ▼]  Search: [_________]

Entity          Type          Item                Marked By      Date       Action
──────────────────────────────────────────────────────────────────────────────────
Project Alpha   Field         capex               jsmith         Dec 1      [Make Public] [Details]
Project Alpha   Field         opex                jsmith         Dec 1      [Make Public] [Details]
Project Alpha   Relationship  → Constructor D     jdoe           Nov 28     [Make Public] [Details]
Vendor X        Field         supplier_cost       admin          Nov 15     [Make Public] [Details]
Owner A         Relationship  → Vendor B          jsmith         Nov 10     [Make Public] [Details]

[Select All Visible]  [Bulk Actions ▼]

Showing 1-5 of 47  [Previous] [Next]

Bulk Actions:
• Make Selected Public
• Export Selected
• Generate Report
```

### 4.3 Item Detail Modal

```
┌────────────────────────────────────────────────────────┐
│ CONFIDENTIAL ITEM DETAILS                              │
├────────────────────────────────────────────────────────┤
│ Entity:    Project Alpha (ID: 45)                      │
│ Type:      Field                                        │
│ Field:     capex                                        │
│ Value:     $50,000,000                                  │
│                                                        │
│ CONFIDENTIALITY STATUS                                 │
│ ──────────────────────────────────────────────────────│
│ Status:      🔒 Confidential                            │
│ Marked By:   John Smith (jsmith)                       │
│ Marked Date: December 1, 2025                          │
│                                                        │
│ ACCESS                                                 │
│ ──────────────────────────────────────────────────────│
│ Users with access: 8 of 15 users                       │
│ • Administrators: 2 users                              │
│ • Confidential Access: 6 users                         │
│                                                        │
│ ACTIONS                                                │
│ ──────────────────────────────────────────────────────│
│ [Make Public]  [View Access Log]  [Close]            │
└────────────────────────────────────────────────────────┘
```

### 4.4 Make Public Confirmation

```
┌────────────────────────────────────────────────────────┐
│ MAKE PUBLIC                                            │
├────────────────────────────────────────────────────────┤
│ Are you sure you want to make this item public?       │
│                                                        │
│ Entity:    Project Alpha                               │
│ Field:     capex ($50,000,000)                         │
│                                                        │
│ Effects:                                               │
│ • All users will be able to view this information      │
│ • Change will be logged in audit trail                 │
│ • Cannot be easily undone (would need to mark again)   │
│                                                        │
│ [Cancel]  [Make Public]                               │
└────────────────────────────────────────────────────────┘
```

### 4.5 Bulk Action Confirmation

```
┌────────────────────────────────────────────────────────┐
│ BULK MAKE PUBLIC                                       │
├────────────────────────────────────────────────────────┤
│ You are about to make 12 items public:                │
│                                                        │
│ • 8 fields                                             │
│ • 4 relationships                                      │
│                                                        │
│ Affected entities:                                     │
│ • Project Alpha (3 items)                              │
│ • Project Beta (2 items)                               │
│ • Vendor X (5 items)                                   │
│ • Owner A (2 items)                                    │
│                                                        │
│ This action will:                                      │
│ • Make all selected items visible to all users         │
│ • Log changes in audit trail                           │
│ • Cannot be easily undone                              │
│                                                        │
│ [Cancel]  [Continue]                                  │
└────────────────────────────────────────────────────────┘
```

---

## 5. System Settings

### 5.1 Settings Overview

```
╔══════════════════════════════════════════════════════════╗
SYSTEM SETTINGS
╚══════════════════════════════════════════════════════════╝

[Company] [Backups] [CRM] [Reports] [Advanced]

COMPANY INFORMATION
────────────────────────────────────────────────────────────
Company Name:       [MPR Associates]

Company Logo:       [current_logo.png]  [Change] [Remove]
                    Preview: [Logo image shown]

[Save Changes]

AUTOMATED BACKUPS
────────────────────────────────────────────────────────────
[✓] Enable automated snapshots

Daily Snapshot Time:    [02:00] (24-hour format, server time)

Retention Period:       [30] days
                        Automated snapshots older than this are deleted

Maximum Snapshots:      [10]
                        Keep at most this many automated snapshots

[Save Changes]

CRM SETTINGS
────────────────────────────────────────────────────────────
Roundtable History:     Keep last [3 ▼] meetings per entity
                        Older meetings are automatically removed

[Save Changes]

REPORT SETTINGS
────────────────────────────────────────────────────────────
[✓] Add "CONFIDENTIAL" watermark to PDF reports

Watermark Text:         [CONFIDENTIAL]

Watermark Position:     [Diagonal ▼]
                        Options: Diagonal, Header, Footer

[Save Changes]
```

### 5.2 Company Settings Tab

```
╔══════════════════════════════════════════════════════════╗
SYSTEM SETTINGS - COMPANY
╚══════════════════════════════════════════════════════════╝

COMPANY INFORMATION
────────────────────────────────────────────────────────────
Company Name:       [MPR Associates, Inc.]
                    Appears on reports and application header

COMPANY LOGO
────────────────────────────────────────────────────────────
Current Logo:       [logo.png uploaded on Mar 15, 2025]

Preview:
┌────────────────┐
│                │
│  [LOGO IMAGE]  │
│                │
└────────────────┘

[Upload New Logo]  [Remove Logo]

Logo Requirements:
• Recommended size: 200x80 pixels
• Formats: PNG, JPG, SVG
• Max file size: 2 MB
• Transparent background recommended

[Cancel]  [Save Changes]
```

### 5.3 Backup Settings Tab

```
╔══════════════════════════════════════════════════════════╗
SYSTEM SETTINGS - AUTOMATED BACKUPS
╚══════════════════════════════════════════════════════════╝

AUTOMATED SNAPSHOT CONFIGURATION
────────────────────────────────────────────────────────────
Status:  [✓] Enabled    [ ] Disabled

SCHEDULE
────────────────────────────────────────────────────────────
Daily Snapshot Time:    [02:00]
                        24-hour format (HH:MM)
                        Time is based on server time

Next Scheduled Run:     Tomorrow at 2:00 AM

RETENTION POLICY
────────────────────────────────────────────────────────────
Retention Period:       [30] days
                        Automated snapshots older than this will
                        be automatically deleted

Maximum Snapshots:      [10]
                        Maximum number of automated snapshots to keep
                        Oldest snapshots deleted when limit reached

Note: Manual snapshots and snapshots marked as "important" 
are never automatically deleted.

CURRENT STATUS
────────────────────────────────────────────────────────────
Last Automated Snapshot:    Today at 2:00 AM (2 hours ago)
Status:                     ✓ Success
File Size:                  125 MB

Total Automated Snapshots:  7
Total Manual Snapshots:     3
Total Disk Usage:           1.2 GB

[View All Snapshots]

[Cancel]  [Save Changes]
```

### 5.4 Advanced Settings Tab

```
╔══════════════════════════════════════════════════════════╗
SYSTEM SETTINGS -