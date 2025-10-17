#!/usr/bin/env python3
"""
Manual test runner for encryption utilities
Bypasses pytest to avoid conftest import issues
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Import test functions
from tests.test_encryption_utils import *

def run_test(test_func, test_name):
    """Run a single test function"""
    try:
        test_func()
        print(f"[PASS] {test_name}")
        return True
    except AssertionError as e:
        print(f"[FAIL] {test_name}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {test_name}: {e}")
        return False


def main():
    print("=" * 70)
    print("ENCRYPTION UTILITIES TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        # Key Management Tests
        (test_key_manager_loads_keys, "Key Manager loads keys from environment"),
        (test_key_manager_get_cipher, "Key Manager returns valid Fernet ciphers"),
        (test_key_validation, "Key validation works"),
        (test_invalid_key_type, "Invalid key type raises error"),

        # Encryption/Decryption Tests
        (test_encrypt_decrypt_confidential, "Encrypt and decrypt confidential data"),
        (test_encrypt_decrypt_various_types, "Encryption works with various data types"),
        (test_encrypt_none, "None values handled correctly"),
        (test_decrypt_invalid_data, "Decrypting invalid data raises error"),

        # Permission-Based Access Tests
        (test_user_can_access_confidential_key, "User confidential key access control"),
        (test_user_can_access_ned_team_key, "User NED team key access control"),
        (test_decrypt_for_user_with_permission, "Users with permission can decrypt"),
        (test_decrypt_for_user_without_permission, "Users without permission see redaction"),
        (test_decrypt_for_user_custom_redaction, "Custom redaction message works"),
        (test_get_user_key_access, "Get user key access summary"),

        # User Scenario Tests
        (test_joe_scenario, "Joe's scenario (standard user)"),
        (test_sally_scenario, "Sally's scenario (confidential access)"),
        (test_admin_scenario, "Admin scenario (full access)"),

        # Database Browser Test
        (test_database_browser_sees_encrypted_data, "DB Browser sees encrypted data"),
    ]

    passed = 0
    failed = 0

    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    print()

    if failed == 0:
        print("[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"[FAILURE] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
