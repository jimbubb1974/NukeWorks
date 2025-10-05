"""Read helpers for unified company schema."""
from __future__ import annotations

from sqlalchemy.orm import joinedload

from app import db_session
from app.models import CompanyRoleAssignment, Company

_VENDOR_CONTEXT = 'VendorRecord'
_OWNER_CONTEXT = 'OwnerRecord'
_CLIENT_CONTEXT = 'ClientRecord'
_OPERATOR_CONTEXT = 'OperatorRecord'


def _get_company_for_context(context_type: str, context_id: int) -> Company | None:
    assignment = (
        db_session.query(CompanyRoleAssignment)
        .options(joinedload(CompanyRoleAssignment.company))
        .filter(
            CompanyRoleAssignment.context_type == context_type,
            CompanyRoleAssignment.context_id == context_id,
        )
        .one_or_none()
    )
    return assignment.company if assignment else None


def get_company_for_vendor(vendor_id: int) -> Company | None:
    return _get_company_for_context(_VENDOR_CONTEXT, vendor_id)


def get_company_for_owner(owner_id: int) -> Company | None:
    return _get_company_for_context(_OWNER_CONTEXT, owner_id)


def get_company_for_client(client_id: int) -> Company | None:
    return _get_company_for_context(_CLIENT_CONTEXT, client_id)


def get_company_for_operator(operator_id: int) -> Company | None:
    return _get_company_for_context(_OPERATOR_CONTEXT, operator_id)


__all__ = [
    'get_company_for_vendor',
    'get_company_for_owner',
    'get_company_for_client',
    'get_company_for_operator',
]
