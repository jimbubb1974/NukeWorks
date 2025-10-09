"""Helper utilities for relationship management routes"""
from typing import List, Tuple, Optional

from app import db_session
from app.models import Company, CompanyRoleAssignment, CompanyRole, Project, Personnel


def _with_placeholder(choices: List[Tuple[int, str]], placeholder: str) -> List[Tuple[int, str]]:
    """Add a placeholder choice at the beginning of the list"""
    return [(0, placeholder)] + choices


def get_company_choices(
    role_filter: Optional[str] = None,
    placeholder: str = '-- Select Company --'
) -> List[Tuple[int, str]]:
    """
    Return selectable company choices.

    Args:
        role_filter: Optional role code to filter by (e.g., 'vendor', 'developer', 'operator')
        placeholder: Placeholder text for dropdown

    Returns:
        List of (company_id, company_name) tuples with placeholder at index 0
    """
    query = db_session.query(Company).order_by(Company.company_name)

    if role_filter:
        # Filter companies that have the specified role
        query = query.join(CompanyRoleAssignment).join(CompanyRole).filter(
            CompanyRole.role_code == role_filter
        ).distinct()

    companies = query.all()
    choices = [(company.company_id, company.company_name) for company in companies]
    return _with_placeholder(choices, placeholder)


def get_project_choices(placeholder: str = '-- Select Project --') -> List[Tuple[int, str]]:
    """Return selectable project choices"""
    projects = db_session.query(Project).order_by(Project.project_name).all()
    choices = [(project.project_id, project.project_name) for project in projects]
    return _with_placeholder(choices, placeholder)


def get_personnel_choices(
    placeholder: str = '-- Select Personnel --',
    internal_only: bool = False
) -> List[Tuple[int, str]]:
    """Return selectable personnel choices"""
    query = db_session.query(Personnel).order_by(Personnel.full_name)
    if internal_only:
        query = query.filter(Personnel.personnel_type == 'Internal')
    personnel = query.all()
    choices = [(person.personnel_id, person.full_name) for person in personnel]
    return _with_placeholder(choices, placeholder)


# Legacy function aliases for backward compatibility
# These will be deprecated in future releases

def get_vendor_choices(exclude_id: int | None = None, placeholder: str = '-- Select Vendor --') -> List[Tuple[int, str]]:
    """DEPRECATED: Use get_company_choices(role_filter='vendor') instead"""
    return get_company_choices(role_filter='vendor', placeholder=placeholder)


def get_owner_choices(placeholder: str = '-- Select Owner / Developer --') -> List[Tuple[int, str]]:
    """DEPRECATED: Use get_company_choices(role_filter='developer') instead"""
    return get_company_choices(role_filter='developer', placeholder=placeholder)


def get_constructor_choices(placeholder: str = '-- Select Constructor --') -> List[Tuple[int, str]]:
    """DEPRECATED: Use get_company_choices(role_filter='constructor') instead"""
    return get_company_choices(role_filter='constructor', placeholder=placeholder)


def get_operator_choices(placeholder: str = '-- Select Operator --') -> List[Tuple[int, str]]:
    """DEPRECATED: Use get_company_choices(role_filter='operator') instead"""
    return get_company_choices(role_filter='operator', placeholder=placeholder)


def get_offtaker_choices(placeholder: str = '-- Select Off-taker --') -> List[Tuple[int, str]]:
    """DEPRECATED: Use get_company_choices(role_filter='offtaker') instead"""
    return get_company_choices(role_filter='offtaker', placeholder=placeholder)
