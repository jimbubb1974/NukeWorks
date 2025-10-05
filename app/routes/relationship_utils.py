"""Helper utilities for relationship management routes"""
from typing import List, Tuple

from app import db_session
from app.models import (
    TechnologyVendor,
    OwnerDeveloper,
    Project,
    Constructor,
    Operator,
    Personnel,
    Offtaker
)


def _with_placeholder(choices: List[Tuple[int, str]], placeholder: str) -> List[Tuple[int, str]]:
    """Add a placeholder choice at the beginning of the list"""
    return [(0, placeholder)] + choices


def get_vendor_choices(exclude_id: int | None = None, placeholder: str = '-- Select Vendor --') -> List[Tuple[int, str]]:
    """Return selectable vendor choices"""
    query = db_session.query(TechnologyVendor).order_by(TechnologyVendor.vendor_name)
    if exclude_id:
        query = query.filter(TechnologyVendor.vendor_id != exclude_id)
    choices = [(vendor.vendor_id, vendor.vendor_name) for vendor in query]
    return _with_placeholder(choices, placeholder)


def get_owner_choices(placeholder: str = '-- Select Owner / Developer --') -> List[Tuple[int, str]]:
    """Return selectable owner/developer choices"""
    owners = db_session.query(OwnerDeveloper).order_by(OwnerDeveloper.company_name).all()
    choices = [(owner.owner_id, owner.company_name) for owner in owners]
    return _with_placeholder(choices, placeholder)


def get_project_choices(placeholder: str = '-- Select Project --') -> List[Tuple[int, str]]:
    """Return selectable project choices"""
    projects = db_session.query(Project).order_by(Project.project_name).all()
    choices = [(project.project_id, project.project_name) for project in projects]
    return _with_placeholder(choices, placeholder)


def get_constructor_choices(placeholder: str = '-- Select Constructor --') -> List[Tuple[int, str]]:
    """Return selectable constructor choices"""
    constructors = db_session.query(Constructor).order_by(Constructor.company_name).all()
    choices = [(constructor.constructor_id, constructor.company_name) for constructor in constructors]
    return _with_placeholder(choices, placeholder)


def get_operator_choices(placeholder: str = '-- Select Operator --') -> List[Tuple[int, str]]:
    """Return selectable operator choices"""
    operators = db_session.query(Operator).order_by(Operator.company_name).all()
    choices = [(operator.operator_id, operator.company_name) for operator in operators]
    return _with_placeholder(choices, placeholder)


def get_offtaker_choices(placeholder: str = '-- Select Off-taker --') -> List[Tuple[int, str]]:
    """Return selectable energy off-taker choices."""
    offtakers = db_session.query(Offtaker).order_by(Offtaker.organization_name).all()
    choices = [(offtaker.offtaker_id, offtaker.organization_name) for offtaker in offtakers]
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
