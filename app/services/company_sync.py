"""Utilities to synchronize legacy role-specific records into the unified company schema."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_

from app import db_session
from app.models import (
    Company,
    CompanyRole,
    CompanyRoleAssignment,
    ClientProfile,
    TechnologyVendor,
    OwnerDeveloper,
    Client,
)

_VENDOR_ROLE_CODE = 'vendor'
_VENDOR_ROLE_LABEL = 'Technology Vendor'
_VENDOR_CONTEXT = 'VendorRecord'

_OWNER_ROLE_CODE = 'developer'
_OWNER_ROLE_LABEL = 'Owner / Developer'
_OWNER_CONTEXT = 'OwnerRecord'

_CLIENT_ROLE_CODE = 'client'
_CLIENT_ROLE_LABEL = 'MPR Client'
_CLIENT_CONTEXT = 'ClientRecord'


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


def _get_assignment(company_id: int, role_id: int, context_type: str, context_id: int) -> CompanyRoleAssignment | None:
    return (
        db_session.query(CompanyRoleAssignment)
        .filter(
            and_(
                CompanyRoleAssignment.company_id == company_id,
                CompanyRoleAssignment.role_id == role_id,
                CompanyRoleAssignment.context_type == context_type,
                CompanyRoleAssignment.context_id == context_id,
            )
        )
        .one_or_none()
    )


def _get_assignment_by_context(role_id: int, context_type: str, context_id: int) -> CompanyRoleAssignment | None:
    return (
        db_session.query(CompanyRoleAssignment)
        .filter(
            and_(
                CompanyRoleAssignment.role_id == role_id,
                CompanyRoleAssignment.context_type == context_type,
                CompanyRoleAssignment.context_id == context_id,
            )
        )
        .one_or_none()
    )


def _sync_company_name_and_notes(
    company: Company,
    name: str,
    notes: str | None,
    user_id: int | None,
    *,
    force_notes: bool = False,
) -> None:
    fields_updated = False

    if company.company_name != name:
        company.company_name = name
        fields_updated = True

    if notes and (force_notes or notes != company.notes):
        company.notes = notes
        fields_updated = True

    if fields_updated:
        company.modified_by = user_id
        company.modified_date = datetime.utcnow()


def sync_company_from_vendor(vendor: TechnologyVendor, user_id: int | None = None) -> Company:
    """Ensure a Company + vendor role assignment exists for the given vendor."""
    role = _get_or_create_role(
        _VENDOR_ROLE_CODE,
        _VENDOR_ROLE_LABEL,
        'Company that develops or supplies nuclear technology',
        user_id=user_id,
    )

    assignment = _get_assignment_by_context(role.role_id, _VENDOR_CONTEXT, vendor.vendor_id)

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
        db_session.flush()

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

    _sync_company_name_and_notes(company, vendor.vendor_name, vendor.notes, user_id)
    db_session.flush()
    return company


def sync_company_from_owner(owner: OwnerDeveloper, user_id: int | None = None) -> Company:
    """Ensure a Company record exists for an owner/developer and sync key fields."""
    role = _get_or_create_role(
        _OWNER_ROLE_CODE,
        _OWNER_ROLE_LABEL,
        'Company that owns or develops nuclear projects',
        user_id=user_id,
    )

    assignment = _get_assignment_by_context(role.role_id, _OWNER_CONTEXT, owner.owner_id)

    if assignment:
        company = assignment.company
    else:
        company = Company(
            company_name=owner.company_name,
            company_type=owner.company_type or 'Owner/Developer',
            notes=owner.notes,
            is_mpr_client=False,
            is_internal=False,
            created_by=user_id,
            modified_by=user_id,
        )
        db_session.add(company)
        db_session.flush()

        assignment = CompanyRoleAssignment(
            company_id=company.company_id,
            role_id=role.role_id,
            context_type=_OWNER_CONTEXT,
            context_id=owner.owner_id,
            is_primary=True,
            created_by=user_id,
            modified_by=user_id,
        )
        db_session.add(assignment)

    company.company_type = owner.company_type or company.company_type
    _sync_company_name_and_notes(company, owner.company_name, owner.notes, user_id)
    db_session.flush()
    return company


def sync_company_from_client(client: Client, user_id: int | None = None) -> Company:
    """Ensure a Company and ClientProfile exist for a CRM client."""
    role = _get_or_create_role(
        _CLIENT_ROLE_CODE,
        _CLIENT_ROLE_LABEL,
        'Company engaging MPR for consulting services',
        user_id=user_id,
    )

    assignment = _get_assignment_by_context(role.role_id, _CLIENT_CONTEXT, client.client_id)

    if assignment:
        company = assignment.company
    else:
        company = Company(
            company_name=client.client_name,
            company_type=client.client_type or 'Client',
            notes=client.notes,
            is_mpr_client=True,
            is_internal=False,
            created_by=user_id,
            modified_by=user_id,
        )
        db_session.add(company)
        db_session.flush()

        assignment = CompanyRoleAssignment(
            company_id=company.company_id,
            role_id=role.role_id,
            context_type=_CLIENT_CONTEXT,
            context_id=client.client_id,
            is_primary=True,
            created_by=user_id,
            modified_by=user_id,
        )
        db_session.add(assignment)

    company.company_type = client.client_type or company.company_type
    company.is_mpr_client = True
    _sync_company_name_and_notes(company, client.client_name, client.notes, user_id, force_notes=True)

    profile = db_session.get(ClientProfile, company.company_id)
    if profile is None:
        profile = ClientProfile(
            company_id=company.company_id,
            created_by=user_id,
            modified_by=user_id,
        )
        db_session.add(profile)

    profile.relationship_strength = client.relationship_strength
    profile.relationship_notes = client.relationship_notes
    profile.client_priority = client.client_priority
    profile.client_status = client.client_status
    profile.last_contact_date = client.last_contact_date
    profile.last_contact_type = client.last_contact_type
    profile.last_contact_by = client.last_contact_by
    profile.next_planned_contact_date = client.next_planned_contact_date
    profile.next_planned_contact_type = client.next_planned_contact_type
    profile.next_planned_contact_assigned_to = client.next_planned_contact_assigned_to
    profile.modified_by = user_id
    profile.modified_date = datetime.utcnow()

    db_session.flush()
    return company


__all__ = ['sync_company_from_vendor', 'sync_company_from_owner', 'sync_company_from_client']
