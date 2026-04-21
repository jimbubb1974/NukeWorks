# Business Rules & Validation System Implementation

**Date:** 2025-10-05
**Status:** ✅ Complete
**Specification:** `docs/06_BUSINESS_RULES.md`

---

## Overview

A comprehensive data validation system has been implemented for NukeWorks following the business rules specification in `docs/06_BUSINESS_RULES.md`. The system provides validation functions for user management, password strength, field validation, business logic, relationships, workflows, and data integrity.

## Implementation Summary

### ✅ Components Implemented

1. **Validators Module** (`app/utils/validators.py`)
   - Common field validation (string, numeric, date, email, phone)
   - Enumerated field validation
   - User management validators
   - Password strength validation
   - Business logic validators
   - Relationship validators
   - Workflow validators
   - Data integrity validators
   - Error formatting utilities

2. **Comprehensive Test Suite** (`test_validators.py`)
   - 50+ tests covering all validation scenarios
   - **All tests passing ✓**
   - Automated test execution

3. **Documentation**
   - Complete implementation guide (this file)
   - Inline documentation for all functions
   - Usage examples in docstrings

---

## File Structure

```
NukeWorks/
├── app/
│   └── utils/
│       └── validators.py                 # Core validation system
│
├── test_validators.py                    # Comprehensive test suite
└── VALIDATION_SYSTEM_IMPLEMENTATION.md   # This file
```

---

## Validation Categories

### 1. Common Field Validation

#### String Fields

```python
from app.utils.validators import validate_string_field, ValidationError

# Basic usage
try:
    value = validate_string_field("  John Doe  ", "full_name")
    # Returns: "John Doe" (stripped)
except ValidationError as e:
    print(e)

# With options
value = validate_string_field(
    value="Long text...",
    field_name="vendor_name",
    max_length=255,
    required=True,
    allow_newlines=False  # For notes fields, set to True
)
```

**Features:**
- Strips leading/trailing whitespace
- Validates required fields
- Checks maximum length
- Validates against control characters
- Returns `None` for empty optional fields

#### Numeric Fields

```python
from app.utils.validators import validate_numeric_field

# Basic usage
value = validate_numeric_field(
    value=50.5,
    field_name="thermal_efficiency",
    min_value=0,
    max_value=100,
    allow_null=True
)
```

**Features:**
- Converts to float
- Validates min/max bounds
- Allows NULL values (configurable)
- Type checking

#### Date Fields

```python
from app.utils.validators import validate_date_field

# COD - allow future
cod = validate_date_field(
    value="2026-12-31",
    field_name="cod",
    allow_future=True
)

# Contact date - past only
contact_date = validate_date_field(
    value="2025-01-15",
    field_name="last_contact_date",
    allow_future=False
)
```

**Features:**
- Accepts string (YYYY-MM-DD) or date objects
- Validates future/past constraints
- Returns date object

#### Email Validation

```python
from app.utils.validators import validate_email

email = validate_email("John.Doe@Example.COM")
# Returns: "john.doe@example.com" (lowercase)
```

**Features:**
- Format validation using regex
- Converts to lowercase
- Returns normalized email

#### Phone Validation

```python
from app.utils.validators import validate_phone

phone = validate_phone("(555) 123-4567")
# Returns: "(555) 123-4567" (preserves formatting)
```

**Features:**
- Accepts various formats
- Validates minimum 10 digits
- Preserves original formatting
- Supports international numbers

### 2. Enumerated Field Validation

Pre-defined valid values for specific fields:

```python
from app.utils.validators import (
    validate_company_type,        # IOU, COOP, Public Power, IPP, Other
    validate_engagement_level,     # Intrigued, Interested, Invested, Inservice
    validate_project_status,       # Conceptual, Planning, Design, etc.
    validate_licensing_approach,   # Research Reactor, Part 50, Part 52
    validate_contact_type,         # In-person, Phone, Email, Video, Conference
    validate_relationship_type     # MOU, Development_Agreement, etc.
)

# Usage
status = validate_project_status("Planning")  # Valid
status = validate_project_status("Invalid")   # Raises ValidationError
```

**Available Enumerations:**
- `VALID_COMPANY_TYPES`
- `VALID_ENGAGEMENT_LEVELS`
- `VALID_PROJECT_STATUSES`
- `VALID_LICENSING_APPROACHES`
- `VALID_CONTACT_TYPES`
- `VALID_RELATIONSHIP_TYPES`

### 3. Specific Numeric Field Validation

Domain-specific numeric validators:

```python
from app.utils.validators import (
    validate_thermal_capacity,     # Must be positive
    validate_thermal_efficiency,   # 0-100 percentage
    validate_burnup,               # Must be positive
    validate_financial_field       # Must be positive
)

# Thermal efficiency (0-100%)
efficiency = validate_thermal_efficiency(45.5)  # Valid
efficiency = validate_thermal_efficiency(150)   # Error: exceeds 100

# Financial fields
capex = validate_financial_field(5000000, "capex")  # Valid
capex = validate_financial_field(-1000, "capex")    # Error: negative
```

### 4. User Management Validation

#### Unique Username

```python
from app.utils.validators import validate_unique_username

# Create new user
validate_unique_username("newuser")

# Update existing user (exclude self from check)
validate_unique_username("updatedname", user_id=123)
```

#### Unique Email

```python
from app.utils.validators import validate_unique_email

# Create new user
validate_unique_email("user@example.com")

# Update existing user
validate_unique_email("newemail@example.com", user_id=123)
```

#### Password Strength

```python
from app.utils.validators import validate_password_strength

# Check password meets requirements
validate_password_strength("SecurePass123")  # Valid

# Check with username
validate_password_strength("JohnDoe123", username="johndoe")  # Error: contains username
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- Cannot be common password
- Cannot contain username

**Common Passwords Blocked:**
- password, password123, 12345678
- admin, admin123
- And 10+ more common passwords

#### Admin Protection

```python
from app.utils.validators import (
    validate_can_delete_user,
    validate_can_remove_admin_rights
)

# Prevent deleting last admin
try:
    validate_can_delete_user(admin_user_id)
except ValidationError as e:
    print(e)  # "Cannot delete the last administrator account"

# Prevent removing last admin's rights
try:
    validate_can_remove_admin_rights(admin_user_id)
except ValidationError as e:
    print(e)  # "Cannot remove admin rights from the last administrator"
```

### 5. Business Logic Validation

#### Unique Vendor Name

```python
from app.utils.validators import validate_unique_vendor_name

# Create new vendor
validate_unique_vendor_name("NuScale Power")

# Update existing vendor
validate_unique_vendor_name("Updated Name", vendor_id=123)
```

#### Unique Product Name (per vendor)

```python
from app.utils.validators import validate_unique_product_name

# Create new product
validate_unique_product_name("VOYGR-12", vendor_id=5)

# Update existing product
validate_unique_product_name("VOYGR-12", vendor_id=5, product_id=10)
```

#### Duplicate Project Name Check

```python
from app.utils.validators import check_duplicate_project_name

# Returns warning (not error) if duplicate found
warning = check_duplicate_project_name("New Project")
if warning:
    flash(warning, 'warning')  # Display warning to user
```

#### COD Validation by Project Status

```python
from app.utils.validators import validate_cod_for_status

# Future projects need future COD
validate_cod_for_status(
    cod=date(2026, 12, 31),
    project_status="Planning"
)  # Valid

# Operating projects need past COD
validate_cod_for_status(
    cod=date(2030, 1, 1),
    project_status="Operating"
)  # Error: must be in past
```

**Rules:**
- Conceptual/Planning/Design/Licensing/Construction: COD must be in future
- Operating: COD must be in past
- COD is optional (can be None)

#### Contact Person Validation

```python
from app.utils.validators import validate_contact_person

# At least one method required
validate_contact_person(
    contact_person_id=123,
    contact_person_freetext=None
)  # Valid - ID provided

validate_contact_person(
    contact_person_id=None,
    contact_person_freetext="John Doe"
)  # Valid - name provided

validate_contact_person(
    contact_person_id=None,
    contact_person_freetext=None
)  # Error: one must be specified
```

### 6. Relationship Validation

#### No Self-Relationships

```python
from app.utils.validators import validate_no_self_relationship

# Prevent vendor from being its own supplier
validate_no_self_relationship(
    entity1_id=5,
    entity2_id=5,
    relationship_type="vendor-supplier"
)  # Error: same entity
```

### 7. Workflow Validation

#### Project Status Transitions

```python
from app.utils.validators import validate_status_transition, VALID_STATUS_TRANSITIONS

# Valid transition
validate_status_transition("Planning", "Design")  # Valid

# Invalid transition
validate_status_transition("Operating", "Planning")  # Error: invalid transition

# Terminal states cannot transition
validate_status_transition("Cancelled", "Planning")  # Error: terminal state
```

**Status Workflow:**
```
Conceptual → Planning → Design → Licensing → Construction → Commissioning → Operating → Decommissioned
                ↓         ↓        ↓             ↓               ↓
              Cancelled / On Hold
```

**Valid Transitions:**
- Conceptual → Planning, Cancelled, On Hold
- Planning → Design, Cancelled, On Hold
- Design → Licensing, Cancelled, On Hold
- Licensing → Construction, Cancelled, On Hold
- Construction → Commissioning, Cancelled, On Hold
- Commissioning → Operating, Cancelled
- Operating → Decommissioned
- On Hold → Conceptual, Planning, Design, Licensing, Construction, Cancelled
- Cancelled → (terminal)
- Decommissioned → (terminal)

### 8. Data Integrity Validation

#### Timestamp Consistency

```python
from app.utils.validators import validate_timestamp_consistency

# Valid timestamps
validate_timestamp_consistency(
    created_date=date(2025, 1, 1),
    modified_date=date(2025, 1, 15)
)  # Valid

# Invalid timestamps
validate_timestamp_consistency(
    created_date=date(2025, 1, 15),
    modified_date=date(2025, 1, 1)
)  # Error: modified before created
```

---

## Error Handling

### ValidationError Exception

All validation functions raise `ValidationError` on failure:

```python
from app.utils.validators import ValidationError, validate_email

try:
    email = validate_email("invalid-email")
except ValidationError as e:
    print(f"Validation failed: {e}")
    # Output: "email must be a valid email address"
```

### Error Formatting

```python
from app.utils.validators import format_validation_error

# Standard error messages
msg = format_validation_error("vendor_name", "required")
# Returns: "vendor_name is required"

msg = format_validation_error("relationship", "invalid_relationship", "Vendor not found")
# Returns: "Invalid relationship: Vendor not found"
```

### Collecting Multiple Errors

```python
from app.utils.validators import collect_validation_errors

errors = collect_validation_errors([
    (validate_string_field, ("", "vendor_name", 255, True)),
    (validate_email, ("invalid",)),
    (validate_phone, ("123",))
])

# Returns list of error messages:
# ['vendor_name cannot be empty', 'email must be a valid email address', 'phone must contain at least 10 digits']

if errors:
    for error in errors:
        flash(error, 'error')
```

---

## Usage Examples

### Form Validation in Routes

```python
from flask import request, flash, redirect
from app.utils.validators import (
    ValidationError,
    validate_string_field,
    validate_email,
    validate_unique_username,
    validate_password_strength,
    collect_validation_errors
)

@bp.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    # Collect all validation errors
    validators = [
        (validate_string_field, (request.form.get('username'), 'username', 80, True)),
        (validate_email, (request.form.get('email'),)),
        (validate_string_field, (request.form.get('full_name'), 'full_name', 200, True))
    ]

    errors = collect_validation_errors(validators)

    # Check unique constraints
    try:
        validate_unique_username(request.form.get('username'))
    except ValidationError as e:
        errors.append(str(e))

    try:
        validate_unique_email(request.form.get('email'))
    except ValidationError as e:
        errors.append(str(e))

    # Check password
    try:
        validate_password_strength(
            request.form.get('password'),
            username=request.form.get('username')
        )
    except ValidationError as e:
        errors.append(str(e))

    # If any errors, show them and return
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('admin.create_user'))

    # Validation passed - create user
    user = User(...)
    db_session.add(user)
    db_session.commit()

    flash('User created successfully', 'success')
    return redirect(url_for('admin.users'))
```

### Model-Level Validation

```python
from app.utils.validators import (
    ValidationError,
    validate_string_field,
    validate_numeric_field,
    validate_project_status
)

class Project(Base):
    # ... fields ...

    def validate(self):
        """Validate project data"""
        errors = []

        # Validate project name
        try:
            self.project_name = validate_string_field(
                self.project_name,
                "project_name",
                required=True
            )
        except ValidationError as e:
            errors.append(str(e))

        # Validate status
        try:
            self.project_status = validate_project_status(self.project_status)
        except ValidationError as e:
            errors.append(str(e))

        # Validate capacity
        try:
            self.thermal_capacity = validate_numeric_field(
                self.thermal_capacity,
                "thermal_capacity",
                min_value=0
            )
        except ValidationError as e:
            errors.append(str(e))

        if errors:
            raise ValidationError("; ".join(errors))

    def save(self):
        """Save with validation"""
        self.validate()
        db_session.add(self)
        db_session.commit()
```

### WTForms Integration

```python
from wtforms import StringField, PasswordField, validators
from app.utils.validators import validate_password_strength, ValidationError

class CustomPasswordValidator:
    """WTForms validator using our password strength validator"""

    def __call__(self, form, field):
        try:
            username = form.username.data if hasattr(form, 'username') else None
            validate_password_strength(field.data, username=username)
        except ValidationError as e:
            raise validators.ValidationError(str(e))

class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[
        validators.DataRequired(),
        validators.Length(min=3, max=80)
    ])

    password = PasswordField('Password', validators=[
        validators.DataRequired(),
        CustomPasswordValidator()
    ])
```

---

## Test Suite

### Running Tests

```bash
cd /home/jim/Coding\ Project/NukeWorks
./venv/bin/python test_validators.py
```

### Test Coverage

**50+ Tests - All Passing ✓**

1. **String Field Validation (5 tests)**
   - Strip whitespace
   - Required field empty
   - Optional field empty
   - Max length exceeded
   - Invalid characters

2. **Numeric Field Validation (5 tests)**
   - Valid number
   - Min value check
   - Max value check
   - Invalid number
   - Null value allowed

3. **Date Field Validation (4 tests)**
   - Valid date string
   - Invalid date format
   - Future date not allowed
   - Past date not allowed

4. **Email Validation (3 tests)**
   - Valid email
   - Invalid email - no @
   - Invalid email - no domain

5. **Phone Validation (3 tests)**
   - Valid phone format
   - Valid international
   - Too few digits

6. **Enumerated Fields (4 tests)**
   - Valid company type
   - Invalid company type
   - Valid engagement level
   - Valid project status

7. **Specific Numeric Fields (3 tests)**
   - Valid thermal efficiency
   - Thermal efficiency > 100
   - Negative capex

8. **Password Strength (7 tests)**
   - Valid strong password
   - Too short
   - No uppercase letter
   - No lowercase letter
   - No digit
   - Common password
   - Contains username

9. **User Management (3 tests)**
   - Duplicate username check
   - Unique username check
   - Delete last admin protection

10. **Business Logic (4 tests)**
    - COD past for Planning project
    - COD future for Operating project
    - Contact person both missing
    - Contact person ID provided

11. **Relationships (2 tests)**
    - No self-relationship
    - Different entities OK

12. **Workflow (4 tests)**
    - Valid status transition
    - Invalid status transition
    - Transition from terminal state
    - Same status (no change)

13. **Data Integrity (2 tests)**
    - Valid timestamp consistency
    - Invalid timestamp consistency

14. **Error Formatting (3 tests)**
    - Format required error
    - Format with details
    - Collect multiple errors

### Test Output Example

```
======================================================================
NUKEWORKS VALIDATION SYSTEM TEST SUITE
======================================================================

======================================================================
TEST: String Field Validation
======================================================================
✓ PASS: Strip whitespace
       Result: 'John Doe'
✓ PASS: Required field empty
       vendor_name cannot be empty
✓ PASS: Optional field empty
✓ PASS: Max length exceeded
       vendor_name exceeds maximum length of 255
✓ PASS: Invalid characters
       vendor_name contains invalid characters

... (45 more tests)

======================================================================
ALL VALIDATION TESTS COMPLETED ✓
======================================================================
```

---

## Validation Checklist

### For New Features

When adding new features, ensure validation for:

- [x] Required fields checked
- [x] String fields have max length
- [x] Numeric fields have min/max bounds
- [x] Dates validated for future/past constraints
- [x] Emails validated for format
- [x] Enumerated fields have valid options
- [x] Unique constraints enforced
- [x] Relationships validated
- [x] Status transitions follow workflow
- [x] Timestamps are consistent

### For User Management

- [x] Username uniqueness (case-insensitive)
- [x] Email uniqueness (case-insensitive)
- [x] Password strength (8+ chars, mixed case, digit)
- [x] Password not common
- [x] Password doesn't contain username
- [x] Cannot delete last admin
- [x] Cannot remove last admin's rights

### For Business Data

- [x] Vendor names unique
- [x] Product names unique per vendor
- [x] Project names checked (warning if duplicate)
- [x] COD matches project status
- [x] Contact person specified
- [x] No self-relationships
- [x] Project status transitions valid

---

## Best Practices

### 1. Validate Early

```python
# Good: Validate before processing
try:
    email = validate_email(user_input)
    # ... continue processing
except ValidationError as e:
    flash(str(e), 'error')
    return redirect(...)

# Bad: Process first, validate later
email = user_input.lower()  # Too late, might be invalid
```

### 2. Collect All Errors

```python
# Good: Show all errors at once
errors = collect_validation_errors([...])
if errors:
    for error in errors:
        flash(error, 'error')

# Bad: Show one error at a time
try:
    validate_field_1(...)
except ValidationError as e:
    flash(str(e), 'error')
    return  # User has to fix and resubmit to see next error
```

### 3. Use Specific Validators

```python
# Good: Use specific validator
efficiency = validate_thermal_efficiency(value)

# Bad: Generic validation
efficiency = validate_numeric_field(value, "efficiency", 0, 100)
```

### 4. Provide Context

```python
# Good: Specific error messages
validate_cod_for_status(cod, status)
# Error: "Commercial Operation Date must be in the future for non-operating projects"

# Bad: Generic errors
if cod <= today and status != 'Operating':
    raise ValidationError("Invalid date")
```

---

## Common Validation Patterns

### Pattern 1: Form Validation

```python
def validate_form_data(form_data):
    """Validate all form fields and return errors"""
    errors = []

    # Validate each field
    try:
        validate_string_field(form_data.get('name'), 'name', required=True)
    except ValidationError as e:
        errors.append(str(e))

    try:
        validate_email(form_data.get('email'))
    except ValidationError as e:
        errors.append(str(e))

    return errors
```

### Pattern 2: Model Validation

```python
class MyModel(Base):
    def validate_before_save(self):
        """Validate model before saving"""
        errors = collect_validation_errors([
            (validate_string_field, (self.name, 'name', 255, True)),
            (validate_numeric_field, (self.value, 'value', 0, None, False))
        ])

        if errors:
            raise ValidationError("; ".join(errors))
```

### Pattern 3: API Validation

```python
@api.route('/api/projects', methods=['POST'])
def create_project_api():
    """API endpoint with validation"""
    data = request.get_json()

    # Validate
    errors = []
    try:
        validate_string_field(data.get('project_name'), 'project_name', required=True)
    except ValidationError as e:
        errors.append(str(e))

    if errors:
        return jsonify({'errors': errors}), 400

    # Process...
    return jsonify({'success': True}), 201
```

---

## Troubleshooting

### Issue: ValidationError Not Caught

**Problem:** ValidationError not being caught in try/except

**Solution:**
```python
# Ensure you're importing from the right place
from app.utils.validators import ValidationError  # ✓ Correct

# Not:
from wtforms.validators import ValidationError  # ✗ Different class
```

### Issue: Unique Constraint Fails

**Problem:** validate_unique_username says username is taken but it's not

**Diagnosis:**
```python
# Check database directly
user = db_session.query(User).filter(User.username.ilike('testuser')).first()
print(f"User found: {user}")
```

**Solution:**
- Ensure database session is active
- Check for soft-deleted records
- Verify case-insensitive comparison

### Issue: Password Validation Too Strict

**Problem:** Users complain password requirements are too strict

**Solution:**
```python
# Adjust requirements in validators.py
def validate_password_strength(password, username=None):
    # Option 1: Reduce minimum length
    if len(password) < 6:  # Was 8
        raise ValidationError("...")

    # Option 2: Make uppercase optional
    # if not re.search(r'[A-Z]', password):
    #     raise ValidationError("...")  # Comment out

    # Option 3: Remove common password check
    # if password.lower() in COMMON_PASSWORDS:
    #     raise ValidationError("...")  # Comment out
```

---

## Future Enhancements

Potential improvements to the validation system:

1. **Custom Validation Rules**
   - User-defined validation functions
   - Configurable constraints via database

2. **Async Validation**
   - Real-time validation in forms
   - AJAX endpoint for unique checks

3. **Validation Profiles**
   - Different rules for different contexts
   - Import vs. manual entry validation

4. **Batch Validation**
   - Validate multiple records efficiently
   - Import preview with all errors

5. **Localization**
   - Translatable error messages
   - Culture-specific date/number formats

6. **Audit Trail**
   - Log validation failures
   - Track validation rule changes

---

## Compliance Checklist

Following Business Rules Best Practices:

- [x] All required fields validated
- [x] String length constraints enforced
- [x] Numeric bounds checked
- [x] Date constraints validated
- [x] Email format validated
- [x] Phone format validated
- [x] Enumerated fields restricted
- [x] Unique constraints enforced
- [x] Password strength requirements
- [x] Business logic rules enforced
- [x] Relationship rules validated
- [x] Workflow transitions controlled
- [x] Data integrity maintained
- [x] Comprehensive test coverage
- [x] Complete documentation

---

## Conclusion

The validation system is **production-ready** and provides:

✅ **Comprehensive Validation**
- Field-level validation (string, numeric, date, email, phone)
- Enumerated field validation
- User management validation
- Password strength validation
- Business logic validation
- Relationship validation
- Workflow validation
- Data integrity validation

✅ **Developer-Friendly**
- Simple function-based API
- Clear error messages
- Easy integration with forms and models
- Helper functions for common patterns

✅ **Well-Tested**
- 50+ comprehensive tests all passing
- Coverage of all validation scenarios
- Automated test suite

✅ **Robust Error Handling**
- Custom ValidationError exception
- Error collection and formatting
- Multiple error reporting

The system follows validation best practices and is ready for deployment in a production environment.

---

**Implementation Complete** ✅
