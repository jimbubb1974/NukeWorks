"""Unified company views."""
from collections import defaultdict

from flask import Blueprint, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.orm import joinedload
from werkzeug.routing import BuildError

from app import db_session
from app.models import Company, CompanyRole, CompanyRoleAssignment

bp = Blueprint('companies', __name__, url_prefix='/companies')

_ROLE_ENDPOINTS = {
    'VendorRecord': ('vendors.view_vendor', 'vendor_id'),
    'OwnerRecord': ('owners.view_owner', 'owner_id'),
    'ClientRecord': ('clients.view_client', 'client_id'),
    'OperatorRecord': ('operators.view_operator', 'operator_id'),
    'ConstructorRecord': ('constructors.view_constructor', 'constructor_id'),
    'OfftakerRecord': ('offtakers.view_offtaker', 'offtaker_id'),
}


def _assignment_link(assignment: CompanyRoleAssignment) -> str | None:
    mapping = _ROLE_ENDPOINTS.get(assignment.context_type)
    if not mapping:
        return None
    endpoint, param = mapping
    if assignment.context_id is None:
        return None
    try:
        return url_for(endpoint, **{param: assignment.context_id})
    except BuildError:
        return None


@bp.route('/')
@login_required
def list_companies():
    role_filter = request.args.get('role', '').strip()

    query = db_session.query(Company)
    if role_filter:
        query = (
            query.join(CompanyRoleAssignment)
            .join(CompanyRole)
            .filter(CompanyRole.role_code == role_filter)
            .distinct()
        )

    companies = query.options(joinedload(Company.role_assignments).joinedload(CompanyRoleAssignment.role)).order_by(Company.company_name).all()

    company_ids = [company.company_id for company in companies]
    assignments_map: dict[int, list[dict[str, str | int | None]]] = defaultdict(list)

    if company_ids:
        assignments = (
            db_session.query(CompanyRoleAssignment)
            .options(joinedload(CompanyRoleAssignment.role))
            .filter(CompanyRoleAssignment.company_id.in_(company_ids))
            .all()
        )
        for assignment in assignments:
            assignments_map[assignment.company_id].append(
                {
                    'role_label': assignment.role.role_label if assignment.role else assignment.role_id,
                    'context_type': assignment.context_type,
                    'context_id': assignment.context_id,
                    'url': _assignment_link(assignment),
                }
            )

    roles = db_session.query(CompanyRole).filter(CompanyRole.is_active == True).order_by(CompanyRole.role_label).all()

    return render_template(
        'companies/list.html',
        companies=companies,
        assignments_map=assignments_map,
        roles=roles,
        active_role=role_filter,
    )
