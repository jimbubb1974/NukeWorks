"""
Custom exceptions for NukeWorks application
"""


class NukeWorksException(Exception):
    """Base exception for all NukeWorks errors"""
    pass


class ConcurrentModificationError(NukeWorksException):
    """Raised when concurrent modification is detected (optimistic locking)"""
    pass


class PermissionDeniedError(NukeWorksException):
    """Raised when user attempts unauthorized action"""
    pass


class ValidationError(NukeWorksException):
    """Raised when data validation fails"""
    pass


class DatabaseError(NukeWorksException):
    """Raised when database operation fails"""
    pass


class SnapshotError(NukeWorksException):
    """Raised when snapshot operation fails"""
    pass


class MigrationError(NukeWorksException):
    """Raised when database migration fails"""
    pass
