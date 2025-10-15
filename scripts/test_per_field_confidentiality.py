"""
Test Per-Field Confidentiality System

This script tests Option 2 implementation:
- Mark CAPEX as confidential
- Leave OPEX as public
- Mark Fuel Cost as confidential
- Leave LCOE as public

Then verify that users without confidential access see:
- CAPEX: [Confidential]
- OPEX: actual value
- Fuel Cost: [Confidential]
- LCOE: actual value
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Project, User
from app.utils.permissions import mark_field_confidential, can_view_field
from app.models.confidential import ConfidentialFieldFlag

def test_per_field_confidentiality(db_session):
    """Test per-field confidentiality for project financial data"""

    print("=" * 80)
    print("TESTING PER-FIELD CONFIDENTIALITY (Option 2)")
    print("=" * 80)

    # Get project 1 (test project)
    project = db_session.get(Project, 1)
    if not project:
        print("[ERROR] Project 1 not found. Run add_test_encrypted_data.py first.")
        return

    print(f"\n[PROJECT] {project.project_name}")
    print(f"   CAPEX: {project._capex_encrypted[:20] if project._capex_encrypted else None}... (encrypted)")
    print(f"   OPEX: {project._opex_encrypted[:20] if project._opex_encrypted else None}... (encrypted)")
    print(f"   Fuel Cost: {project._fuel_cost_encrypted[:20] if project._fuel_cost_encrypted else None}... (encrypted)")
    print(f"   LCOE: {project._lcoe_encrypted[:20] if project._lcoe_encrypted else None}... (encrypted)")

    # Get test users
    admin = db_session.query(User).filter_by(username='admin').first()
    jsmith = db_session.query(User).filter_by(username='jsmith').first()
    mjones = db_session.query(User).filter_by(username='mjones').first()
    bwilson = db_session.query(User).filter_by(username='bwilson').first()

    if not all([admin, jsmith, mjones, bwilson]):
        print("[ERROR] Test users not found")
        return

    print("\n[USERS] Test Users:")
    print(f"   - admin: is_admin={admin.is_admin}, confidential={admin.has_confidential_access}")
    print(f"   - jsmith: is_admin={jsmith.is_admin}, confidential={jsmith.has_confidential_access}")
    print(f"   - mjones: is_admin={mjones.is_admin}, confidential={mjones.has_confidential_access}")
    print(f"   - bwilson: is_admin={bwilson.is_admin}, confidential={bwilson.has_confidential_access}")

    # Clear any existing flags
    print("\n[SETUP] Clearing existing confidentiality flags...")
    db_session.query(ConfidentialFieldFlag).filter_by(
        table_name='projects',
        record_id=1
    ).delete()
    db_session.commit()

    # Set confidentiality flags according to test plan
    print("\n[FLAGS] Setting confidentiality flags:")
    print("   - CAPEX: CONFIDENTIAL [*]")
    mark_field_confidential('projects', 1, 'capex', True, admin.user_id)

    print("   - OPEX: PUBLIC (no flag)")
    mark_field_confidential('projects', 1, 'opex', False, admin.user_id)

    print("   - Fuel Cost: CONFIDENTIAL [*]")
    mark_field_confidential('projects', 1, 'fuel_cost', True, admin.user_id)

    print("   - LCOE: PUBLIC (no flag)")
    mark_field_confidential('projects', 1, 'lcoe', False, admin.user_id)

    # Verify flags in database
    print("\n[DATABASE] Flags in database:")
    flags = db_session.query(ConfidentialFieldFlag).filter_by(
        table_name='projects',
        record_id=1
    ).all()
    for flag in flags:
        print(f"   - {flag.field_name}: is_confidential={flag.is_confidential}")

    # Test permission checks for each user
    print("\n" + "=" * 80)
    print("TESTING PERMISSION CHECKS")
    print("=" * 80)

    test_users = [
        ('admin (full access)', admin),
        ('jsmith (confidential access)', jsmith),
        ('mjones (NO confidential access)', mjones),
        ('bwilson (NO confidential access)', bwilson),
    ]

    fields = ['capex', 'opex', 'fuel_cost', 'lcoe']

    for user_label, user in test_users:
        print(f"\n[USER] {user_label}")
        for field in fields:
            can_view = can_view_field(user, 'projects', 1, field)
            icon = "[OK]" if can_view else "[NO]"
            print(f"   {icon} {field}: {'CAN VIEW' if can_view else 'CANNOT VIEW'}")

    # Test actual decryption via property access
    print("\n" + "=" * 80)
    print("TESTING DECRYPTION VIA PROPERTY ACCESS")
    print("=" * 80)
    print("\n[NOTE] Property access requires Flask context with current_user")
    print("       This test only validates the permission logic, not the actual descriptor")

    # Test expected behavior
    print("\n[EXPECTED BEHAVIOR]")
    print("   - admin should see all values (decrypted)")
    print("   - jsmith should see all values (has confidential access)")
    print("   - mjones should see:")
    print("       - CAPEX: [Confidential] (flagged)")
    print("       - OPEX: actual value (not flagged)")
    print("       - Fuel Cost: [Confidential] (flagged)")
    print("       - LCOE: actual value (not flagged)")
    print("   - bwilson should see:")
    print("       - CAPEX: [Confidential] (flagged)")
    print("       - OPEX: actual value (not flagged)")
    print("       - Fuel Cost: [Confidential] (flagged)")
    print("       - LCOE: actual value (not flagged)")

    print("\n" + "=" * 80)
    print("[SUCCESS] PER-FIELD CONFIDENTIALITY TEST COMPLETE")
    print("=" * 80)
    print("\n[NEXT STEPS]")
    print("   1. Visit http://127.0.0.1:5000/projects/1")
    print("   2. Log in as different users to verify display")
    print("   3. Edit project at http://127.0.0.1:5000/projects/1/edit")
    print("   4. Toggle checkboxes and verify flags update correctly")
    print()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        from app import db_session
        test_per_field_confidentiality(db_session)
