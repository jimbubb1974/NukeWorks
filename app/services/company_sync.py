"""Utilities to synchronize legacy role-specific records into the unified company schema.

PARTIALLY DEPRECATED: As of migration 010, all CompanyRoleAssignments use 'Global'
or 'Project' context types. The *Record context types no longer exist.

The sync functions still work for creating/updating Company records from legacy tables,
but they now create assignments with context_type='Global' instead of legacy types.

These functions will be removed in Phase 4 when legacy tables are dropped.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_

from flask import current_app

import app as app_module

# DEPRECATED FILE: This entire file will be removed once legacy tables are dropped.
# The sync functions below attempt to import legacy models that no longer exist.
# Keeping file temporarily to avoid breaking backfill scripts.

try:
    from app.models import (
        Company,
        CompanyRole,
        CompanyRoleAssignment,
        ClientProfile,
        PersonCompanyAffiliation,
    )
    # Legacy models no longer exported from app.models as of Phase 4
    # These imports will fail but are wrapped in try/except for graceful degradation
    from app.models.vendor import TechnologyVendor
    from app.models.owner import OwnerDeveloper
    from app.models.client import Client
    from app.models.operator import Operator
    from app.models.constructor import Constructor
    from app.models.offtaker import Offtaker
    from app.models.relationships import (
        PersonnelEntityRelationship,
        ProjectVendorRelationship,
        ProjectConstructorRelationship,
        ProjectOperatorRelationship,
        ProjectOwnerRelationship,
        ProjectOfftakerRelationship,
    )
except ImportError as e:
    # Expected after legacy model files are deleted
    import warnings
    warnings.warn(f"company_sync.py: Legacy model imports failed: {e}. This file should be deleted.", DeprecationWarning)

_VENDOR_ROLE_CODE = 'vendor'
_VENDOR_ROLE_LABEL = 'Technology Vendor'
_VENDOR_CONTEXT = 'Global'  # Changed from 'VendorRecord' in migration 010

_OWNER_ROLE_CODE = 'developer'
_OWNER_ROLE_LABEL = 'Owner / Developer'
_OWNER_CONTEXT = 'Global'  # Changed from 'OwnerRecord' in migration 010

_CLIENT_ROLE_CODE = 'client'
_CLIENT_ROLE_LABEL = 'MPR Client'
_CLIENT_CONTEXT = 'Global'  # Changed from 'ClientRecord' in migration 010

_OPERATOR_ROLE_CODE = 'operator'
_OPERATOR_ROLE_LABEL = 'Operator'
_OPERATOR_CONTEXT = 'Global'  # Changed from 'OperatorRecord' in migration 010

_CONSTRUCTOR_ROLE_CODE = 'constructor'
_CONSTRUCTOR_ROLE_LABEL = 'Constructor'
_CONSTRUCTOR_CONTEXT = 'Global'  # Changed from 'ConstructorRecord' in migration 010

_OFFTAKER_ROLE_CODE = 'offtaker'
_OFFTAKER_ROLE_LABEL = 'Off-taker'
_OFFTAKER_CONTEXT = 'Global'  # Changed from 'OfftakerRecord' in migration 010

def _session():
    try:
        return current_app.db_session  # type: ignore[attr-defined]
    except RuntimeError:
        return app_module.db_session


def _find_company_by_name(name: str) -> Company | None:
    session = _session()
    return session.query(Company).filter(Company.company_name == name).one_or_none()


def _get_or_create_role(code: str, label: str, description: str | None, user_id: int | None = None) -> CompanyRole:
    """Return an existing CompanyRole or create it if missing."""
    session = _session()
    role = session.query(CompanyRole).filter(CompanyRole.role_code == code).one_or_none()
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
    session.add(role)
    session.flush()
    return role


def _get_assignment_for_vendor(vendor_id: int, role_id: int) -> CompanyRoleAssignment | None:
    session = _session()
    return (
        session.query(CompanyRoleAssignment)
        .filter(
            and_(
                CompanyRoleAssignment.role_id == role_id,
                CompanyRoleAssignment.context_type == _VENDOR_CONTEXT,
                CompanyRoleAssignment.context_id == vendor_id,
            )
        )
        .one_or_none()
    )


def _get_assignment(company_id: int, role_id: int, context_type: str, context_id: int | None) -> CompanyRoleAssignment | None:
    """Get assignment for company/role/context. After migration 010, context_id should be None for Global."""
    session = _session()
    filters = [
        CompanyRoleAssignment.company_id == company_id,
        CompanyRoleAssignment.role_id == role_id,
        CompanyRoleAssignment.context_type == context_type,
    ]

    if context_id is None:
        filters.append(CompanyRoleAssignment.context_id.is_(None))
    else:
        filters.append(CompanyRoleAssignment.context_id == context_id)

    return (
        session.query(CompanyRoleAssignment)
        .filter(and_(*filters))
        .one_or_none()
    )


def _get_assignment_by_context(role_id: int, context_type: str, context_id: int | None) -> CompanyRoleAssignment | None:
    """Get assignment by context. After migration 010, context_id should be None for Global context."""
    session = _session()
    filters = [
        CompanyRoleAssignment.role_id == role_id,
        CompanyRoleAssignment.context_type == context_type,
    ]

    if context_id is None:
        filters.append(CompanyRoleAssignment.context_id.is_(None))
    else:
        filters.append(CompanyRoleAssignment.context_id == context_id)

    return (
        session.query(CompanyRoleAssignment)
        .filter(and_(*filters))
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

    session = _session()

    # After migration 010: Look up company directly by name instead of by assignment
    company = _find_company_by_name(vendor.vendor_name)
    if company is None:
        company = Company(
            company_name=vendor.vendor_name,
            company_type='Vendor',
            notes=vendor.notes,
            is_mpr_client=False,
            is_internal=False,
            created_by=user_id,
            modified_by=user_id,
        )
        session.add(company)
        session.flush()

    # Check if Global assignment already exists for this company/role
    existing_assignment = _get_assignment(company.company_id, role.role_id, _VENDOR_CONTEXT, None)
    if not existing_assignment:
        assignment = CompanyRoleAssignment(
            company_id=company.company_id,
            role_id=role.role_id,
            context_type=_VENDOR_CONTEXT,
            context_id=None,  # Global context after migration 010
            is_primary=True,
            created_by=user_id,
            modified_by=user_id,
        )
        session.add(assignment)

    _sync_company_name_and_notes(company, vendor.vendor_name, vendor.notes, user_id)
    session.flush()
    return company


def sync_company_from_owner(owner: OwnerDeveloper, user_id: int | None = None) -> Company:
    """Ensure a Company record exists for an owner/developer and sync key fields."""
    role = _get_or_create_role(
        _OWNER_ROLE_CODE,
        _OWNER_ROLE_LABEL,
        'Company that owns or develops nuclear projects',
        user_id=user_id,
    )

    session = _session()
    # NOTE: After migration 010, this will find any Global assignment for this role
    # Multiple companies may have the same role, so we rely on company name lookup below
    assignment = _get_assignment_by_context(role.role_id, _OWNER_CONTEXT, None)

    if assignment:
        company = assignment.company
    else:
        company = _find_company_by_name(owner.company_name)
        if company is None:
            company = Company(
                company_name=owner.company_name,
                company_type=owner.company_type or 'Owner/Developer',
                notes=owner.notes,
                is_mpr_client=False,
                is_internal=False,
                created_by=user_id,
                modified_by=user_id,
            )
            session.add(company)
            session.flush()

        assignment = CompanyRoleAssignment(
            company_id=company.company_id,
            role_id=role.role_id,
            context_type=_OWNER_CONTEXT,
            context_id=None,  # Global context after migration 010
            is_primary=True,
            created_by=user_id,
            modified_by=user_id,
        )
        session.add(assignment)

    company.company_type = owner.company_type or company.company_type
    _sync_company_name_and_notes(company, owner.company_name, owner.notes, user_id)
    session.flush()
    return company


def sync_company_from_client(client: Client, user_id: int | None = None) -> Company:
    """Ensure a Company and ClientProfile exist for a CRM client."""
    role = _get_or_create_role(
        _CLIENT_ROLE_CODE,
        _CLIENT_ROLE_LABEL,
        'Company engaging MPR for consulting services',
        user_id=user_id,
    )

    session = _session()
    assignment = _get_assignment_by_context(role.role_id, _CLIENT_CONTEXT, client.client_id)

    if assignment:
        company = assignment.company
    else:
        company = _find_company_by_name(client.client_name)
        if company is None:
            company = Company(
                company_name=client.client_name,
                company_type=client.client_type or 'Client',
                notes=client.notes,
                is_mpr_client=True,
                is_internal=False,
                created_by=user_id,
                modified_by=user_id,
            )
            session.add(company)
            session.flush()

        assignment = CompanyRoleAssignment(
            company_id=company.company_id,
            role_id=role.role_id,
            context_type=_CLIENT_CONTEXT,
            context_id=None,  # Global context after migration 010
            is_primary=True,
            created_by=user_id,
            modified_by=user_id,
        )
        session.add(assignment)

    company.company_type = client.client_type or company.company_type
    company.is_mpr_client = True
    _sync_company_name_and_notes(company, client.client_name, client.notes, user_id, force_notes=True)

    profile = session.get(ClientProfile, company.company_id)
    if profile is None:
        profile = ClientProfile(
            company_id=company.company_id,
            created_by=user_id,
            modified_by=user_id,
        )
        session.add(profile)

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

    session.flush()
    return company


def sync_company_from_operator(operator: Operator, user_id: int | None = None) -> Company:
    """Ensure an operator record is represented in the unified company table."""
    role = _get_or_create_role(
        _OPERATOR_ROLE_CODE,
        _OPERATOR_ROLE_LABEL,
        'Company that operates nuclear facilities',
        user_id=user_id,
    )

    session = _session()
    assignment = _get_assignment_by_context(role.role_id, _OPERATOR_CONTEXT, operator.operator_id)

    if assignment:
        company = assignment.company
    else:
        company = _find_company_by_name(operator.company_name)
        if company is None:
            company = Company(
                company_name=operator.company_name,
                company_type='Operator',
                notes=operator.notes,
                is_mpr_client=False,
                is_internal=False,
                created_by=user_id,
                modified_by=user_id,
            )
            session.add(company)
            session.flush()

        assignment = CompanyRoleAssignment(
            company_id=company.company_id,
            role_id=role.role_id,
            context_type=_OPERATOR_CONTEXT,
            context_id=None,  # Global context after migration 010
            is_primary=True,
            created_by=user_id,
            modified_by=user_id,
        )
        session.add(assignment)

    _sync_company_name_and_notes(company, operator.company_name, operator.notes, user_id)
    session.flush()
    return company


def sync_company_from_constructor(constructor: Constructor, user_id: int | None = None) -> Company:
    """Ensure constructor records map into the unified company schema."""
    role = _get_or_create_role(
        _CONSTRUCTOR_ROLE_CODE,
        _CONSTRUCTOR_ROLE_LABEL,
        'Company providing EPC or construction services',
        user_id=user_id,
    )

    session = _session()
    assignment = _get_assignment_by_context(role.role_id, _CONSTRUCTOR_CONTEXT, constructor.constructor_id)

    if assignment:
        company = assignment.company
    else:
        company = _find_company_by_name(constructor.company_name)
        if company is None:
            company = Company(
                company_name=constructor.company_name,
                company_type='Constructor',
                notes=constructor.notes,
                is_mpr_client=False,
                is_internal=False,
                created_by=user_id,
                modified_by=user_id,
            )
            session.add(company)
            session.flush()

        assignment = CompanyRoleAssignment(
            company_id=company.company_id,
            role_id=role.role_id,
            context_type=_CONSTRUCTOR_CONTEXT,
            context_id=None,  # Global context after migration 010
            is_primary=True,
            created_by=user_id,
            modified_by=user_id,
        )
        session.add(assignment)

    _sync_company_name_and_notes(company, constructor.company_name, constructor.notes, user_id)
    session.flush()
    return company


def sync_company_from_offtaker(offtaker: Offtaker, user_id: int | None = None) -> Company:
    """Ensure off-takers are represented in the unified company table."""
    role = _get_or_create_role(
        _OFFTAKER_ROLE_CODE,
        _OFFTAKER_ROLE_LABEL,
        'Organization purchasing energy output',
        user_id=user_id,
    )

    session = _session()
    assignment = _get_assignment_by_context(role.role_id, _OFFTAKER_CONTEXT, offtaker.offtaker_id)

    if assignment:
        company = assignment.company
    else:
        company = _find_company_by_name(offtaker.organization_name)
        if company is None:
            company = Company(
                company_name=offtaker.organization_name,
                company_type=offtaker.sector or 'Off-taker',
                notes=offtaker.notes,
                is_mpr_client=False,
                is_internal=False,
                created_by=user_id,
                modified_by=user_id,
            )
            session.add(company)
            session.flush()

        assignment = CompanyRoleAssignment(
            company_id=company.company_id,
            role_id=role.role_id,
            context_type=_OFFTAKER_CONTEXT,
            context_id=None,  # Global context after migration 010
            is_primary=True,
            created_by=user_id,
            modified_by=user_id,
        )
        session.add(assignment)

    company.company_type = offtaker.sector or company.company_type
    _sync_company_name_and_notes(company, offtaker.organization_name, offtaker.notes, user_id)
    session.flush()
    return company


def _get_company_for_entity(entity_type: str, entity_id: int) -> Company | None:
    """
    Find the unified Company record linked to a legacy entity.

    Args:
        entity_type: Entity type from PersonnelEntityRelationship (Vendor, Owner, Operator, etc.)
        entity_id: The legacy entity's primary key

    Returns:
        Company record if found, None otherwise
    """
    session = _session()

    # Map entity types to context types and role codes
    entity_map = {
        'Vendor': (_VENDOR_CONTEXT, _VENDOR_ROLE_CODE),
        'Owner': (_OWNER_CONTEXT, _OWNER_ROLE_CODE),
        'Developer': (_OWNER_CONTEXT, _OWNER_ROLE_CODE),
        'Operator': (_OPERATOR_CONTEXT, _OPERATOR_ROLE_CODE),
        'Constructor': (_CONSTRUCTOR_CONTEXT, _CONSTRUCTOR_ROLE_CODE),
        'Offtaker': (_OFFTAKER_CONTEXT, _OFFTAKER_ROLE_CODE),
        'Client': (_CLIENT_CONTEXT, _CLIENT_ROLE_CODE),
    }

    if entity_type not in entity_map:
        return None

    context_type, role_code = entity_map[entity_type]

    # Get the role
    role = session.query(CompanyRole).filter(CompanyRole.role_code == role_code).one_or_none()
    if not role:
        return None

    # Find the assignment linking to this entity
    assignment = _get_assignment_by_context(role.role_id, context_type, entity_id)
    if assignment:
        return assignment.company

    return None


def sync_personnel_affiliation(
    personnel_rel: PersonnelEntityRelationship,
    user_id: int | None = None
) -> PersonCompanyAffiliation | None:
    """
    Create or update a PersonCompanyAffiliation from a PersonnelEntityRelationship.

    Args:
        personnel_rel: Legacy personnel-entity relationship
        user_id: User performing the sync

    Returns:
        PersonCompanyAffiliation if company found, None otherwise
    """
    session = _session()

    # Find the unified company for this entity
    company = _get_company_for_entity(personnel_rel.entity_type, personnel_rel.entity_id)
    if not company:
        return None

    # Check if affiliation already exists
    affiliation = (
        session.query(PersonCompanyAffiliation)
        .filter(
            and_(
                PersonCompanyAffiliation.person_id == personnel_rel.personnel_id,
                PersonCompanyAffiliation.company_id == company.company_id,
                PersonCompanyAffiliation.title == personnel_rel.role_at_entity,
            )
        )
        .first()
    )

    if affiliation:
        # Update existing
        if personnel_rel.notes and personnel_rel.notes != affiliation.notes:
            affiliation.notes = personnel_rel.notes
            affiliation.modified_by = user_id
            affiliation.modified_date = datetime.utcnow()
    else:
        # Create new affiliation
        affiliation = PersonCompanyAffiliation(
            person_id=personnel_rel.personnel_id,
            company_id=company.company_id,
            title=personnel_rel.role_at_entity,
            notes=personnel_rel.notes,
            is_primary=False,
            created_by=user_id,
            modified_by=user_id,
        )
        session.add(affiliation)

    session.flush()
    return affiliation



# ============================================================================
# REMOVED: Legacy project relationship sync functions
# ============================================================================
# The following functions have been removed as projects.py now creates
# CompanyRoleAssignment records directly:
#
# - sync_project_vendor_relationship()
# - sync_project_constructor_relationship()
# - sync_project_operator_relationship()
# - sync_project_owner_relationship()
# - sync_project_offtaker_relationship()
#
# These were dual-write transitional functions used during the migration
# from legacy ProjectVendorRelationship, ProjectOwnerRelationship, etc.
# to the unified CompanyRoleAssignment schema.
#
# If you need to backfill historical data, use the scripts in scripts/:
# - scripts/backfill_project_relationships.py
# ============================================================================


__all__ = [
    'sync_company_from_vendor',
    'sync_company_from_owner',
    'sync_company_from_client',
    'sync_company_from_operator',
    'sync_company_from_constructor',
    'sync_company_from_offtaker',
    'sync_personnel_affiliation',
]
