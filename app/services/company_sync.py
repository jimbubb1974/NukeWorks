"""Utilities to synchronize legacy role-specific records into the unified company schema."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_

from app import db_session
from app.models import Company, CompanyRole, CompanyRoleAssignment, TechnologyVendor

_VENDOR_ROLE_CODE = 'vendor'
_VENDOR_ROLE_LABEL = 'Technology Vendor'
_VENDOR_CONTEXT = 'VendorRecord'


def _get_or_create_role(code: str, label: str, description: str | None, user_id: int | None = None) -> CompanyRole:
    """Return an existing CompanyRole or create it if missing."""
    role = db_session.query(CompanyRole).filter(CompanyRole.role_code == code).one_or_none()
    if role:
        return role

    role = CompanyRole(
        role_code=code,
        role_label=label,
        description=description,
        is_active=True,
        created_by=user_id,
        modified_by=user_id,
    )
    db_session.add(role)
    db_session.flush()
    return role


def _get_assignment_for_vendor(vendor_id: int, role_id: int) -> CompanyRoleAssignment | None:
    return (
        db_session.query(CompanyRoleAssignment)
        .filter(
            and_(
                CompanyRoleAssignment.role_id == role_id,
                CompanyRoleAssignment.context_type == _VENDOR_CONTEXT,
                CompanyRoleAssignment.context_id == vendor_id,
            )
        )
        .one_or_none()
    )


def sync_company_from_vendor(vendor: TechnologyVendor, user_id: int | None = None) -> Company:
    """Ensure a Company + role assignment exists for the given vendor and sync core fields.

    Args:
        vendor: Legacy TechnologyVendor record.
        user_id: Optional user performing the sync for audit fields.

    Returns:
        Company instance linked to the vendor.
    """
    role = _get_or_create_role(
        _VENDOR_ROLE_CODE,
        _VENDOR_ROLE_LABEL,
        'Company that develops or supplies nuclear technology',
        user_id=user_id,
    )

    assignment = _get_assignment_for_vendor(vendor.vendor_id, role.role_id)

    if assignment:
        company = assignment.company
    else:
        company = Company(
            company_name=vendor.vendor_name,
            company_type='Vendor',
            notes=vendor.notes,
            is_mpr_client=False,
            is_internal=False,
            created_by=user_id,
            modified_by=user_id,
        )
        db_session.add(company)
        db_session.flush()  # acquire company_id for assignment

        assignment = CompanyRoleAssignment(
            company_id=company.company_id,
            role_id=role.role_id,
            context_type=_VENDOR_CONTEXT,
            context_id=vendor.vendor_id,
            is_primary=True,
            created_by=user_id,
            modified_by=user_id,
        )
        db_session.add(assignment)

    # Update company fields if the legacy record changed
    fields_updated = False

    if company.company_name != vendor.vendor_name:
        company.company_name = vendor.vendor_name
        fields_updated = True

    # Only update notes if vendor provides a value; avoid overwriting richer company notes with empty text
    if vendor.notes and vendor.notes != company.notes:
        company.notes = vendor.notes
        fields_updated = True

    if fields_updated:
        company.modified_by = user_id
        company.modified_date = datetime.utcnow()

    db_session.flush()
    return company


__all__ = ['sync_company_from_vendor']
