"""
Key Management for NukeWorks Field-Level Encryption

Handles loading and access control for master encryption keys.
Keys are stored in environment variables and never exposed to users.
"""

import os
from typing import Dict, Optional
from cryptography.fernet import Fernet
from app.exceptions import EncryptionKeyError


class KeyManager:
    """
    Manages master encryption keys and permission-based access

    Master keys are stored in environment variables:
    - CONFIDENTIAL_DATA_KEY: Encrypts financial and competitive data
    - NED_TEAM_KEY: Encrypts internal team notes and relationship data
    """

    # Key type constants
    CONFIDENTIAL = 'confidential'
    NED_TEAM = 'ned_team'

    _keys: Optional[Dict[str, bytes]] = None

    @classmethod
    def _load_keys(cls) -> Dict[str, bytes]:
        """
        Load master encryption keys from environment variables

        Returns:
            dict: Keys by type

        Raises:
            EncryptionKeyError: If required keys are missing
        """
        if cls._keys is not None:
            return cls._keys

        confidential_key = os.environ.get('CONFIDENTIAL_DATA_KEY')
        ned_team_key = os.environ.get('NED_TEAM_KEY')

        if not confidential_key:
            raise EncryptionKeyError(
                "CONFIDENTIAL_DATA_KEY not found in environment. "
                "Run scripts/generate_encryption_keys.py to generate keys."
            )

        if not ned_team_key:
            raise EncryptionKeyError(
                "NED_TEAM_KEY not found in environment. "
                "Run scripts/generate_encryption_keys.py to generate keys."
            )

        # Store as bytes for Fernet
        cls._keys = {
            cls.CONFIDENTIAL: confidential_key.encode(),
            cls.NED_TEAM: ned_team_key.encode(),
        }

        return cls._keys

    @classmethod
    def get_key(cls, key_type: str) -> bytes:
        """
        Get a specific encryption key by type

        Args:
            key_type: 'confidential' or 'ned_team'

        Returns:
            bytes: The encryption key

        Raises:
            EncryptionKeyError: If key type is invalid or key not found
        """
        keys = cls._load_keys()

        if key_type not in keys:
            raise EncryptionKeyError(
                f"Invalid key type: {key_type}. "
                f"Must be one of: {', '.join(keys.keys())}"
            )

        return keys[key_type]

    @classmethod
    def get_cipher(cls, key_type: str) -> Fernet:
        """
        Get a Fernet cipher for a specific key type

        Args:
            key_type: 'confidential' or 'ned_team'

        Returns:
            Fernet: Cipher instance for encryption/decryption
        """
        key = cls.get_key(key_type)
        return Fernet(key)

    @classmethod
    def get_keys_for_user(cls, user) -> Dict[str, bytes]:
        """
        Get encryption keys that a user is authorized to access
        Based on user's permission flags

        Args:
            user: User object with permission flags

        Returns:
            dict: Keys the user can access (by key type)
        """
        if not user or not user.is_authenticated:
            return {}

        authorized_keys = {}

        # Check confidential access permission
        if user.has_confidential_access or user.is_admin:
            authorized_keys[cls.CONFIDENTIAL] = cls.get_key(cls.CONFIDENTIAL)

        # Check NED team permission
        if user.is_ned_team or user.is_admin:
            authorized_keys[cls.NED_TEAM] = cls.get_key(cls.NED_TEAM)

        return authorized_keys

    @classmethod
    def user_can_access_key(cls, user, key_type: str) -> bool:
        """
        Check if a user has permission to access a specific key type

        Args:
            user: User object
            key_type: 'confidential' or 'ned_team'

        Returns:
            bool: True if user has permission
        """
        if not user or not user.is_authenticated:
            return False

        if key_type == cls.CONFIDENTIAL:
            return user.has_confidential_access or user.is_admin

        if key_type == cls.NED_TEAM:
            return user.is_ned_team or user.is_admin

        return False

    @classmethod
    def validate_keys(cls) -> bool:
        """
        Validate that all required keys are present and valid

        Returns:
            bool: True if all keys are valid

        Raises:
            EncryptionKeyError: If any keys are missing or invalid
        """
        try:
            keys = cls._load_keys()

            # Test that each key can create a valid Fernet cipher
            for key_type, key in keys.items():
                cipher = Fernet(key)
                # Test encryption/decryption
                test_data = b"test"
                encrypted = cipher.encrypt(test_data)
                decrypted = cipher.decrypt(encrypted)
                if decrypted != test_data:
                    raise EncryptionKeyError(
                        f"Key validation failed for {key_type}: "
                        "Encryption/decryption test failed"
                    )

            return True

        except Exception as e:
            if isinstance(e, EncryptionKeyError):
                raise
            raise EncryptionKeyError(f"Key validation failed: {str(e)}")

    @classmethod
    def reload_keys(cls):
        """
        Force reload of keys from environment
        Useful for testing or key rotation
        """
        cls._keys = None
        cls._load_keys()


# Convenience functions for direct access

def get_confidential_cipher() -> Fernet:
    """Get cipher for confidential data encryption"""
    return KeyManager.get_cipher(KeyManager.CONFIDENTIAL)


def get_ned_team_cipher() -> Fernet:
    """Get cipher for NED team data encryption"""
    return KeyManager.get_cipher(KeyManager.NED_TEAM)


def validate_encryption_keys() -> bool:
    """
    Validate all encryption keys are present and working

    Returns:
        bool: True if valid

    Raises:
        EncryptionKeyError: If validation fails
    """
    return KeyManager.validate_keys()
