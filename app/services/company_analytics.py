"""Analytics and reporting utilities using the unified company schema."""
from __future__ import annotations

from typing import Dict, List, Any

from sqlalchemy import func

from app import db_session
from app.models import Company, CompanyRole, CompanyRoleAssignment


def get_company_counts_by_role() -> Dict[str, int]:
    """
    Get counts of companies by role from unified schema.

    Returns:
        Dictionary mapping role codes to counts of distinct companies
    """
    roles = db_session.query(CompanyRole).all()
    counts = {}

    for role in roles:
        count = db_session.query(func.count(func.distinct(CompanyRoleAssignment.company_id))).filter(
            CompanyRoleAssignment.role_id == role.role_id
        ).scalar() or 0
        counts[role.role_code] = count

    return counts


def get_companies_by_role(role_code: str) -> List[Company]:
    """
    Get all companies with a specific role.

    Args:
        role_code: Role code (vendor, developer, operator, constructor, offtaker, client)

    Returns:
        List of Company objects with that role
    """
    role = db_session.query(CompanyRole).filter(CompanyRole.role_code == role_code).first()
    if not role:
        return []

    company_ids = (
        db_session.query(CompanyRoleAssignment.company_id)
        .filter(CompanyRoleAssignment.role_id == role.role_id)
        .distinct()
        .all()
    )

    company_ids = [cid[0] for cid in company_ids]

    return db_session.query(Company).filter(Company.company_id.in_(company_ids)).order_by(Company.company_name).all()


def get_companies_for_project(project_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all companies associated with a project, grouped by role.

    Args:
        project_id: Project ID

    Returns:
        Dictionary mapping role codes to lists of company info dictionaries
    """
    assignments = (
        db_session.query(CompanyRoleAssignment)
        .filter(
            CompanyRoleAssignment.context_type == 'Project',
            CompanyRoleAssignment.context_id == project_id
        )
        .all()
    )

    results = {}

    for assignment in assignments:
        role_code = assignment.role.role_code if assignment.role else 'unknown'
        company_info = {
            'id': assignment.company_id,
            'name': assignment.company.company_name if assignment.company else 'Unknown',
            'notes': assignment.notes,
            'is_confidential': assignment.is_confidential,
        }

        if role_code not in results:
            results[role_code] = []

        results[role_code].append(company_info)

    return results


def get_project_participation_summary() -> Dict[str, Any]:
    """
    Get summary statistics about project participation across all companies.

    Returns:
        Dictionary with summary statistics
    """
    # Count unique companies with project assignments
    companies_with_projects = (
        db_session.query(func.count(func.distinct(CompanyRoleAssignment.company_id)))
        .filter(CompanyRoleAssignment.context_type == 'Project')
        .scalar() or 0
    )

    # Count project assignments by role
    role_assignments = {}
    roles = db_session.query(CompanyRole).all()

    for role in roles:
        count = (
            db_session.query(func.count(CompanyRoleAssignment.assignment_id))
            .filter(
                CompanyRoleAssignment.role_id == role.role_id,
                CompanyRoleAssignment.context_type == 'Project'
            )
            .scalar() or 0
        )
        role_assignments[role.role_code] = count

    return {
        'companies_with_projects': companies_with_projects,
        'role_assignments': role_assignments,
    }


__all__ = [
    'get_company_counts_by_role',
    'get_companies_by_role',
    'get_companies_for_project',
    'get_project_participation_summary',
]
