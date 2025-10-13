"""Read helpers for unified company schema.

DEPRECATED: These lookup functions are deprecated as of migration 010.
All CompanyRoleAssignments now use 'Global' or 'Project' context types.
The legacy *Record context types no longer exist in the database.

These functions will be removed in Phase 4 when legacy tables are dropped.
Use direct company lookups via company_id instead.
"""
from __future__ import annotations

import warnings
from sqlalchemy.orm import joinedload

from app import db_session
from app.models import CompanyRoleAssignment, Company

# DEPRECATED: These context types no longer exist after migration 010
_VENDOR_CONTEXT = 'VendorRecord'
_OWNER_CONTEXT = 'OwnerRecord'
_CLIENT_CONTEXT = 'ClientRecord'
_OPERATOR_CONTEXT = 'OperatorRecord'
_CONSTRUCTOR_CONTEXT = 'ConstructorRecord'
_OFFTAKER_CONTEXT = 'OfftakerRecord'


def _get_company_for_context(context_type: str, context_id: int) -> Company | None:
    """DEPRECATED: Context types were normalized to Global in migration 010.

    This function will always return None as legacy context types no longer exist.
    Will be removed in Phase 4 of legacy cleanup.
    """
    warnings.warn(
        f"_get_company_for_context is deprecated. Legacy context type '{context_type}' "
        "no longer exists. Use direct company lookups instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Legacy context types no longer exist after migration 010
    # All assignments are now 'Global' or 'Project'
    return None


def get_company_for_vendor(vendor_id: int) -> Company | None:
    """DEPRECATED: Returns None. Use direct company lookup instead."""
    return _get_company_for_context(_VENDOR_CONTEXT, vendor_id)


def get_company_for_owner(owner_id: int) -> Company | None:
    """DEPRECATED: Returns None. Use direct company lookup instead."""
    return _get_company_for_context(_OWNER_CONTEXT, owner_id)


def get_company_for_client(client_id: int) -> Company | None:
    """DEPRECATED: Returns None. Use direct company lookup instead."""
    return _get_company_for_context(_CLIENT_CONTEXT, client_id)


def get_company_for_operator(operator_id: int) -> Company | None:
    """DEPRECATED: Returns None. Use direct company lookup instead."""
    return _get_company_for_context(_OPERATOR_CONTEXT, operator_id)


def get_company_for_constructor(constructor_id: int) -> Company | None:
    """DEPRECATED: Returns None. Use direct company lookup instead."""
    return _get_company_for_context(_CONSTRUCTOR_CONTEXT, constructor_id)


def get_company_for_offtaker(offtaker_id: int) -> Company | None:
    """DEPRECATED: Returns None. Use direct company lookup instead."""
    return _get_company_for_context(_OFFTAKER_CONTEXT, offtaker_id)


__all__ = [
    'get_company_for_vendor',
    'get_company_for_owner',
    'get_company_for_client',
    'get_company_for_operator',
    'get_company_for_constructor',
    'get_company_for_offtaker',
]
