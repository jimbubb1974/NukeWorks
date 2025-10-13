"""
Business Rules & Data Validation for NukeWorks
Implements validation functions from docs/06_BUSINESS_RULES.md
"""
import re
from datetime import date, datetime
from flask import current_app


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


# =============================================================================
# COMMON FIELD VALIDATION
# =============================================================================

def validate_string_field(value, field_name, max_length=255, required=True, allow_newlines=False):
    """
    Standard string field validation

    Args:
        value: String value to validate
        field_name: Name of field for error messages
        max_length: Maximum allowed length
        required: Whether field is required
        allow_newlines: Whether to allow newline characters (for text areas)

    Returns:
        Cleaned string value or None

    Raises:
        ValidationError: If validation fails

    Examples:
        >>> validate_string_field("  John Doe  ", "full_name")
        'John Doe'
        >>> validate_string_field("", "vendor_name", required=True)
        ValidationError: vendor_name cannot be empty
    """
    if value is None:
        if required:
            raise ValidationError(f"{field_name} is required")
        return None

    # Strip leading/trailing whitespace
    value = value.strip()

    if required and len(value) == 0:
        raise ValidationError(f"{field_name} cannot be empty")

    # If optional and empty, return None
    if not required and len(value) == 0:
        return None

    if len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length}")

    # Check for invalid control characters
    if allow_newlines:
        invalid_chars = [c for c in value if ord(c) < 32 and c not in ['\n', '\r', '\t']]
    else:
        invalid_chars = [c for c in value if ord(c) < 32]

    if invalid_chars:
        raise ValidationError(f"{field_name} contains invalid characters")

    return value


def validate_numeric_field(value, field_name, min_value=None, max_value=None, allow_null=True):
    """
    Numeric field validation

    Args:
        value: Numeric value to validate
        field_name: Name of field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        allow_null: Whether None is allowed

    Returns:
        Float value or None

    Raises:
        ValidationError: If validation fails

    Examples:
        >>> validate_numeric_field(50.5, "thermal_efficiency", min_value=0, max_value=100)
        50.5
        >>> validate_numeric_field(-5, "capex", min_value=0)
        ValidationError: capex must be at least 0
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


def validate_date_field(value, field_name, allow_future=True, allow_past=True):
    """
    Date field validation

    Args:
        value: Date string or date object to validate
        field_name: Name of field for error messages
        allow_future: Whether future dates are allowed
        allow_past: Whether past dates are allowed

    Returns:
        Date object or None

    Raises:
        ValidationError: If validation fails

    Examples:
        >>> validate_date_field("2025-12-31", "cod", allow_future=True)
        date(2025, 12, 31)
        >>> validate_date_field("2030-01-01", "last_contact_date", allow_future=False)
        ValidationError: last_contact_date cannot be in the future
    """
    if value is None:
        return None

    # Convert string to date if needed
    if isinstance(value, str):
        try:
            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(f"{field_name} must be in YYYY-MM-DD format")
    elif isinstance(value, date):
        date_obj = value
    else:
        raise ValidationError(f"{field_name} must be a valid date")

    today = date.today()

    if not allow_future and date_obj > today:
        raise ValidationError(f"{field_name} cannot be in the future")

    if not allow_past and date_obj < today:
        raise ValidationError(f"{field_name} cannot be in the past")

    return date_obj


def validate_email(email, field_name="email"):
    """
    Email validation

    Args:
        email: Email address to validate
        field_name: Name of field for error messages

    Returns:
        Lowercase email string or None

    Raises:
        ValidationError: If email format is invalid

    Examples:
        >>> validate_email("John.Doe@Example.COM")
        'john.doe@example.com'
        >>> validate_email("invalid-email")
        ValidationError: email must be a valid email address
    """
    if email is None:
        return None

    email = email.strip().lower()

    # Basic email regex pattern
    pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'

    if not re.match(pattern, email):
        raise ValidationError(f"{field_name} must be a valid email address")

    return email


def validate_phone(phone, field_name="phone"):
    """
    Phone validation

    Args:
        phone: Phone number to validate
        field_name: Name of field for error messages

    Returns:
        Phone string (preserves formatting) or None

    Raises:
        ValidationError: If phone has too few digits

    Examples:
        >>> validate_phone("(555) 123-4567")
        '(555) 123-4567'
        >>> validate_phone("123")
        ValidationError: phone must contain at least 10 digits
    """
    if phone is None:
        return None

    phone = phone.strip()

    # Extract digits for validation
    digits = re.sub(r'[^0-9+]', '', phone)

    if len(digits) < 10:
        raise ValidationError(f"{field_name} must contain at least 10 digits")

    return phone  # Store as entered (preserves formatting)


# =============================================================================
# ENUMERATED FIELD VALIDATION
# =============================================================================

VALID_COMPANY_TYPES = ['IOU', 'COOP', 'Public Power', 'IPP', 'Other']
VALID_ENGAGEMENT_LEVELS = ['Intrigued', 'Interested', 'Invested', 'Inservice']
VALID_PROJECT_STATUSES = ['Conceptual', 'Planning', 'Design', 'Licensing',
                          'Construction', 'Commissioning', 'Operating',
                          'Decommissioned', 'Cancelled', 'On Hold']
VALID_LICENSING_APPROACHES = ['Research Reactor', 'Part 50', 'Part 52']
VALID_CONTACT_TYPES = ['In-person', 'Phone', 'Email', 'Video', 'Conference']
VALID_RELATIONSHIP_TYPES = ['MOU', 'Development_Agreement', 'Delivery_Contract', 'Other']


def validate_contact_date(contact_date):
    """Validate contact_date cannot be in the future"""
    if contact_date is None:
        raise ValidationError("contact_date is required")

    contact_date = validate_date_field(contact_date, 'contact_date', allow_future=False)
    return contact_date


def validate_contact_person(contact_person_id, contact_person_freetext):
    """Validate that at least one method of identifying contact person is provided"""
    if contact_person_id in (None, 0) and (not contact_person_freetext or contact_person_freetext.strip() == ''):
        raise ValidationError("Contact person must be specified (select from list or enter a name)")

    if contact_person_freetext:
        validate_string_field(contact_person_freetext, 'contact_person_freetext', max_length=255, required=False)

    return contact_person_id if contact_person_id not in (None, 0) else None


def validate_follow_up_date(follow_up_date):
    """Validate follow_up_date is in the future"""
    if follow_up_date is None:
        return None

    follow_up_date = validate_date_field(follow_up_date, 'follow_up_date', allow_future=True, allow_past=False)

    if follow_up_date <= date.today():
        raise ValidationError("follow_up_date should be in the future")

    return follow_up_date


def validate_meeting_date(meeting_date):
    """Validate roundtable meeting_date cannot be in the future"""
    if meeting_date is None:
        raise ValidationError("meeting_date is required")

    meeting_date = validate_date_field(meeting_date, 'meeting_date', allow_future=False)
    return meeting_date


def validate_company_type(value):
    """Validate company_type field"""
    if value is None:
        return None
    if value not in VALID_COMPANY_TYPES:
        raise ValidationError(f"company_type must be one of: {', '.join(VALID_COMPANY_TYPES)}")
    return value


def validate_engagement_level(value):
    """Validate engagement_level field"""
    if value is None:
        return None
    if value not in VALID_ENGAGEMENT_LEVELS:
        raise ValidationError(f"engagement_level must be one of: {', '.join(VALID_ENGAGEMENT_LEVELS)}")
    return value


def validate_project_status(value):
    """Validate project_status field"""
    if value is None:
        return None
    if value not in VALID_PROJECT_STATUSES:
        raise ValidationError(f"project_status must be one of: {', '.join(VALID_PROJECT_STATUSES)}")
    return value


def validate_licensing_approach(value):
    """Validate licensing_approach field"""
    if value is None:
        return None
    if value not in VALID_LICENSING_APPROACHES:
        raise ValidationError(f"licensing_approach must be one of: {', '.join(VALID_LICENSING_APPROACHES)}")
    return value


def validate_contact_type(value):
    """Validate contact_type field"""
    if value is None:
        return None
    if value not in VALID_CONTACT_TYPES:
        raise ValidationError(f"contact_type must be one of: {', '.join(VALID_CONTACT_TYPES)}")
    return value


def validate_relationship_type(value):
    """Validate relationship_type field"""
    if value is None:
        return None
    if value not in VALID_RELATIONSHIP_TYPES:
        raise ValidationError(f"relationship_type must be one of: {', '.join(VALID_RELATIONSHIP_TYPES)}")
    return value


# =============================================================================
# SPECIFIC NUMERIC FIELD VALIDATION
# =============================================================================

def validate_thermal_capacity(value):
    """Validate thermal_capacity - must be positive"""
    return validate_numeric_field(value, "thermal_capacity", min_value=0, allow_null=True)


def validate_thermal_efficiency(value):
    """Validate thermal_efficiency - percentage (0-100)"""
    return validate_numeric_field(value, "thermal_efficiency", min_value=0, max_value=100, allow_null=True)


def validate_burnup(value):
    """Validate burnup - must be positive"""
    return validate_numeric_field(value, "burnup", min_value=0, allow_null=True)


def validate_financial_field(value, field_name):
    """Validate financial fields (capex, opex, fuel_cost, lcoe) - must be positive"""
    return validate_numeric_field(value, field_name, min_value=0, allow_null=True)


# =============================================================================
# USER MANAGEMENT VALIDATION
# =============================================================================

def validate_unique_username(username, user_id=None):
    """
    Validate username is unique (case-insensitive)

    Args:
        username: Username to check
        user_id: User ID to exclude from check (for updates)

    Raises:
        ValidationError: If username already exists
    """
    from app import db_session
    from app.models import User

    if not db_session:
        db_session = current_app.db_session

    query = db_session.query(User).filter(User.username.ilike(username))

    if user_id is not None:
        query = query.filter(User.user_id != user_id)

    existing = query.first()

    if existing:
        raise ValidationError(f"Username '{username}' is already taken")


def validate_unique_email(email, user_id=None):
    """
    Validate email is unique (case-insensitive)

    Args:
        email: Email to check
        user_id: User ID to exclude from check (for updates)

    Raises:
        ValidationError: If email already exists
    """
    from app import db_session
    from app.models import User

    if not db_session:
        db_session = current_app.db_session

    query = db_session.query(User).filter(User.email.ilike(email))

    if user_id is not None:
        query = query.filter(User.user_id != user_id)

    existing = query.first()

    if existing:
        raise ValidationError(f"Email '{email}' is already registered")


# Common weak passwords list (subset - expand as needed)
# Store in lowercase for case-insensitive comparison
COMMON_PASSWORDS = {
    'password', 'password123', '12345678', 'qwerty', 'abc123',
    'password1', 'admin', 'admin123', 'letmein', 'welcome',
    'monkey', '1234567890', 'password!', 'pa$$w0rd', 'p@ssw0rd',
    'Password123'  # Add mixed case version
}


def validate_password_strength(password, username=None):
    """
    Validate password meets minimum security requirements

    Args:
        password: Password to validate
        username: Optional username to check against

    Raises:
        ValidationError: If password doesn't meet requirements

    Rules:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - Cannot be common password
        - Cannot contain username (if provided)

    Examples:
        >>> validate_password_strength("SecurePass123")
        True
        >>> validate_password_strength("weak")
        ValidationError: Password must be at least 8 characters long
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")

    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit")

    # Check against common passwords
    if password.lower() in COMMON_PASSWORDS:
        raise ValidationError("Password is too common. Please choose a stronger password")

    # Check if password contains username
    if username and username.lower() in password.lower():
        raise ValidationError("Password cannot contain your username")

    return True


def validate_can_delete_user(user_id):
    """
    Validate user can be deleted (prevent deletion of last admin)

    Args:
        user_id: ID of user to delete

    Raises:
        ValidationError: If user is last admin
    """
    from app import db_session
    from app.models import User

    if not db_session:
        db_session = current_app.db_session

    user = db_session.query(User).get(user_id)

    if user and user.is_admin:
        admin_count = db_session.query(User).filter(
            User.is_admin == True,
            User.is_active == True
        ).count()

        if admin_count <= 1:
            raise ValidationError("Cannot delete the last administrator account")


def validate_can_remove_admin_rights(user_id):
    """
    Validate admin rights can be removed (prevent removing last admin)

    Args:
        user_id: ID of user whose admin rights are being removed

    Raises:
        ValidationError: If user is last admin
    """
    from app import db_session
    from app.models import User

    if not db_session:
        db_session = current_app.db_session

    admin_count = db_session.query(User).filter(
        User.is_admin == True,
        User.is_active == True
    ).count()

    if admin_count <= 1:
        raise ValidationError("Cannot remove admin rights from the last administrator")


# =============================================================================
# BUSINESS LOGIC VALIDATION
# =============================================================================

def validate_unique_vendor_name(vendor_name, vendor_id=None):
    """
    DEPRECATED: Legacy TechnologyVendor model removed in Phase 4.
    Use validate_unique_company_name instead.

    Validate vendor name is unique

    Args:
        vendor_name: Vendor name to check
        vendor_id: Vendor ID to exclude from check (for updates)

    Raises:
        ValidationError: If vendor name already exists
    """
    # Legacy function - vendors are now companies with vendor role
    # Redirect to company name validation
    return validate_unique_company_name(vendor_name, vendor_id)


def validate_unique_product_name(product_name, vendor_id, product_id=None):
    """
    DEPRECATED: Legacy Product model removed in Phase 4.
    Technology/product data is now stored in Company model.

    Validate product name is unique within a vendor

    Args:
        product_name: Product name to check
        vendor_id: Vendor ID (legacy, ignored)
        product_id: Product ID to exclude from check (for updates)

    Raises:
        ValidationError: Always raises - function is deprecated
    """
    raise ValidationError("Product validation is deprecated. Technology data is now part of Company model.")


def validate_unique_company_name(company_name, company_id=None):
    """
    Validate company name is unique

    Args:
        company_name: Company name to check
        company_id: Company ID to exclude from check (for updates)

    Raises:
        ValidationError: If company name already exists
    """
    from app import db_session
    from app.models import Company

    if not db_session:
        db_session = current_app.db_session

    query = db_session.query(Company).filter(
        Company.company_name.ilike(company_name)
    )

    if company_id is not None:
        query = query.filter(Company.company_id != company_id)

    existing = query.first()

    if existing:
        raise ValidationError(f"Company '{company_name}' already exists")


def check_duplicate_project_name(project_name, project_id=None):
    """
    Check for duplicate project names (returns warning, not error)

    Args:
        project_name: Project name to check
        project_id: Project ID to exclude from check (for updates)

    Returns:
        Warning message if duplicate found, None otherwise
    """
    from app import db_session
    from app.models import Project

    if not db_session:
        db_session = current_app.db_session

    query = db_session.query(Project).filter(Project.project_name.ilike(project_name))

    if project_id is not None:
        query = query.filter(Project.project_id != project_id)

    existing = query.first()

    if existing:
        return f"Warning: A project named '{project_name}' already exists"

    return None


def validate_cod_for_status(cod, project_status):
    """
    Validate COD (Commercial Operation Date) based on project status

    Args:
        cod: Commercial Operation Date
        project_status: Current project status

    Raises:
        ValidationError: If COD doesn't match project status
    """
    if cod is None:
        return  # COD is optional

    today = date.today()

    # Future projects should have future COD
    if project_status in ['Conceptual', 'Planning', 'Design', 'Licensing', 'Construction']:
        if cod <= today:
            raise ValidationError("Commercial Operation Date must be in the future for non-operating projects")

    # Operating projects should have past COD
    elif project_status == 'Operating':
        if cod > today:
            raise ValidationError("Commercial Operation Date must be in the past for operating projects")


def validate_contact_person(contact_person_id, contact_person_freetext):
    """
    Validate at least one method of identifying contact person is provided

    Args:
        contact_person_id: ID of contact person from personnel
        contact_person_freetext: Free-text name of contact person

    Raises:
        ValidationError: If neither is provided
    """
    if contact_person_id is None and (contact_person_freetext is None or contact_person_freetext.strip() == ''):
        raise ValidationError("Contact person must be specified (select from list or enter name)")


# =============================================================================
# RELATIONSHIP VALIDATION
# =============================================================================

def validate_no_self_relationship(entity1_id, entity2_id, relationship_type=""):
    """
    Prevent entity from having relationship with itself

    Args:
        entity1_id: First entity ID
        entity2_id: Second entity ID
        relationship_type: Type of relationship for error message

    Raises:
        ValidationError: If IDs are the same
    """
    if entity1_id == entity2_id:
        raise ValidationError(f"Cannot create {relationship_type} relationship with the same entity")


# =============================================================================
# WORKFLOW VALIDATION
# =============================================================================

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

    Args:
        current_status: Current project status
        new_status: Desired new status

    Raises:
        ValidationError: If transition is not allowed

    Examples:
        >>> validate_status_transition('Planning', 'Design')
        True
        >>> validate_status_transition('Operating', 'Planning')
        ValidationError: Invalid status transition from Operating to Planning
    """
    if current_status == new_status:
        return True  # No change

    allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])

    if new_status not in allowed_transitions:
        raise ValidationError(f"Invalid status transition from {current_status} to {new_status}")

    return True


# =============================================================================
# DATA INTEGRITY VALIDATION
# =============================================================================

def validate_timestamp_consistency(created_date, modified_date):
    """
    Validate modified_date is not before created_date

    Args:
        created_date: Date record was created
        modified_date: Date record was modified

    Raises:
        ValidationError: If modified is before created
    """
    if created_date and modified_date:
        if modified_date < created_date:
            raise ValidationError("Modified date cannot be before created date")


# =============================================================================
# ERROR FORMATTING
# =============================================================================

def format_validation_error(field_name, error_type, details=None):
    """
    Consistent error message formatting

    Args:
        field_name: Name of field with error
        error_type: Type of error
        details: Additional error details

    Returns:
        Formatted error message string
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


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def collect_validation_errors(validators):
    """
    Run multiple validators and collect all errors

    Args:
        validators: List of (validator_func, args) tuples

    Returns:
        List of validation error messages

    Example:
        >>> errors = collect_validation_errors([
        ...     (validate_string_field, ("", "vendor_name")),
        ...     (validate_email, ("invalid",))
        ... ])
        >>> print(errors)
        ['vendor_name cannot be empty', 'email must be a valid email address']
    """
    errors = []

    for validator_func, args in validators:
        try:
            validator_func(*args)
        except ValidationError as e:
            errors.append(str(e))

    return errors


def validate_all_or_none(errors):
    """
    Raise ValidationError with all collected errors or return success

    Args:
        errors: List of error messages

    Raises:
        ValidationError: With combined error messages if any errors exist
    """
    if errors:
        raise ValidationError("; ".join(errors))
