"""
Field-Level Encryption for NukeWorks

Provides encryption utilities with permission-based access control.
Users automatically get access to encrypted data based on their permission flags.

Usage:
    # In models:
    from app.utils.encryption import EncryptedString

    class Project(Base):
        capex = Column(EncryptedString('confidential'))

    # In views/templates:
    from app.utils.encryption import decrypt_for_user

    value = decrypt_for_user(encrypted_data, 'confidential', current_user)
"""

from typing import Optional, Any
from sqlalchemy import LargeBinary, TypeDecorator
from cryptography.fernet import Fernet, InvalidToken
from app.utils.key_management import KeyManager
from app.exceptions import DecryptionError, InsufficientPermissionsError


# =============================================================================
# CORE ENCRYPTION FUNCTIONS
# =============================================================================

def encrypt_value(value: Any, key_type: str) -> bytes:
    """
    Encrypt a value with the specified key type

    Args:
        value: Value to encrypt (will be converted to string)
        key_type: 'confidential' or 'ned_team'

    Returns:
        bytes: Encrypted data

    Raises:
        EncryptionKeyError: If key is invalid
    """
    if value is None:
        return None

    # Convert to string and encode
    value_str = str(value)
    value_bytes = value_str.encode('utf-8')

    # Get cipher and encrypt
    cipher = KeyManager.get_cipher(key_type)
    encrypted = cipher.encrypt(value_bytes)

    return encrypted


def decrypt_value(encrypted_data: bytes, key_type: str) -> Optional[str]:
    """
    Decrypt data with the specified key type

    Args:
        encrypted_data: Encrypted bytes
        key_type: 'confidential' or 'ned_team'

    Returns:
        str: Decrypted value, or None if data is None

    Raises:
        DecryptionError: If decryption fails
        EncryptionKeyError: If key is invalid
    """
    if encrypted_data is None:
        return None

    try:
        cipher = KeyManager.get_cipher(key_type)
        decrypted_bytes = cipher.decrypt(encrypted_data)
        return decrypted_bytes.decode('utf-8')

    except InvalidToken:
        raise DecryptionError(
            f"Failed to decrypt data with {key_type} key. "
            "Data may be corrupted or encrypted with a different key."
        )
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {str(e)}")


def decrypt_for_user(
    encrypted_data: bytes,
    key_type: str,
    user,
    redaction_message: str = "[Confidential]"
) -> str:
    """
    Decrypt data for a user if they have permission
    Automatically checks user permissions and returns redaction message if unauthorized

    Args:
        encrypted_data: Encrypted bytes
        key_type: 'confidential' or 'ned_team'
        user: User object with permission flags
        redaction_message: Message to show if user lacks permission

    Returns:
        str: Decrypted value if authorized, redaction message otherwise
    """
    if encrypted_data is None:
        return None

    # Check if user has permission for this key type
    if not KeyManager.user_can_access_key(user, key_type):
        return redaction_message

    # User has permission - decrypt
    try:
        return decrypt_value(encrypted_data, key_type)
    except DecryptionError:
        # If decryption fails, show error message
        return "[Decryption Error]"


# =============================================================================
# SQLALCHEMY ENCRYPTED COLUMN TYPES
# =============================================================================

class EncryptedString(TypeDecorator):
    """
    SQLAlchemy column type that automatically encrypts/decrypts string data

    Usage:
        class Project(Base):
            capex = Column(EncryptedString('confidential'))
            internal_notes = Column(EncryptedString('ned_team'))

    The column will:
    - Store encrypted bytes in the database (LargeBinary)
    - Automatically encrypt when setting values
    - Return encrypted bytes when reading (decrypt in your property)
    """

    impl = LargeBinary
    cache_ok = True

    def __init__(self, key_type: str = 'confidential', *args, **kwargs):
        """
        Initialize encrypted column

        Args:
            key_type: 'confidential' or 'ned_team'
        """
        self.key_type = key_type
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        """
        Encrypt value when saving to database

        Args:
            value: Value to encrypt
            dialect: SQLAlchemy dialect (unused)

        Returns:
            bytes: Encrypted data
        """
        if value is None:
            return None

        return encrypt_value(value, self.key_type)

    def process_result_value(self, value, dialect):
        """
        Return encrypted bytes when reading from database
        NOTE: Does NOT automatically decrypt - use property for that

        Args:
            value: Encrypted bytes from database
            dialect: SQLAlchemy dialect (unused)

        Returns:
            bytes: Encrypted data (still encrypted!)
        """
        # Return encrypted bytes as-is
        # Decryption happens in the model's @property
        return value


class EncryptedText(EncryptedString):
    """
    Alias for EncryptedString for semantic clarity
    Use for longer text fields like notes
    """
    pass


# =============================================================================
# PERMISSION-BASED ENCRYPTION HELPERS
# =============================================================================

class PermissionBasedEncryption:
    """
    Helper class for permission-based encryption/decryption
    Automatically grants/denies access based on user permissions
    """

    @staticmethod
    def encrypt_field(value: Any, key_type: str) -> bytes:
        """
        Encrypt a field value

        Args:
            value: Value to encrypt
            key_type: 'confidential' or 'ned_team'

        Returns:
            bytes: Encrypted data
        """
        return encrypt_value(value, key_type)

    @staticmethod
    def decrypt_field_for_user(
        encrypted_data: bytes,
        key_type: str,
        user,
        redaction_message: str = "[Confidential]"
    ) -> str:
        """
        Decrypt field for user with automatic permission checking

        Args:
            encrypted_data: Encrypted bytes
            key_type: 'confidential' or 'ned_team'
            user: User object
            redaction_message: Message if no permission

        Returns:
            str: Decrypted value or redaction message
        """
        return decrypt_for_user(encrypted_data, key_type, user, redaction_message)

    @staticmethod
    def get_user_key_access(user) -> dict:
        """
        Get summary of which keys a user can access

        Args:
            user: User object

        Returns:
            dict: {key_type: bool} indicating access
        """
        if not user or not user.is_authenticated:
            return {
                'confidential': False,
                'ned_team': False
            }

        return {
            'confidential': KeyManager.user_can_access_key(user, KeyManager.CONFIDENTIAL),
            'ned_team': KeyManager.user_can_access_key(user, KeyManager.NED_TEAM),
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def encrypt_confidential(value: Any) -> bytes:
    """Encrypt value as confidential data"""
    return encrypt_value(value, KeyManager.CONFIDENTIAL)


def encrypt_ned_team(value: Any) -> bytes:
    """Encrypt value as NED team data"""
    return encrypt_value(value, KeyManager.NED_TEAM)


def decrypt_confidential(encrypted_data: bytes) -> str:
    """Decrypt confidential data (no permission check)"""
    return decrypt_value(encrypted_data, KeyManager.CONFIDENTIAL)


def decrypt_ned_team(encrypted_data: bytes) -> str:
    """Decrypt NED team data (no permission check)"""
    return decrypt_value(encrypted_data, KeyManager.NED_TEAM)


# =============================================================================
# FIELD DESCRIPTOR FOR MODELS
# =============================================================================

class EncryptedField:
    """
    Property descriptor for encrypted fields in SQLAlchemy models
    Provides automatic encryption/decryption with permission checking

    Usage:
        class Project(Base):
            _capex_encrypted = Column(LargeBinary)
            capex = EncryptedField('_capex_encrypted', 'confidential')

    When accessed:
        project.capex  # Automatically decrypts for current_user
    """

    def __init__(self, encrypted_column_name: str, key_type: str, redaction_message: str = "[Confidential]"):
        """
        Initialize encrypted field descriptor

        Args:
            encrypted_column_name: Name of the column storing encrypted data
            key_type: 'confidential' or 'ned_team'
            redaction_message: Message to show when user lacks permission
        """
        self.encrypted_column_name = encrypted_column_name
        self.key_type = key_type
        self.redaction_message = redaction_message

    def __get__(self, obj, objtype=None):
        """Get decrypted value (with permission check and per-field confidentiality flags)"""
        if obj is None:
            return self

        encrypted_data = getattr(obj, self.encrypted_column_name)

        # If no data, return None
        if encrypted_data is None:
            return None

        # Get current user from flask context
        try:
            from flask_login import current_user
            if not current_user or not current_user.is_authenticated:
                return self.redaction_message
        except:
            # If not in flask context, return redacted
            return self.redaction_message

        # Check per-field confidentiality flag (Option 2 implementation)
        # If field is NOT flagged as confidential, show to everyone (no permission check)
        # If field IS flagged as confidential, check user permission
        try:
            from app.utils.permissions import can_view_field

            # Determine table and field name from the object
            table_name = obj.__tablename__ if hasattr(obj, '__tablename__') else None
            record_id = None

            # Try to get primary key value
            if hasattr(obj, 'project_id'):
                record_id = obj.project_id
                table_name = 'projects'
            elif hasattr(obj, 'company_id'):
                record_id = obj.company_id
                table_name = 'companies'
            elif hasattr(obj, 'history_id'):
                record_id = obj.history_id
                table_name = 'roundtable_history'

            # Get field name (strip '_encrypted' suffix from column name)
            # For column name like '_capex_encrypted', we want 'capex'
            field_name = self.encrypted_column_name.lstrip('_').replace('_encrypted', '')

            # Check if field is confidential and if user can view it
            if table_name and record_id and field_name:
                try:
                    can_view = can_view_field(current_user, table_name, record_id, field_name)

                    if not can_view:
                        # User doesn't have permission for this specific field
                        return self.redaction_message

                    # User has permission for this field (either not flagged or user has access)
                    # Decrypt directly without re-checking key permissions
                    # This allows public fields to be visible to all authenticated users
                    cipher = KeyManager.get_cipher(self.key_type)
                    decrypted_bytes = cipher.decrypt(encrypted_data)
                    return decrypted_bytes.decode('utf-8')
                except DecryptionError:
                    return "[Decryption Error]"
                except InvalidToken:
                    return "[Decryption Error]"
        except Exception as e:
            # If permission check fails, fall back to key-based permission
            # This handles cases where per-field flags aren't set up yet
            pass

        # Fall back to key-based permission check for backward compatibility
        return decrypt_for_user(
            encrypted_data,
            self.key_type,
            current_user,
            self.redaction_message
        )

    def __set__(self, obj, value):
        """Set value (automatically encrypts)"""
        if value is None:
            setattr(obj, self.encrypted_column_name, None)
        else:
            encrypted = encrypt_value(value, self.key_type)
            setattr(obj, self.encrypted_column_name, encrypted)
