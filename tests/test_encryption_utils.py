"""
Tests for encryption utilities and key management
"""

import pytest
import os
from app.utils.encryption import (
    encrypt_value,
    decrypt_value,
    decrypt_for_user,
    encrypt_confidential,
    decrypt_confidential,
    PermissionBasedEncryption
)
from app.utils.key_management import KeyManager, validate_encryption_keys
from app.exceptions import DecryptionError, EncryptionKeyError


# =============================================================================
# TEST KEY MANAGEMENT
# =============================================================================

def test_key_manager_loads_keys():
    """Test that KeyManager loads keys from environment"""
    # Keys should be loaded from .env file
    confidential_key = KeyManager.get_key('confidential')
    ned_team_key = KeyManager.get_key('ned_team')

    assert confidential_key is not None
    assert ned_team_key is not None
    assert isinstance(confidential_key, bytes)
    assert isinstance(ned_team_key, bytes)


def test_key_manager_get_cipher():
    """Test that KeyManager returns valid Fernet ciphers"""
    cipher = KeyManager.get_cipher('confidential')
    assert cipher is not None

    # Test encryption/decryption works
    test_data = b"test data"
    encrypted = cipher.encrypt(test_data)
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == test_data


def test_key_validation():
    """Test that key validation works"""
    result = validate_encryption_keys()
    assert result is True


def test_invalid_key_type():
    """Test that invalid key type raises error"""
    with pytest.raises(EncryptionKeyError):
        KeyManager.get_key('invalid_type')


# =============================================================================
# TEST ENCRYPTION/DECRYPTION
# =============================================================================

def test_encrypt_decrypt_confidential():
    """Test encrypting and decrypting confidential data"""
    original_value = "$5,000,000"

    # Encrypt
    encrypted = encrypt_confidential(original_value)
    assert encrypted is not None
    assert isinstance(encrypted, bytes)
    assert encrypted != original_value.encode()  # Should be different

    # Decrypt
    decrypted = decrypt_confidential(encrypted)
    assert decrypted == original_value


def test_encrypt_decrypt_various_types():
    """Test encryption works with various data types"""
    test_values = [
        "$5,000,000",
        "500000",
        "0.085",
        "This is a long note with special characters: !@#$%^&*()",
        "",  # Empty string
    ]

    for value in test_values:
        encrypted = encrypt_value(value, 'confidential')
        decrypted = decrypt_value(encrypted, 'confidential')
        assert decrypted == str(value), f"Failed for value: {value}"


def test_encrypt_none():
    """Test that None values are handled correctly"""
    encrypted = encrypt_value(None, 'confidential')
    assert encrypted is None

    decrypted = decrypt_value(None, 'confidential')
    assert decrypted is None


def test_decrypt_invalid_data():
    """Test that decrypting invalid data raises error"""
    invalid_data = b"this is not encrypted data"

    with pytest.raises(DecryptionError):
        decrypt_value(invalid_data, 'confidential')


# =============================================================================
# TEST PERMISSION-BASED ACCESS
# =============================================================================

class MockUser:
    """Mock user for testing"""
    def __init__(self, has_confidential_access=False, is_ned_team=False, is_admin=False):
        self.is_authenticated = True
        self.has_confidential_access = has_confidential_access
        self.is_ned_team = is_ned_team
        self.is_admin = is_admin


def test_user_can_access_confidential_key():
    """Test that users with confidential access can access confidential key"""
    # User with confidential access
    user = MockUser(has_confidential_access=True)
    assert KeyManager.user_can_access_key(user, 'confidential') is True

    # User without confidential access
    user = MockUser(has_confidential_access=False)
    assert KeyManager.user_can_access_key(user, 'confidential') is False

    # Admin always has access
    user = MockUser(is_admin=True)
    assert KeyManager.user_can_access_key(user, 'confidential') is True


def test_user_can_access_ned_team_key():
    """Test that NED team members can access NED team key"""
    # NED team member
    user = MockUser(is_ned_team=True)
    assert KeyManager.user_can_access_key(user, 'ned_team') is True

    # Non-NED team member
    user = MockUser(is_ned_team=False)
    assert KeyManager.user_can_access_key(user, 'ned_team') is False

    # Admin always has access
    user = MockUser(is_admin=True)
    assert KeyManager.user_can_access_key(user, 'ned_team') is True


def test_decrypt_for_user_with_permission():
    """Test that users with permission can decrypt data"""
    original_value = "$5,000,000"
    encrypted = encrypt_confidential(original_value)

    # User with confidential access
    user = MockUser(has_confidential_access=True)
    decrypted = decrypt_for_user(encrypted, 'confidential', user)
    assert decrypted == original_value


def test_decrypt_for_user_without_permission():
    """Test that users without permission see redaction message"""
    original_value = "$5,000,000"
    encrypted = encrypt_confidential(original_value)

    # User without confidential access
    user = MockUser(has_confidential_access=False)
    decrypted = decrypt_for_user(encrypted, 'confidential', user)
    assert decrypted == "[Confidential]"


def test_decrypt_for_user_custom_redaction():
    """Test custom redaction message"""
    original_value = "Internal notes"
    encrypted = encrypt_value(original_value, 'ned_team')

    user = MockUser(is_ned_team=False)
    decrypted = decrypt_for_user(
        encrypted,
        'ned_team',
        user,
        redaction_message="[NED Team Only]"
    )
    assert decrypted == "[NED Team Only]"


def test_get_user_key_access():
    """Test getting summary of user's key access"""
    # Standard user
    user = MockUser()
    access = PermissionBasedEncryption.get_user_key_access(user)
    assert access['confidential'] is False
    assert access['ned_team'] is False

    # Confidential user
    user = MockUser(has_confidential_access=True)
    access = PermissionBasedEncryption.get_user_key_access(user)
    assert access['confidential'] is True
    assert access['ned_team'] is False

    # NED team user
    user = MockUser(is_ned_team=True)
    access = PermissionBasedEncryption.get_user_key_access(user)
    assert access['confidential'] is False
    assert access['ned_team'] is True

    # Admin
    user = MockUser(is_admin=True)
    access = PermissionBasedEncryption.get_user_key_access(user)
    assert access['confidential'] is True
    assert access['ned_team'] is True


# =============================================================================
# TEST USER SCENARIOS
# =============================================================================

def test_joe_scenario():
    """
    Test Joe's experience (standard user, no confidential access)
    He should see redacted messages for all encrypted confidential data
    """
    joe = MockUser(has_confidential_access=False, is_ned_team=False)

    # Joe tries to view confidential financial data
    capex_encrypted = encrypt_confidential("$5,000,000")
    capex_view = decrypt_for_user(capex_encrypted, 'confidential', joe)
    assert capex_view == "[Confidential]"

    opex_encrypted = encrypt_confidential("$500,000")
    opex_view = decrypt_for_user(opex_encrypted, 'confidential', joe)
    assert opex_view == "[Confidential]"

    # Joe also can't see NED team notes
    notes_encrypted = encrypt_value("Confidential relationship notes", 'ned_team')
    notes_view = decrypt_for_user(notes_encrypted, 'ned_team', joe)
    assert notes_view == "[Confidential]"


def test_sally_scenario():
    """
    Test Sally's experience (confidential access but not NED team)
    She should see confidential financial data but not NED team notes
    """
    sally = MockUser(has_confidential_access=True, is_ned_team=False)

    # Sally can view confidential financial data
    capex_encrypted = encrypt_confidential("$5,000,000")
    capex_view = decrypt_for_user(capex_encrypted, 'confidential', sally)
    assert capex_view == "$5,000,000"

    opex_encrypted = encrypt_confidential("$500,000")
    opex_view = decrypt_for_user(opex_encrypted, 'confidential', sally)
    assert opex_view == "$500,000"

    # Sally cannot see NED team notes
    notes_encrypted = encrypt_value("Confidential relationship notes", 'ned_team')
    notes_view = decrypt_for_user(notes_encrypted, 'ned_team', sally)
    assert notes_view == "[Confidential]"


def test_admin_scenario():
    """
    Test Admin's experience
    They should see everything
    """
    admin = MockUser(is_admin=True)

    # Admin can view confidential financial data
    capex_encrypted = encrypt_confidential("$5,000,000")
    capex_view = decrypt_for_user(capex_encrypted, 'confidential', admin)
    assert capex_view == "$5,000,000"

    # Admin can also see NED team notes
    notes_encrypted = encrypt_value("Confidential relationship notes", 'ned_team')
    notes_view = decrypt_for_user(notes_encrypted, 'ned_team', admin)
    assert notes_view == "Confidential relationship notes"


# =============================================================================
# TEST DATABASE BROWSER SCENARIO
# =============================================================================

def test_database_browser_sees_encrypted_data():
    """
    Simulate what happens when someone opens the database with DB Browser
    Even with the database file, they should only see encrypted gibberish
    """
    # Encrypt confidential data
    capex_original = "$5,000,000"
    capex_encrypted = encrypt_confidential(capex_original)

    # This is what's stored in the database (what DB Browser sees)
    database_stored_value = capex_encrypted

    # Verify it's encrypted (looks like gibberish)
    assert database_stored_value != capex_original.encode()
    assert database_stored_value.startswith(b'gAAAAA')  # Fernet format

    # Verify it's at least 100 bytes (encrypted data is larger)
    assert len(database_stored_value) >= 100

    # Even if Joe opens DB Browser, he sees this gibberish
    # He can't decrypt it without the CONFIDENTIAL_DATA_KEY from .env
    print(f"\nWhat DB Browser shows: {database_stored_value[:50]}...")
    print(f"Length: {len(database_stored_value)} bytes")

    # Only someone with the key can decrypt
    decrypted = decrypt_confidential(database_stored_value)
    assert decrypted == capex_original
