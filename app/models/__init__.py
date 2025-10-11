"""
NukeWorks Database Models
All SQLAlchemy models for the application
"""
from .base import Base, TimestampMixin
from .user import User
from .company import (
    Company,
    CompanyRole,
    CompanyRoleAssignment,
    ClientProfile,
    PersonCompanyAffiliation,
    InternalExternalLink,
)
from .project import Project
from .personnel import Personnel
from .internal_personnel import InternalPersonnel
from .external_personnel import ExternalPersonnel
from .personnel_relationships import PersonnelRelationship
from .contact import ContactLog
from .roundtable import RoundtableHistory
from .confidential import ConfidentialFieldFlag
from .audit import AuditLog
from .snapshot import DatabaseSnapshot
from .system import SystemSetting, SchemaVersion

# Legacy imports removed in Phase 4 cleanup (2025-10-10):
# - TechnologyVendor, Product (from vendor.py)
# - OwnerDeveloper (from owner.py)
# - Constructor, Operator, Offtaker (from constructor.py, operator.py, offtaker.py)
# - Client (from client.py)
# - All legacy relationship models from relationships.py

__all__ = [
    'Base',
    'TimestampMixin',
    'User',
    'Company',
    'CompanyRole',
    'CompanyRoleAssignment',
    'ClientProfile',
    'PersonCompanyAffiliation',
    'InternalExternalLink',
    'Project',
    'Personnel',
    'InternalPersonnel',
    'ExternalPersonnel',
    'PersonnelRelationship',
    'ContactLog',
    'RoundtableHistory',
    'ConfidentialFieldFlag',
    'AuditLog',
    'DatabaseSnapshot',
    'SystemSetting',
    'SchemaVersion',
]
