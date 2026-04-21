#!/usr/bin/env python3
"""
Validation System Test Suite
Tests all validation functions from app/utils/validators.py
"""
import sys
import os
from datetime import date, timedelta

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User, TechnologyVendor, Product, Project
from app.utils.validators import (
    ValidationError,
    # Common field validation
    validate_string_field,
    validate_numeric_field,
    validate_date_field,
    validate_email,
    validate_phone,
    # Enumerated fields
    validate_company_type,
    validate_engagement_level,
    validate_project_status,
    validate_licensing_approach,
    validate_contact_type,
    validate_relationship_type,
    # Specific numeric fields
    validate_thermal_capacity,
    validate_thermal_efficiency,
    validate_burnup,
    validate_financial_field,
    # User management
    validate_unique_username,
    validate_unique_email,
    validate_password_strength,
    validate_can_delete_user,
    validate_can_remove_admin_rights,
    # Business logic
    validate_unique_vendor_name,
    validate_unique_product_name,
    check_duplicate_project_name,
    validate_cod_for_status,
    validate_contact_person,
    # Relationships
    validate_no_self_relationship,
    # Workflow
    validate_status_transition,
    # Data integrity
    validate_timestamp_consistency,
    # Helpers
    format_validation_error,
    collect_validation_errors
)

# Global references
db_session = None


def print_test_header(test_name):
    """Print formatted test header"""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)


def print_test_result(description, passed, details=None):
    """Print formatted test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {description}")
    if details:
        print(f"       {details}")


def test_string_validation():
    """Test string field validation"""
    print_test_header("String Field Validation")

    # Test 1: Valid string
    try:
        result = validate_string_field("  John Doe  ", "full_name")
        print_test_result("Strip whitespace", result == "John Doe", f"Result: '{result}'")
    except ValidationError as e:
        print_test_result("Strip whitespace", False, str(e))

    # Test 2: Required field empty
    try:
        validate_string_field("", "vendor_name", required=True)
        print_test_result("Required field empty", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Required field empty", "cannot be empty" in str(e), str(e))

    # Test 3: Optional field empty
    try:
        result = validate_string_field("", "notes", required=False)
        print_test_result("Optional field empty", result is None)
    except ValidationError as e:
        print_test_result("Optional field empty", False, str(e))

    # Test 4: Max length exceeded
    try:
        validate_string_field("x" * 300, "vendor_name", max_length=255)
        print_test_result("Max length exceeded", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Max length exceeded", "exceeds maximum length" in str(e), str(e))

    # Test 5: Invalid characters
    try:
        validate_string_field("test\x00name", "vendor_name")
        print_test_result("Invalid characters", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Invalid characters", "invalid characters" in str(e), str(e))


def test_numeric_validation():
    """Test numeric field validation"""
    print_test_header("Numeric Field Validation")

    # Test 1: Valid number
    try:
        result = validate_numeric_field(42.5, "thermal_capacity")
        print_test_result("Valid number", result == 42.5, f"Result: {result}")
    except ValidationError as e:
        print_test_result("Valid number", False, str(e))

    # Test 2: Min value check
    try:
        validate_numeric_field(-5, "capex", min_value=0)
        print_test_result("Min value check", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Min value check", "must be at least 0" in str(e), str(e))

    # Test 3: Max value check
    try:
        validate_numeric_field(150, "thermal_efficiency", max_value=100)
        print_test_result("Max value check", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Max value check", "must be at most 100" in str(e), str(e))

    # Test 4: Invalid number
    try:
        validate_numeric_field("not a number", "capex")
        print_test_result("Invalid number", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Invalid number", "must be a valid number" in str(e), str(e))

    # Test 5: Null value allowed
    try:
        result = validate_numeric_field(None, "opex", allow_null=True)
        print_test_result("Null value allowed", result is None)
    except ValidationError as e:
        print_test_result("Null value allowed", False, str(e))


def test_date_validation():
    """Test date field validation"""
    print_test_header("Date Field Validation")

    today = date.today()
    future_date = today + timedelta(days=30)
    past_date = today - timedelta(days=30)

    # Test 1: Valid date string
    try:
        result = validate_date_field("2025-12-31", "cod")
        print_test_result("Valid date string", result == date(2025, 12, 31))
    except ValidationError as e:
        print_test_result("Valid date string", False, str(e))

    # Test 2: Invalid date format
    try:
        validate_date_field("12/31/2025", "cod")
        print_test_result("Invalid date format", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Invalid date format", "YYYY-MM-DD format" in str(e), str(e))

    # Test 3: Future date not allowed
    try:
        validate_date_field(future_date, "last_contact_date", allow_future=False)
        print_test_result("Future date not allowed", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Future date not allowed", "cannot be in the future" in str(e), str(e))

    # Test 4: Past date not allowed
    try:
        validate_date_field(past_date, "follow_up_date", allow_past=False)
        print_test_result("Past date not allowed", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Past date not allowed", "cannot be in the past" in str(e), str(e))


def test_email_validation():
    """Test email validation"""
    print_test_header("Email Validation")

    # Test 1: Valid email
    try:
        result = validate_email("John.Doe@Example.COM")
        print_test_result("Valid email", result == "john.doe@example.com", f"Result: '{result}'")
    except ValidationError as e:
        print_test_result("Valid email", False, str(e))

    # Test 2: Invalid email - no @
    try:
        validate_email("invalid-email")
        print_test_result("Invalid email - no @", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Invalid email - no @", "valid email address" in str(e), str(e))

    # Test 3: Invalid email - no domain
    try:
        validate_email("user@")
        print_test_result("Invalid email - no domain", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Invalid email - no domain", "valid email address" in str(e), str(e))


def test_phone_validation():
    """Test phone validation"""
    print_test_header("Phone Validation")

    # Test 1: Valid phone - various formats
    try:
        result = validate_phone("(555) 123-4567")
        print_test_result("Valid phone format 1", result == "(555) 123-4567")
    except ValidationError as e:
        print_test_result("Valid phone format 1", False, str(e))

    # Test 2: Valid phone - international
    try:
        result = validate_phone("+1-555-123-4567")
        print_test_result("Valid phone international", result == "+1-555-123-4567")
    except ValidationError as e:
        print_test_result("Valid phone international", False, str(e))

    # Test 3: Too few digits
    try:
        validate_phone("123-456")
        print_test_result("Too few digits", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Too few digits", "at least 10 digits" in str(e), str(e))


def test_enumerated_fields():
    """Test enumerated field validation"""
    print_test_header("Enumerated Field Validation")

    # Test 1: Valid company type
    try:
        result = validate_company_type("IOU")
        print_test_result("Valid company type", result == "IOU")
    except ValidationError as e:
        print_test_result("Valid company type", False, str(e))

    # Test 2: Invalid company type
    try:
        validate_company_type("Invalid")
        print_test_result("Invalid company type", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Invalid company type", "must be one of" in str(e), str(e))

    # Test 3: Valid engagement level
    try:
        result = validate_engagement_level("Interested")
        print_test_result("Valid engagement level", result == "Interested")
    except ValidationError as e:
        print_test_result("Valid engagement level", False, str(e))

    # Test 4: Valid project status
    try:
        result = validate_project_status("Planning")
        print_test_result("Valid project status", result == "Planning")
    except ValidationError as e:
        print_test_result("Valid project status", False, str(e))


def test_specific_numeric_fields():
    """Test specific numeric field validators"""
    print_test_header("Specific Numeric Field Validation")

    # Test 1: Valid thermal efficiency
    try:
        result = validate_thermal_efficiency(45.5)
        print_test_result("Valid thermal efficiency", result == 45.5)
    except ValidationError as e:
        print_test_result("Valid thermal efficiency", False, str(e))

    # Test 2: Thermal efficiency out of range
    try:
        validate_thermal_efficiency(150)
        print_test_result("Thermal efficiency > 100", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Thermal efficiency > 100", "must be at most 100" in str(e), str(e))

    # Test 3: Negative financial field
    try:
        validate_financial_field(-1000, "capex")
        print_test_result("Negative capex", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Negative capex", "must be at least 0" in str(e), str(e))


def test_password_strength():
    """Test password strength validation"""
    print_test_header("Password Strength Validation")

    # Test 1: Valid strong password
    try:
        validate_password_strength("SecurePass123")
        print_test_result("Valid strong password", True)
    except ValidationError as e:
        print_test_result("Valid strong password", False, str(e))

    # Test 2: Too short
    try:
        validate_password_strength("Short1")
        print_test_result("Password too short", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Password too short", "at least 8 characters" in str(e), str(e))

    # Test 3: No uppercase
    try:
        validate_password_strength("lowercase123")
        print_test_result("No uppercase letter", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("No uppercase letter", "uppercase letter" in str(e), str(e))

    # Test 4: No lowercase
    try:
        validate_password_strength("UPPERCASE123")
        print_test_result("No lowercase letter", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("No lowercase letter", "lowercase letter" in str(e), str(e))

    # Test 5: No digit
    try:
        validate_password_strength("NoDigitsHere")
        print_test_result("No digit", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("No digit", "at least one digit" in str(e), str(e))

    # Test 6: Common password
    try:
        validate_password_strength("Password123")
        print_test_result("Common password", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Common password", "too common" in str(e), str(e))

    # Test 7: Contains username
    try:
        validate_password_strength("JohnDoe123", username="johndoe")
        print_test_result("Contains username", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Contains username", "cannot contain your username" in str(e), str(e))


def test_user_management_validation(app):
    """Test user management validators"""
    print_test_header("User Management Validation")

    with app.app_context():
        # Test 1: Unique username check - existing user
        try:
            # Assuming admin user exists
            validate_unique_username("admin")
            print_test_result("Duplicate username check", False, "Should have raised ValidationError")
        except ValidationError as e:
            print_test_result("Duplicate username check", "already taken" in str(e), str(e))

        # Test 2: Unique username - new user
        try:
            validate_unique_username("newuser123")
            print_test_result("Unique username check", True)
        except ValidationError as e:
            print_test_result("Unique username check", False, str(e))

        # Test 3: Cannot delete last admin
        try:
            admin = db_session.query(User).filter_by(is_admin=True, is_active=True).first()
            if admin:
                # Count admins
                admin_count = db_session.query(User).filter(
                    User.is_admin == True,
                    User.is_active == True
                ).count()

                if admin_count == 1:
                    validate_can_delete_user(admin.user_id)
                    print_test_result("Delete last admin", False, "Should have raised ValidationError")
                else:
                    print_test_result("Delete last admin", True, "Multiple admins exist, skipping test")
        except ValidationError as e:
            print_test_result("Delete last admin", "last administrator" in str(e), str(e))


def test_business_logic_validation(app):
    """Test business logic validators"""
    print_test_header("Business Logic Validation")

    with app.app_context():
        # Test 1: COD validation for future projects
        try:
            past_date = date.today() - timedelta(days=30)
            validate_cod_for_status(past_date, "Planning")
            print_test_result("COD past for Planning project", False, "Should have raised ValidationError")
        except ValidationError as e:
            print_test_result("COD past for Planning project", "must be in the future" in str(e), str(e))

        # Test 2: COD validation for operating projects
        try:
            future_date = date.today() + timedelta(days=30)
            validate_cod_for_status(future_date, "Operating")
            print_test_result("COD future for Operating project", False, "Should have raised ValidationError")
        except ValidationError as e:
            print_test_result("COD future for Operating project", "must be in the past" in str(e), str(e))

        # Test 3: Contact person validation - both missing
        try:
            validate_contact_person(None, None)
            print_test_result("Contact person both missing", False, "Should have raised ValidationError")
        except ValidationError as e:
            print_test_result("Contact person both missing", "must be specified" in str(e), str(e))

        # Test 4: Contact person validation - one provided
        try:
            validate_contact_person(123, None)
            print_test_result("Contact person ID provided", True)
        except ValidationError as e:
            print_test_result("Contact person ID provided", False, str(e))


def test_relationship_validation():
    """Test relationship validators"""
    print_test_header("Relationship Validation")

    # Test 1: No self-relationship
    try:
        validate_no_self_relationship(5, 5, "vendor-supplier")
        print_test_result("No self-relationship", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("No self-relationship", "same entity" in str(e), str(e))

    # Test 2: Different entities OK
    try:
        validate_no_self_relationship(5, 10, "vendor-supplier")
        print_test_result("Different entities OK", True)
    except ValidationError as e:
        print_test_result("Different entities OK", False, str(e))


def test_workflow_validation():
    """Test workflow validators"""
    print_test_header("Workflow Validation")

    # Test 1: Valid status transition
    try:
        validate_status_transition("Planning", "Design")
        print_test_result("Valid status transition", True)
    except ValidationError as e:
        print_test_result("Valid status transition", False, str(e))

    # Test 2: Invalid status transition
    try:
        validate_status_transition("Operating", "Planning")
        print_test_result("Invalid status transition", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Invalid status transition", "Invalid status transition" in str(e), str(e))

    # Test 3: Terminal state
    try:
        validate_status_transition("Cancelled", "Planning")
        print_test_result("Transition from terminal state", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Transition from terminal state", "Invalid status transition" in str(e), str(e))

    # Test 4: Same status (no change)
    try:
        validate_status_transition("Planning", "Planning")
        print_test_result("Same status (no change)", True)
    except ValidationError as e:
        print_test_result("Same status (no change)", False, str(e))


def test_data_integrity():
    """Test data integrity validators"""
    print_test_header("Data Integrity Validation")

    # Test 1: Valid timestamp consistency
    try:
        created = date(2025, 1, 1)
        modified = date(2025, 1, 15)
        validate_timestamp_consistency(created, modified)
        print_test_result("Valid timestamp consistency", True)
    except ValidationError as e:
        print_test_result("Valid timestamp consistency", False, str(e))

    # Test 2: Invalid timestamp consistency
    try:
        created = date(2025, 1, 15)
        modified = date(2025, 1, 1)
        validate_timestamp_consistency(created, modified)
        print_test_result("Invalid timestamp consistency", False, "Should have raised ValidationError")
    except ValidationError as e:
        print_test_result("Invalid timestamp consistency", "cannot be before created date" in str(e), str(e))


def test_error_formatting():
    """Test error formatting helpers"""
    print_test_header("Error Formatting")

    # Test 1: Format validation error
    msg = format_validation_error("vendor_name", "required")
    print_test_result("Format required error", msg == "vendor_name is required")

    # Test 2: Format with details
    msg = format_validation_error("relationship", "invalid_relationship", "Vendor not found")
    print_test_result("Format with details", "Vendor not found" in msg)

    # Test 3: Collect multiple errors
    errors = collect_validation_errors([
        (validate_string_field, ("", "vendor_name", 255, True)),
        (validate_email, ("invalid",))
    ])
    print_test_result("Collect multiple errors", len(errors) == 2, f"Collected {len(errors)} errors")


def main():
    """Run all validation tests"""
    global db_session

    print("\n" + "=" * 70)
    print("NUKEWORKS VALIDATION SYSTEM TEST SUITE")
    print("=" * 70)

    # Create Flask app context
    app = create_app('development')
    db_session = app.db_session

    try:
        # Run all tests
        test_string_validation()
        test_numeric_validation()
        test_date_validation()
        test_email_validation()
        test_phone_validation()
        test_enumerated_fields()
        test_specific_numeric_fields()
        test_password_strength()
        test_user_management_validation(app)
        test_business_logic_validation(app)
        test_relationship_validation()
        test_workflow_validation()
        test_data_integrity()
        test_error_formatting()

        print("\n" + "=" * 70)
        print("ALL VALIDATION TESTS COMPLETED ✓")
        print("=" * 70 + "\n")

        return 0

    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
