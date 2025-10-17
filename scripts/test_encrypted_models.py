#!/usr/bin/env python3
"""
Test Encrypted Models

Quick verification that encrypted model fields work correctly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


def test_encrypted_field_descriptor():
    """Test that EncryptedField descriptor works"""
    from app.utils.encryption import EncryptedField, encrypt_value

    print("=" * 70)
    print("TEST: EncryptedField Descriptor")
    print("=" * 70)

    # Create a mock object
    class MockModel:
        def __init__(self):
            self._test_encrypted = None

    # Add encrypted field
    MockModel.test_field = EncryptedField('_test_encrypted', 'confidential')

    obj = MockModel()

    # Test setting value (should encrypt)
    obj.test_field = "$5,000,000"

    # Check that internal storage is encrypted
    assert obj._test_encrypted is not None
    assert isinstance(obj._test_encrypted, bytes)
    assert obj._test_encrypted.startswith(b'gAAAAA')  # Fernet format

    print("[OK] Setting value encrypts data")
    print(f"  Original: $5,000,000")
    print(f"  Encrypted: {obj._test_encrypted[:50]}... ({len(obj._test_encrypted)} bytes)")

    print("\n[SUCCESS] EncryptedField descriptor works!")
    return True


def test_project_model():
    """Test that Project model encrypted fields work"""
    from app.models.project import Project

    print("\n" + "=" * 70)
    print("TEST: Project Model Encrypted Fields")
    print("=" * 70)

    # Create project
    project = Project()
    project.project_name = "Test Nuclear Plant"
    project.capex = "5000000"
    project.opex = "500000"
    project.fuel_cost = "10000"
    project.lcoe = "0.085"

    # Check that values are encrypted in storage
    assert project._capex_encrypted is not None
    assert isinstance(project._capex_encrypted, bytes)

    print("[OK] Project financial fields are encrypted")
    print(f"  capex: {project._capex_encrypted[:30]}...")
    print(f"  opex: {project._opex_encrypted[:30]}...")

    print("\n[SUCCESS] Project model encryption works!")
    return True


def test_client_profile_model():
    """Test that ClientProfile model encrypted fields work"""
    from app.models.company import ClientProfile

    print("\n" + "=" * 70)
    print("TEST: ClientProfile Model Encrypted Fields")
    print("=" * 70)

    # Create client profile
    profile = ClientProfile()
    profile.company_id = 1
    profile.relationship_strength = "Strong"
    profile.relationship_notes = "Good relationship with decision makers"
    profile.client_priority = "High"
    profile.client_status = "Active"

    # Check that values are encrypted in storage
    assert profile._relationship_strength_encrypted is not None
    assert isinstance(profile._relationship_strength_encrypted, bytes)

    print("[OK] ClientProfile CRM fields are encrypted")
    print(f"  relationship_strength: {profile._relationship_strength_encrypted[:30]}...")
    print(f"  relationship_notes: {profile._relationship_notes_encrypted[:30]}...")

    print("\n[SUCCESS] ClientProfile model encryption works!")
    return True


def test_roundtable_model():
    """Test that RoundtableHistory model encrypted fields work"""
    from app.models.roundtable import RoundtableHistory

    print("\n" + "=" * 70)
    print("TEST: RoundtableHistory Model Encrypted Fields")
    print("=" * 70)

    # Create roundtable entry
    entry = RoundtableHistory()
    entry.entity_type = "Project"
    entry.entity_id = 1
    entry.discussion = "Discussed project timeline and budget"
    entry.action_items = "Follow up on licensing application"
    entry.next_steps = "Schedule technical review meeting"

    # Check that values are encrypted in storage
    assert entry._discussion_encrypted is not None
    assert isinstance(entry._discussion_encrypted, bytes)

    print("[OK] RoundtableHistory fields are encrypted")
    print(f"  discussion: {entry._discussion_encrypted[:30]}...")
    print(f"  action_items: {entry._action_items_encrypted[:30]}...")

    print("\n[SUCCESS] RoundtableHistory model encryption works!")
    return True


def main():
    """Run all tests"""
    print("\n")
    print("=" * 70)
    print("ENCRYPTED MODELS TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("EncryptedField Descriptor", test_encrypted_field_descriptor),
        ("Project Model", test_project_model),
        ("ClientProfile Model", test_client_profile_model),
        ("RoundtableHistory Model", test_roundtable_model),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n[FAIL] {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"\n[ERROR] {test_name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    print()

    if failed == 0:
        print("[SUCCESS] All tests passed!")
        print("\nYour encrypted models are ready to use!")
        print("\nNEXT STEPS:")
        print("1. Run migration 013 to add encrypted columns:")
        print("   sqlite3 databases/development/nukeworks.sqlite < migrations/013_add_encrypted_columns.sql")
        print("\n2. Migrate existing data to encrypted format:")
        print("   python scripts/migrate_data_to_encrypted.py databases/development/nukeworks.sqlite --dry-run")
        print("   python scripts/migrate_data_to_encrypted.py databases/development/nukeworks.sqlite")
        print("\n3. Test the application with encrypted data")
        return 0
    else:
        print(f"[FAILURE] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
