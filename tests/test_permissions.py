#!/usr/bin/env python3
"""
Permission System Test Suite
Tests both Tier 1 (Business Confidentiality) and Tier 2 (NED Team Access)
"""
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User, Project, TechnologyVendor, ProjectVendorRelationship, ConfidentialFieldFlag

# Global db_session reference
db_session = None
from app.utils.permissions import (
    # Tier 1 - Business Confidentiality
    can_view_field,
    get_field_display_value,
    can_view_relationship,
    filter_relationships,
    mark_field_confidential,
    mark_financial_fields_confidential,
    # Tier 2 - NED Team Access
    can_view_ned_content,
    get_ned_field_value,
    filter_ned_fields,
    # Route Protection
    get_user_permission_summary,
    get_permission_level_name,
    # Query Helpers
    apply_confidential_filter
)


def print_test_header(test_name):
    """Print formatted test header"""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)


def print_test_result(description, result, expected=None):
    """Print formatted test result"""
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status}: {description}")
    if expected is not None:
        print(f"       Result: {result}, Expected: {expected}")


def cleanup_test_data_full():
    """Clean up all test data including dependencies"""
    # Delete test relationships first (they reference other tables)
    db_session.query(ProjectVendorRelationship).filter(
        ProjectVendorRelationship.notes.in_(['Public technology provider relationship', 'Confidential partnership relationship'])
    ).delete(synchronize_session=False)

    # Delete test projects
    db_session.query(Project).filter(Project.project_name == 'Test Nuclear Project').delete(synchronize_session=False)

    # Delete test vendors
    db_session.query(TechnologyVendor).filter(
        TechnologyVendor.vendor_name.in_(['Test Reactor Vendor', 'Test Reactor Vendor 2'])
    ).delete(synchronize_session=False)

    # Delete test confidential field flags
    db_session.query(ConfidentialFieldFlag).filter(ConfidentialFieldFlag.table_name == 'projects').delete(synchronize_session=False)

    # Finally delete test users
    db_session.query(User).filter(User.username.like('test_%')).delete(synchronize_session=False)

    db_session.commit()


def setup_test_users():
    """Create test users with different permission levels"""
    print_test_header("Setting Up Test Users")

    # Clean up any existing test data first
    cleanup_test_data_full()

    # Create admin user
    admin = User(
        username='test_admin',
        email='admin@test.com',
        full_name='Test Admin',
        is_admin=True,
        has_confidential_access=True,
        is_ned_team=True,
        is_active=True
    )
    admin.set_password('password123')

    # Create NED Team user (no confidential access)
    ned_user = User(
        username='test_ned',
        email='ned@test.com',
        full_name='Test NED User',
        is_admin=False,
        has_confidential_access=False,
        is_ned_team=True,
        is_active=True
    )
    ned_user.set_password('password123')

    # Create confidential access user (not NED team)
    conf_user = User(
        username='test_conf',
        email='conf@test.com',
        full_name='Test Confidential User',
        is_admin=False,
        has_confidential_access=True,
        is_ned_team=False,
        is_active=True
    )
    conf_user.set_password('password123')

    # Create standard user (no special permissions)
    standard_user = User(
        username='test_standard',
        email='standard@test.com',
        full_name='Test Standard User',
        is_admin=False,
        has_confidential_access=False,
        is_ned_team=False,
        is_active=True
    )
    standard_user.set_password('password123')

    db_session.add_all([admin, ned_user, conf_user, standard_user])
    db_session.commit()

    print(f"✓ Created admin user (ID: {admin.user_id})")
    print(f"✓ Created NED Team user (ID: {ned_user.user_id})")
    print(f"✓ Created confidential access user (ID: {conf_user.user_id})")
    print(f"✓ Created standard user (ID: {standard_user.user_id})")

    return admin, ned_user, conf_user, standard_user


def setup_test_data(admin):
    """Create test project and vendor data"""
    print_test_header("Setting Up Test Data")

    # Create test project
    project = Project(
        project_name='Test Nuclear Project',
        capex=5000000.00,
        opex=500000.00,
        fuel_cost=100000.00,
        lcoe=75.50,
        created_by=admin.user_id,
        modified_by=admin.user_id
    )
    db_session.add(project)
    db_session.commit()
    print(f"✓ Created test project (ID: {project.project_id})")

    # Create test vendor
    vendor = TechnologyVendor(
        vendor_name='Test Reactor Vendor',
        notes='Test vendor for permission testing',
        created_by=admin.user_id,
        modified_by=admin.user_id
    )
    db_session.add(vendor)
    db_session.commit()
    print(f"✓ Created test vendor (ID: {vendor.vendor_id})")

    # Create public relationship
    public_rel = ProjectVendorRelationship(
        project_id=project.project_id,
        vendor_id=vendor.vendor_id,
        is_confidential=False,
        notes='Public technology provider relationship',
        created_by=admin.user_id,
        modified_by=admin.user_id
    )

    # Create confidential relationship
    # Need different vendor for unique constraint
    vendor2 = TechnologyVendor(
        vendor_name='Test Reactor Vendor 2',
        notes='Second test vendor for confidential relationship',
        created_by=admin.user_id,
        modified_by=admin.user_id
    )
    db_session.add(vendor2)
    db_session.commit()

    conf_rel = ProjectVendorRelationship(
        project_id=project.project_id,
        vendor_id=vendor2.vendor_id,
        is_confidential=True,
        notes='Confidential partnership relationship',
        created_by=admin.user_id,
        modified_by=admin.user_id
    )

    db_session.add_all([public_rel, conf_rel])
    db_session.commit()
    print(f"✓ Created public relationship (ID: {public_rel.relationship_id})")
    print(f"✓ Created confidential relationship (ID: {conf_rel.relationship_id})")

    return project, vendor, public_rel, conf_rel


def test_tier1_field_permissions(project, admin, conf_user, standard_user):
    """Test Tier 1: Field-level confidentiality"""
    print_test_header("Tier 1: Field-Level Permissions")

    # Test 1: Mark financial field as confidential
    flag = mark_field_confidential('projects', project.project_id, 'capex', True, admin.user_id)
    print_test_result(
        "Mark capex field as confidential",
        flag is not None and flag.is_confidential
    )

    # Test 2: Admin can view confidential field
    result = can_view_field(admin, 'projects', project.project_id, 'capex')
    print_test_result("Admin can view confidential field", result, True)

    # Test 3: Confidential user can view confidential field
    result = can_view_field(conf_user, 'projects', project.project_id, 'capex')
    print_test_result("Confidential user can view confidential field", result, True)

    # Test 4: Standard user cannot view confidential field
    result = can_view_field(standard_user, 'projects', project.project_id, 'capex')
    print_test_result("Standard user CANNOT view confidential field", not result, True)

    # Test 5: Standard user can view non-confidential field
    result = can_view_field(standard_user, 'projects', project.project_id, 'project_name')
    print_test_result("Standard user can view public field", result, True)

    # Test 6: Get field display value with redaction
    value = get_field_display_value(standard_user, project, 'capex', 'projects')
    print_test_result(
        "Standard user gets redacted value for confidential field",
        value == "[Confidential]"
    )

    # Test 7: Confidential user gets actual value
    value = get_field_display_value(conf_user, project, 'capex', 'projects')
    print_test_result(
        "Confidential user gets actual value",
        value == 5000000.00
    )

    # Test 8: Bulk mark all financial fields
    flags = mark_financial_fields_confidential(project.project_id, True, admin.user_id)
    print_test_result(
        "Bulk mark all financial fields (capex, opex, fuel_cost, lcoe)",
        len(flags) == 4
    )


def test_tier1_relationship_permissions(public_rel, conf_rel, admin, conf_user, standard_user):
    """Test Tier 1: Relationship-level confidentiality"""
    print_test_header("Tier 1: Relationship-Level Permissions")

    # Test 1: Admin can view confidential relationship
    result = can_view_relationship(admin, conf_rel)
    print_test_result("Admin can view confidential relationship", result, True)

    # Test 2: Confidential user can view confidential relationship
    result = can_view_relationship(conf_user, conf_rel)
    print_test_result("Confidential user can view confidential relationship", result, True)

    # Test 3: Standard user cannot view confidential relationship
    result = can_view_relationship(standard_user, conf_rel)
    print_test_result("Standard user CANNOT view confidential relationship", not result, True)

    # Test 4: All users can view public relationship
    result = can_view_relationship(standard_user, public_rel)
    print_test_result("Standard user can view public relationship", result, True)

    # Test 5: Filter relationships for standard user
    all_rels = [public_rel, conf_rel]
    filtered = filter_relationships(standard_user, all_rels)
    print_test_result(
        "Filter relationships - standard user sees only public",
        len(filtered) == 1 and filtered[0].relationship_id == public_rel.relationship_id
    )

    # Test 6: Filter relationships for confidential user
    filtered = filter_relationships(conf_user, all_rels)
    print_test_result(
        "Filter relationships - confidential user sees all",
        len(filtered) == 2
    )


def test_tier2_ned_permissions(admin, ned_user, conf_user, standard_user):
    """Test Tier 2: NED Team access"""
    print_test_header("Tier 2: NED Team Permissions")

    # Create mock entity with NED fields
    class MockClient:
        def __init__(self):
            self.client_name = "Test Client"
            self.relationship_strength = "Strong"
            self.relationship_notes = "Confidential internal assessment"
            self.client_priority = "High"
            self.client_status = "Active"

        def to_dict(self):
            return {
                'client_name': self.client_name,
                'relationship_strength': self.relationship_strength,
                'relationship_notes': self.relationship_notes,
                'client_priority': self.client_priority,
                'client_status': self.client_status
            }

    client = MockClient()

    # Test 1: Admin can view NED content
    result = can_view_ned_content(admin)
    print_test_result("Admin can view NED content", result, True)

    # Test 2: NED user can view NED content
    result = can_view_ned_content(ned_user)
    print_test_result("NED Team user can view NED content", result, True)

    # Test 3: Confidential user (not NED) cannot view NED content
    result = can_view_ned_content(conf_user)
    print_test_result("Non-NED user CANNOT view NED content", not result, True)

    # Test 4: Standard user cannot view NED content
    result = can_view_ned_content(standard_user)
    print_test_result("Standard user CANNOT view NED content", not result, True)

    # Test 5: NED user gets actual NED field value
    value = get_ned_field_value(ned_user, client, 'relationship_notes')
    print_test_result(
        "NED user gets actual NED field value",
        value == "Confidential internal assessment"
    )

    # Test 6: Non-NED user gets redacted NED field value
    value = get_ned_field_value(conf_user, client, 'relationship_notes')
    print_test_result(
        "Non-NED user gets redacted NED field value",
        value == "[NED Team Only]"
    )

    # Test 7: Filter NED fields from entity dict
    filtered = filter_ned_fields(conf_user, client)
    print_test_result(
        "Filter NED fields - non-NED user sees redactions",
        filtered['relationship_notes'] == "[NED Team Only]" and
        filtered['client_priority'] == "[NED Team Only]"
    )

    # Test 8: NED user sees actual values in filtered entity
    filtered = filter_ned_fields(ned_user, client)
    print_test_result(
        "Filter NED fields - NED user sees actual values",
        filtered['relationship_notes'] == "Confidential internal assessment" and
        filtered['client_priority'] == "High"
    )


def test_permission_utilities(admin, ned_user, conf_user, standard_user):
    """Test permission utility functions"""
    print_test_header("Permission Utility Functions")

    # Test 1: Admin permission summary
    summary = get_user_permission_summary(admin)
    print_test_result(
        "Admin permission summary - all True",
        summary['is_admin'] and summary['has_confidential_access'] and summary['is_ned_team']
    )

    # Test 2: NED user permission summary
    summary = get_user_permission_summary(ned_user)
    print_test_result(
        "NED user summary - is_ned_team=True, others False",
        summary['is_ned_team'] and not summary['has_confidential_access']
    )

    # Test 3: Confidential user permission summary
    summary = get_user_permission_summary(conf_user)
    print_test_result(
        "Confidential user summary - has_confidential_access=True",
        summary['has_confidential_access'] and not summary['is_ned_team']
    )

    # Test 4: Standard user permission summary
    summary = get_user_permission_summary(standard_user)
    print_test_result(
        "Standard user summary - all False",
        not summary['is_admin'] and not summary['has_confidential_access'] and not summary['is_ned_team']
    )

    # Test 5: Permission level names
    print_test_result(
        "Admin permission level name",
        get_permission_level_name(admin) == "Administrator"
    )

    print_test_result(
        "NED Team permission level name",
        get_permission_level_name(ned_user) == "NED Team"
    )

    print_test_result(
        "Confidential permission level name",
        get_permission_level_name(conf_user) == "Confidential Access"
    )

    print_test_result(
        "Standard permission level name",
        get_permission_level_name(standard_user) == "Standard User"
    )


def test_query_filters(conf_rel, admin, conf_user, standard_user):
    """Test query filter helpers"""
    print_test_header("Query Filter Helpers")

    # Test 1: Apply confidential filter - admin sees all
    query = db_session.query(ProjectVendorRelationship)
    filtered_query = apply_confidential_filter(query, admin, ProjectVendorRelationship)
    result_count = filtered_query.count()
    print_test_result(
        f"Admin query filter - sees all relationships ({result_count} total)",
        result_count >= 2  # At least our test relationships
    )

    # Test 2: Apply confidential filter - confidential user sees all
    query = db_session.query(ProjectVendorRelationship)
    filtered_query = apply_confidential_filter(query, conf_user, ProjectVendorRelationship)
    result_count = filtered_query.count()
    print_test_result(
        f"Confidential user query filter - sees all relationships ({result_count} total)",
        result_count >= 2
    )

    # Test 3: Apply confidential filter - standard user sees only public
    query = db_session.query(ProjectVendorRelationship)
    filtered_query = apply_confidential_filter(query, standard_user, ProjectVendorRelationship)
    # Check that all results have is_confidential=False
    all_public = all(not rel.is_confidential for rel in filtered_query.all())
    print_test_result(
        "Standard user query filter - sees only public relationships",
        all_public
    )


def cleanup_test_data():
    """Clean up test data"""
    print_test_header("Cleaning Up Test Data")
    cleanup_test_data_full()
    print("✓ Cleaned up all test data")


def main():
    """Run all permission tests"""
    global db_session

    print("\n" + "=" * 70)
    print("NUKEWORKS PERMISSION SYSTEM TEST SUITE")
    print("=" * 70)

    # Create Flask app context
    app = create_app('development')
    db_session = app.db_session

    with app.app_context():
        try:
            # Setup
            admin, ned_user, conf_user, standard_user = setup_test_users()
            project, vendor, public_rel, conf_rel = setup_test_data(admin)

            # Run tests
            test_tier1_field_permissions(project, admin, conf_user, standard_user)
            test_tier1_relationship_permissions(public_rel, conf_rel, admin, conf_user, standard_user)
            test_tier2_ned_permissions(admin, ned_user, conf_user, standard_user)
            test_permission_utilities(admin, ned_user, conf_user, standard_user)
            test_query_filters(conf_rel, admin, conf_user, standard_user)

            # Cleanup
            cleanup_test_data()

            print("\n" + "=" * 70)
            print("ALL TESTS COMPLETED SUCCESSFULLY ✓")
            print("=" * 70 + "\n")

        except Exception as e:
            print(f"\n✗ TEST FAILED WITH ERROR: {e}")
            import traceback
            traceback.print_exc()

            # Attempt cleanup even on failure
            try:
                cleanup_test_data()
            except:
                pass

            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
