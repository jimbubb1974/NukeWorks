#!/usr/bin/env python3
"""
Test basic encryption/decryption functionality
Verifies that the encryption keys are working correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_key_loading():
    """Test that encryption keys can be loaded from environment"""
    print("=" * 70)
    print("Testing Encryption Key Loading")
    print("=" * 70)

    confidential_key = os.environ.get('CONFIDENTIAL_DATA_KEY')
    ned_team_key = os.environ.get('NED_TEAM_KEY')

    if not confidential_key:
        print("[ERROR] CONFIDENTIAL_DATA_KEY not found in environment")
        return False

    if not ned_team_key:
        print("[ERROR] NED_TEAM_KEY not found in environment")
        return False

    print(f"[OK] CONFIDENTIAL_DATA_KEY loaded: {confidential_key[:20]}...")
    print(f"[OK] NED_TEAM_KEY loaded: {ned_team_key[:20]}...")
    print()
    return True


def test_encryption_decryption():
    """Test basic encryption and decryption"""
    print("=" * 70)
    print("Testing Encryption/Decryption")
    print("=" * 70)

    # Load key
    confidential_key = os.environ.get('CONFIDENTIAL_DATA_KEY')
    cipher = Fernet(confidential_key.encode())

    # Test data
    test_data = {
        'capex': '$5,000,000',
        'opex': '$500,000 per year',
        'lcoe': '$0.085/kWh',
        'confidential_note': 'This is sensitive business information'
    }

    print("\nOriginal data:")
    for key, value in test_data.items():
        print(f"  {key}: {value}")

    # Encrypt
    print("\nEncrypting...")
    encrypted_data = {}
    for key, value in test_data.items():
        encrypted = cipher.encrypt(value.encode('utf-8'))
        encrypted_data[key] = encrypted
        print(f"  {key}: {encrypted[:40]}... ({len(encrypted)} bytes)")

    # Decrypt
    print("\nDecrypting...")
    decrypted_data = {}
    for key, encrypted in encrypted_data.items():
        decrypted = cipher.decrypt(encrypted).decode('utf-8')
        decrypted_data[key] = decrypted
        print(f"  {key}: {decrypted}")

    # Verify
    print("\nVerification:")
    all_match = True
    for key in test_data:
        match = test_data[key] == decrypted_data[key]
        status = "[OK]" if match else "[FAIL]"
        print(f"  {status} {key}: {'Match' if match else 'Mismatch'}")
        if not match:
            all_match = False

    print()
    return all_match


def test_permission_simulation():
    """Simulate permission-based access to encrypted data"""
    print("=" * 70)
    print("Testing Permission-Based Access Simulation")
    print("=" * 70)

    confidential_key = os.environ.get('CONFIDENTIAL_DATA_KEY')
    cipher = Fernet(confidential_key.encode())

    # Encrypted confidential data
    capex_value = "$5,000,000"
    encrypted_capex = cipher.encrypt(capex_value.encode('utf-8'))

    print(f"\nOriginal value: {capex_value}")
    print(f"Encrypted value: {encrypted_capex[:50]}...")
    print()

    # Simulate Joe (no confidential access)
    print("User: Joe (has_confidential_access=False)")
    print("  - Cannot decrypt: Shows '[Confidential]'")
    print(f"  - Joe sees: [Confidential]")
    print()

    # Simulate Sally (has confidential access)
    print("User: Sally (has_confidential_access=True)")
    print("  - Can decrypt with key")
    decrypted_value = cipher.decrypt(encrypted_capex).decode('utf-8')
    print(f"  - Sally sees: {decrypted_value}")
    print()

    return True


def main():
    """Run all tests"""
    print("\n")
    print("=" * 70)
    print("NUKEWORKS ENCRYPTION TEST SUITE")
    print("=" * 70)
    print()

    results = []

    # Test 1: Key Loading
    results.append(("Key Loading", test_key_loading()))

    # Test 2: Encryption/Decryption
    results.append(("Encryption/Decryption", test_encryption_decryption()))

    # Test 3: Permission Simulation
    results.append(("Permission Simulation", test_permission_simulation()))

    # Summary
    print("=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    all_passed = all(result[1] for result in results)

    print()
    print("=" * 70)
    if all_passed:
        print("[SUCCESS] All tests passed!")
        print("Encryption system is ready for use.")
    else:
        print("[FAILURE] Some tests failed.")
        print("Please review errors above.")
    print("=" * 70)
    print()

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
