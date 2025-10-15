#!/usr/bin/env python3
"""
Generate master encryption keys for NukeWorks field-level encryption

This script generates cryptographically secure keys for:
- CONFIDENTIAL_DATA_KEY: Encrypts financial and competitive data
- NED_TEAM_KEY: Encrypts internal team notes and relationship data

Usage:
    python scripts/generate_encryption_keys.py

The keys are printed to stdout. Add them to your .env file.
IMPORTANT: Store these keys securely and back them up!
"""

from cryptography.fernet import Fernet
import sys


def generate_keys():
    """Generate and display encryption keys"""

    print("=" * 70)
    print("NukeWorks Encryption Key Generator")
    print("=" * 70)
    print()
    print("Generating cryptographically secure encryption keys...")
    print()

    # Generate keys
    confidential_key = Fernet.generate_key().decode()
    ned_team_key = Fernet.generate_key().decode()

    print("[OK] Keys generated successfully!")
    print()
    print("=" * 70)
    print("ADD THESE TO YOUR .env FILE:")
    print("=" * 70)
    print()
    print("# Master encryption keys for field-level encryption")
    print(f"CONFIDENTIAL_DATA_KEY={confidential_key}")
    print(f"NED_TEAM_KEY={ned_team_key}")
    print()
    print("=" * 70)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 70)
    print()
    print("1. BACKUP THESE KEYS SECURELY")
    print("   - Without these keys, encrypted data CANNOT be recovered")
    print("   - Store in a password manager or secure vault")
    print()
    print("2. NEVER COMMIT .env TO VERSION CONTROL")
    print("   - .env is already in .gitignore")
    print("   - Keys should never appear in git history")
    print()
    print("3. USE DIFFERENT KEYS FOR EACH ENVIRONMENT")
    print("   - Development: Use these generated keys")
    print("   - Production: Generate separate keys")
    print()
    print("4. KEY ROTATION")
    print("   - Plan to rotate keys periodically (e.g., annually)")
    print("   - Document rotation procedure in advance")
    print()
    print("5. ACCESS CONTROL")
    print("   - Only administrators should have access to these keys")
    print("   - Keys grant ability to decrypt ALL confidential data")
    print()
    print("=" * 70)
    print()


if __name__ == '__main__':
    try:
        generate_keys()
    except KeyboardInterrupt:
        print("\n\nKey generation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError generating keys: {e}")
        sys.exit(1)
