# 04_DATA_DICTIONARY.md - Field Definitions & Validation

**Document Version:** 1.0  
**Last Updated:** December 4, 2025

**Related Documents:**
- `02_DATABASE_SCHEMA.md` - Table structures
- `03_DATABASE_RELATIONSHIPS.md` - Relationships
- `06_BUSINESS_RULES.md` - Business logic

---

## Overview

This document defines enumerations, validation rules, and field constraints for NukeWorks data.

---

## Table of Contents

1. [Enumerations](#enumerations)
2. [Validation Rules](#validation-rules)
3. [Field Constraints](#field-constraints)
4. [Data Formats](#data-formats)

---

## Enumerations

### Project Status

**Valid Values:**
- `Planning` - Initial planning phase
- `Design` - Design development underway
- `Licensing` - Regulatory review and licensing
- `Construction` - Under construction
- `Commissioning` - Testing and commissioning
- `Operating` - In commercial operation
- `Decommissioned` - Shut down and decommissioned

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Licensing Approach

**Valid Values:**
- `Research Reactor` - Research reactor license
- `Part 50` - 10 CFR Part 50 licensing
- `Part 52` - 10 CFR Part 52 licensing (Design Certification, ESP, COL)

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Company Type (Owners/Developers)

**Valid Values:**
- `IOU` - Investor-Owned Utility
- `COOP` - Cooperative Utility
- `Public Power` - Publicly-owned utility
- `IPP` - Independent Power Producer

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Engagement Level (Owners/Developers)

**Valid Values:**
- `Intrigued` - Initial interest, exploring options
- `Interested` - Actively investigating
- `Invested` - Committed resources, contracts signed
- `Inservice` - Operational deployment

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Contact Type

**Valid Values:**
- `In-person` - Face-to-face meeting
- `Phone` - Phone call
- `Email` - Email correspondence
- `Video` - Video conference
- `Conference` - Industry conference or event

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Relationship Type (Owner-Vendor)

**Valid Values:**
- `MOU` - Memorandum of Understanding (no money exchanged)
- `Development_Agreement` - Development agreement (with money)
- `Delivery_Contract` - Delivery contract (procurement orders/major commitment)

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Relationship Strength (NED Team)

**Valid Values:**
- `Strong` - Excellent relationship, high trust
- `Good` - Solid relationship
- `Needs Attention` - Requires improvement or more engagement
- `At Risk` - Relationship deteriorating
- `New` - Newly established relationship

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Client Priority (NED Team)

**Valid Values:**
- `High` - High priority client
- `Medium` - Medium priority
- `Low` - Low priority
- `Strategic` - Strategic importance (highest)
- `Opportunistic` - Opportunistic engagement

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Client Status (NED Team)

**Valid Values:**
- `Active` - Actively engaged
- `Warm` - Maintaining relationship
- `Cold` - Minimal engagement
- `Prospective` - Potential future client

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Personnel Type

**Valid Values:**
- `Internal` - Your firm's employees
- `Client_Contact` - Contact at client organization
- `Vendor_Contact` - Contact at vendor organization
- `Constructor_Contact` - Contact at construction company
- `Operator_Contact` - Contact at operating company

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Reactor Type

**Common Values (not exhaustive):**
- `PWR` - Pressurized Water Reactor
- `BWR` - Boiling Water Reactor
- `SMR` - Small Modular Reactor (generic)
- `Micro` - Microreactor
- `HTGR` - High-Temperature Gas-Cooled Reactor
- `MSR` - Molten Salt Reactor
- `SFR` - Sodium-Cooled Fast Reactor

**Database Storage:** TEXT (free text)  
**UI Display:** Text input with autocomplete suggestions

### Design Status

**Valid Values:**
- `Conceptual` - Conceptual design phase
- `Preliminary` - Preliminary design
- `Detailed` - Detailed design complete
- `Licensed` - NRC licensed
- `Operating` - In commercial operation
- `Cancelled` - Project cancelled

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Firm Involvement

**Valid Values:**
- `Lead Consultant` - Primary consulting role
- `Supporting Role` - Supporting consultant
- `Monitoring` - Monitoring project developments
- `Not Involved` - Not currently involved

**Database Storage:** TEXT  
**UI Display:** Dropdown select

### Project Health

**Valid Values:**
- `On Track` - Proceeding as planned
- `Delayed` - Behind schedule
- `At Risk` - Significant challenges
- `Stalled` - Progress halted
- `Cancelled` - Project cancelled

**Database Storage:** TEXT  
**UI Display:** Dropdown select

---

## Validation Rules

### Text Fields

**Project Name, Vendor Name, Company Name:**
- **Required:** Yes
- **Min Length:** 2 characters
- **Max Length:** 200 characters
- **Pattern:** Alphanumeric, spaces, hyphens, apostrophes allowed
- **Validation:** `^[A-Za-z0-9\s\-']+$`

**Email:**
- **Required:** Depends on field
- **Format:** Valid email format
- **Max Length:** 254 characters
- **Pattern:** `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`

**Phone:**
- **Required:** No
- **Format:** Flexible (international formats supported)
- **Pattern:** `^[\d\s\-\+\(\)]+$`
- **Examples:** `123-456-7890`, `+1 (123) 456-7890`

**Notes Fields:**
- **Required:** No
- **Max Length:** No hard limit (TEXT field)
- **Format:** Free text, allows line breaks

**MPR Project ID:**
- **Required:** No
- **Format:** Free text
- **Suggested Pattern:** `MPR-YYYY-NNN` (e.g., `MPR-2024-001`)

### Numeric Fields

**Financial Fields (CAPEX, OPEX, Fuel Cost, LCOE):**
- **Type:** REAL (floating point)
- **Required:** No
- **Min Value:** 0 (must be non-negative)
- **Max Value:** 999999999999 (1 trillion)
- **Validation:** `value >= 0`

**Thermal Capacity:**
- **Type:** REAL
- **Required:** No
- **Min Value:** 0.1 MWth
- **Max Value:** 10000 MWth
- **Unit:** Megawatts thermal (MWth)

**Thermal Efficiency:**
- **Type:** REAL
- **Required:** No
- **Min Value:** 0
- **Max Value:** 100
- **Unit:** Percentage
- **Validation:** `0 <= value <= 100`

**Burnup:**
- **Type:** REAL
- **Required:** No
- **Min Value:** 0
- **Max Value:** 200
- **Unit:** GWd/MTU (Gigawatt-days per metric ton uranium)

### Date Fields

**General Date Fields:**
- **Format:** ISO 8601 (YYYY-MM-DD)
- **Required:** Depends on field
- **Validation:** Must be valid date

**Contact Date:**
- **Validation:** Cannot be in the future
- **Rule:** `contact_date <= today()`

**Commercial Operation Date (COD):**
- **Validation:** Should be future date (if project not operational)
- **Rule:** For non-operating projects: `cod >= today()`

**Follow-up Date:**
- **Validation:** Should be future date
- **Rule:** `follow_up_date >= today()`

### Boolean Fields

**is_confidential:**
- **Values:** 0 (false), 1 (true)
- **Default:** 0 (public)
- **Validation:** Must be 0 or 1

**is_active:**
- **Values:** 0 (inactive), 1 (active)
- **Default:** 1 (active)
- **Validation:** Must be 0 or 1

**follow_up_needed:**
- **Values:** 0 (no), 1 (yes)
- **Default:** 0
- **Validation:** Must be 0 or 1
- **Business Rule:** If true, follow_up_date and follow_up_assigned_to should be populated

**has_confidential_access, is_ned_team, is_admin:**
- **Values:** 0 (no), 1 (yes)
- **Default:** 0
- **Validation:** Must be 0 or 1
- **Business Rule:** Cannot modify own admin status

---

## Field Constraints

### Required Field Combinations

**Contact Log Entry:**
```
Required Fields:
- entity_type
- entity_id
- contact_date
- contact_type
- contacted_by
- summary

Conditional Requirements:
- If follow_up_needed = 1:
  - follow_up_date (required)
  - follow_up_assigned_to (required)
```

**Roundtable History:**
```
Required Fields:
- entity_type
- entity_id
- meeting_date
- discussion
- action_items

Access Control:
- Only accessible if user.is_ned_team = 1 or user.is_admin = 1
```

**Personnel (Internal):**
```
If personnel_type = 'Internal':
- organization_id must be NULL
- organization_type must be NULL

If personnel_type != 'Internal':
- organization_id should be populated (recommended)
- organization_type should be populated (recommended)
```

### Unique Constraints

**Users:**
- `username` must be unique
- `email` must be unique

**Combination Uniqueness:**
- `Confidential_Field_Flags(table_name, record_id, field_name)` must be unique
- Junction tables: Each relationship combination should be unique
  - Example: `Project_Vendor_Relationships(project_id, vendor_id)` unique

### Foreign Key Constraints

**All created_by and modified_by fields:**
- Must reference valid `Users.user_id`
- Can be NULL (system-generated entries)

**POC Fields (Owners_Developers):**
- `primary_poc` must reference `Personnel` where `personnel_type = 'Internal'`
- `secondary_poc` must reference `Personnel` where `personnel_type = 'Internal'`
- Can be NULL

**Entity References:**
- All foreign keys must reference existing records
- Cascading behavior: Typically prevent deletion if references exist

---

## Data Formats

### Display Formats

**Currency:**
```
Database: REAL (50000000)
Display:  $50,000,000
Format:   ${value:,.0f}
```

**Percentages:**
```
Database: REAL (35.5)
Display:  35.5%
Format:   {value:.1f}%
```

**Dates:**
```
Database: DATE (2025-12-04)
Display:  December 4, 2025
Format:   %B %d, %Y

Short:    Dec 4, 2025
Format:   %b %d, %Y

ISO:      2025-12-04
Format:   %Y-%m-%d
```

**Date/Time:**
```
Database: TIMESTAMP (2025-12-04 14:30:22)
Display:  December 4, 2025 2:30 PM
Format:   %B %d, %Y %I:%M %p

Short:    12/04/2025 14:30
Format:   %m/%d/%Y %H:%M
```

**Large Numbers:**
```
Capacity: 200 MWth
LCOE:     $85.50/MWh
Burnup:   60 GWd/MTU
```

### Input Formats

**Currency Input:**
```
Accept:
- 50000000
- 50,000,000
- $50,000,000

Store as: 50000000 (REAL, no formatting)
```

**Date Input:**
```
HTML Input Type: date
Format: YYYY-MM-DD
Browser provides calendar picker
```

**Phone Input:**
```
Accept any format:
- 1234567890
- 123-456-7890
- (123) 456-7890
- +1 (123) 456-7890

Store as entered (TEXT)
```

### Export Formats

**CSV Export:**
```
- Dates: ISO 8601 (YYYY-MM-DD)
- Numbers: No formatting (raw values)
- Text: Quoted if contains comma
- Booleans: 1/0 or TRUE/FALSE
```

**Excel Export:**
```
- Dates: Excel date format
- Numbers: Formatted with appropriate decimals
- Currency: Currency format
- Text: Plain text
- Booleans: TRUE/FALSE
```

**PDF Export:**
```
- Dates: Long format (December 4, 2025)
- Numbers: Formatted with commas
- Currency: $50,000,000 format
- Text: Wrapped and formatted
```

---

## Validation Implementation

### Python Validation Functions

```python
# utils/validators.py

import re
from datetime import datetime, date

def validate_email(email):
    """Validate email format"""
    if not email:
        return True  # Optional field
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone format"""
    if not phone:
        return True  # Optional field
    
    pattern = r'^[\d\s\-\+\(\)]+
    return re.match(pattern, phone) is not None

def validate_project_name(name):
    """Validate project/vendor/company name"""
    if not name:
        return False, "Name is required"
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 200:
        return False, "Name must not exceed 200 characters"
    
    pattern = r'^[A-Za-z0-9\s\-\']+
    if not re.match(pattern, name):
        return False, "Name contains invalid characters"
    
    return True, None

def validate_positive_number(value, field_name):
    """Validate positive numeric field"""
    if value is None:
        return True, None  # Optional
    
    try:
        num = float(value)
        if num < 0:
            return False, f"{field_name} must be non-negative"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"

def validate_percentage(value, field_name):
    """Validate percentage field (0-100)"""
    if value is None:
        return True, None
    
    try:
        num = float(value)
        if num < 0 or num > 100:
            return False, f"{field_name} must be between 0 and 100"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"

def validate_date_not_future(date_value, field_name):
    """Validate date is not in the future"""
    if date_value is None:
        return True, None
    
    if isinstance(date_value, str):
        date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
    
    if date_value > date.today():
        return False, f"{field_name} cannot be in the future"
    
    return True, None

def validate_date_not_past(date_value, field_name):
    """Validate date is not in the past"""
    if date_value is None:
        return True, None
    
    if isinstance(date_value, str):
        date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
    
    if date_value < date.today():
        return False, f"{field_name} cannot be in the past"
    
    return True, None

def validate_enum(value, valid_values, field_name):
    """Validate enumeration value"""
    if value is None:
        return True, None  # Optional
    
    if value not in valid_values:
        return False, f"{field_name} must be one of: {', '.join(valid_values)}"
    
    return True, None
```

### JavaScript Client-Side Validation

```javascript
// static/js/validators.js

function validateEmail(email) {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return pattern.test(email);
}

function validatePhone(phone) {
    const pattern = /^[\d\s\-\+\(\)]+$/;
    return pattern.test(phone);
}

function validateRequired(value, fieldName) {
    if (!value || value.trim() === '') {
        return { valid: false, message: `${fieldName} is required` };
    }
    return { valid: true };
}

function validatePositiveNumber(value, fieldName) {
    const num = parseFloat(value);
    if (isNaN(num)) {
        return { valid: false, message: `${fieldName} must be a number` };
    }
    if (num < 0) {
        return { valid: false, message: `${fieldName} must be non-negative` };
    }
    return { valid: true };
}

function validateDateNotFuture(dateStr, fieldName) {
    const date = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (date > today) {
        return { valid: false, message: `${fieldName} cannot be in the future` };
    }
    return { valid: true };
}

// Form validation on submit
document.querySelector('.entity-form').addEventListener('submit', function(e) {
    let errors = [];
    
    // Validate required fields
    this.querySelectorAll('[required]').forEach(field => {
        const result = validateRequired(field.value, field.labels[0].textContent);
        if (!result.valid) {
            errors.push(result.message);
            field.classList.add('error');
        }
    });
    
    // Validate numeric fields
    this.querySelectorAll('input[type="number"]').forEach(field => {
        if (field.value) {
            const result = validatePositiveNumber(field.value, field.labels[0].textContent);
            if (!result.valid) {
                errors.push(result.message);
                field.classList.add('error');
            }
        }
    });
    
    // Validate contact date (not future)
    const contactDate = this.querySelector('#contact_date');
    if (contactDate && contactDate.value) {
        const result = validateDateNotFuture(contactDate.value, 'Contact Date');
        if (!result.valid) {
            errors.push(result.message);
            contactDate.classList.add('error');
        }
    }
    
    // If errors, prevent submission
    if (errors.length > 0) {
        e.preventDefault();
        alert('Please fix the following errors:\n\n' + errors.join('\n'));
    }
});
```

---

## Business Rules Summary

### Critical Validation Rules

1. **Financial fields** must be non-negative
2. **Contact dates** cannot be in the future
3. **Follow-up dates** should be in the future
4. **Email addresses** must be valid format
5. **Required fields** must be populated before save
6. **Enumeration values** must match defined lists
7. **Foreign keys** must reference existing records
8. **Unique constraints** must be enforced
9. **Personnel type** determines organization field requirements
10. **Follow-up** flag requires follow-up date and assignee

### Data Quality Guidelines

**Names:**
- Use proper capitalization
- Avoid abbreviations unless standard
- Be consistent with naming conventions

**Dates:**
- Use ISO 8601 format (YYYY-MM-DD) in database
- Display in user-friendly format
- Validate realistic date ranges

**Financial Data:**
- Store as numbers without formatting
- Format for display with currency symbols and commas
- Use appropriate precision (dollars, not cents)

**Notes:**
- Encourage descriptive notes
- Include relevant context
- Update notes when circumstances change

---

## Enumeration Usage Examples

### Python/Flask

```python
# Constants
PROJECT_STATUS_CHOICES = [
    'Planning', 'Design', 'Licensing', 
    'Construction', 'Commissioning', 'Operating', 'Decommissioned'
]

COMPANY_TYPE_CHOICES = ['IOU', 'COOP', 'Public Power', 'IPP']

ENGAGEMENT_LEVEL_CHOICES = ['Intrigued', 'Interested', 'Invested', 'Inservice']

# In form
from wtforms import SelectField

class ProjectForm(FlaskForm):
    project_status = SelectField(
        'Project Status',
        choices=[(s, s) for s in PROJECT_STATUS_CHOICES]
    )
```

### HTML Template

```html
<select name="project_status" required>
    <option value="">Select status...</option>
    <option value="Planning" {% if project.project_status == 'Planning' %}selected{% endif %}>Planning</option>
    <option value="Design" {% if project.project_status == 'Design' %}selected{% endif %}>Design</option>
    <option value="Licensing" {% if project.project_status == 'Licensing' %}selected{% endif %}>Licensing</option>
    <option value="Construction" {% if project.project_status == 'Construction' %}selected{% endif %}>Construction</option>
    <option value="Commissioning" {% if project.project_status == 'Commissioning' %}selected{% endif %}>Commissioning</option>
    <option value="Operating" {% if project.project_status == 'Operating' %}selected{% endif %}>Operating</option>
    <option value="Decommissioned" {% if project.project_status == 'Decommissioned' %}selected{% endif %}>Decommissioned</option>
</select>
```

---

## Reference Tables

### Quick Reference: Field Types

| Field Type | Database Type | Python Type | Validation |
|------------|---------------|-------------|------------|
| Project Name | TEXT | str | 2-200 chars, alphanumeric |
| Email | TEXT | str | Valid email format |
| Phone | TEXT | str | Numeric + formatting chars |
| CAPEX | REAL | float | >= 0 |
| Efficiency | REAL | float | 0-100 |
| Status | TEXT | str | Must match enum |
| Date | DATE | date | Valid date format |
| Timestamp | TIMESTAMP | datetime | Auto-generated |
| Confidential | BOOLEAN | bool | 0 or 1 |

### Quick Reference: Required vs Optional

**Always Required:**
- Entity names (project_name, vendor_name, company_name)
- Contact log: entity_type, entity_id, contact_date, contact_type, contacted_by, summary
- Roundtable: entity_type, entity_id, meeting_date, discussion, action_items
- Users: username, email, password_hash

**Optional but Recommended:**
- Notes fields
- Financial data (CAPEX, OPEX, etc.)
- Technical specifications
- Contact details (email, phone)

**Conditional:**
- Follow-up fields (required if follow_up_needed = true)
- Organization fields for personnel (required if external)

---

## Summary

This data dictionary ensures:
- ✅ **Consistent data entry** across all users
- ✅ **Valid data** through validation rules
- ✅ **Clear expectations** for each field
- ✅ **Proper formatting** for display and export
- ✅ **Business rule enforcement** at application level

### Implementation Checklist

- [ ] Implement validation functions (Python)
- [ ] Add client-side validation (JavaScript)
- [ ] Create dropdown lists for enumerations
- [ ] Add validation error messages to forms
- [ ] Test all validation rules
- [ ] Document custom validation for users

---

**Document End**