"""
Network View - Flexible table view with dynamic columns and grouping
Allows users to select which entity to group by and which columns to display
"""
from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import func, distinct
from collections import defaultdict

from app.models import (
    Project,
    Company,
    CompanyRole,
    CompanyRoleAssignment,
    Product,
)
from app import db_session

bp = Blueprint('network', __name__, url_prefix='/network')


# Define available columns/entities
AVAILABLE_COLUMNS = {
    'project': {'label': 'Project', 'model': Project, 'field': 'project_name'},
    'owner': {'label': 'Owner/Developer', 'role_code': 'developer'},
    'vendor': {'label': 'Technology Vendor', 'role_code': 'vendor'},
    'technology': {'label': 'Technology/Product', 'model': Product, 'field': 'product_name'},
    'operator': {'label': 'Operator', 'role_code': 'operator'},
    'offtaker': {'label': 'Offtaker', 'role_code': 'offtaker'},
    'constructor': {'label': 'Constructor', 'role_code': 'constructor'},
}


def _get_project_relationships(project_id):
    """Get all relationships for a project using unified schema"""
    relationships = {
        'owners': [],
        'vendors': [],
        'technologies': [],
        'operators': [],
        'offtakers': [],
        'constructors': []
    }

    # Get all company role assignments for this project
    assignments = db_session.query(CompanyRoleAssignment).filter_by(
        context_type='Project',
        context_id=project_id
    ).all()

    for assignment in assignments:
        company = db_session.get(Company, assignment.company_id)
        role = db_session.get(CompanyRole, assignment.role_id)

        if not company or not role:
            continue

        company_info = {
            'id': company.company_id,
            'name': company.company_name
        }

        # Map role to relationship category
        if role.role_code in ['developer', 'owner']:
            relationships['owners'].append(company_info)
        elif role.role_code == 'vendor':
            relationships['vendors'].append(company_info)
            # Get products from this vendor
            for product in company.products:
                relationships['technologies'].append({
                    'id': product.product_id,
                    'name': product.product_name
                })
        elif role.role_code == 'operator':
            relationships['operators'].append(company_info)
        elif role.role_code == 'offtaker':
            relationships['offtakers'].append(company_info)
        elif role.role_code == 'constructor':
            relationships['constructors'].append(company_info)

    return relationships


def _build_grouped_data(group_by, selected_columns):
    """Build data grouped by the specified entity, including entities without relationships"""

    # Get all projects with their relationships
    projects = db_session.query(Project).all()

    # Build network data
    grouped_data = defaultdict(lambda: {
        'group_id': None,
        'group_name': None,
        'items': []
    })

    # First, add all projects to their respective groups
    for project in projects:
        project_rels = _get_project_relationships(project.project_id)

        # Determine grouping
        if group_by == 'project':
            groups = [{'id': project.project_id, 'name': project.project_name}]
        elif group_by == 'owner':
            groups = project_rels['owners'] if project_rels['owners'] else [{'id': None, 'name': 'No Owner'}]
        elif group_by == 'vendor':
            groups = project_rels['vendors'] if project_rels['vendors'] else [{'id': None, 'name': 'No Vendor'}]
        elif group_by == 'technology':
            groups = project_rels['technologies'] if project_rels['technologies'] else [{'id': None, 'name': 'No Technology'}]
        elif group_by == 'operator':
            groups = project_rels['operators'] if project_rels['operators'] else [{'id': None, 'name': 'No Operator'}]
        elif group_by == 'offtaker':
            groups = project_rels['offtakers'] if project_rels['offtakers'] else [{'id': None, 'name': 'No Offtaker'}]
        else:
            groups = [{'id': None, 'name': 'All'}]

        # Add project to each group it belongs to
        for group in groups:
            group_key = f"{group_by}_{group['id']}"

            if not grouped_data[group_key]['group_id']:
                grouped_data[group_key]['group_id'] = group['id']
                grouped_data[group_key]['group_name'] = group['name']

            # Build item data with selected columns
            item = {
                'project_id': project.project_id,
                'project_name': project.project_name
            }

            # Add selected column data
            for col in selected_columns:
                if col == 'project':
                    continue  # Already have project
                elif col == 'owner':
                    item['owners'] = [o['name'] for o in project_rels['owners']]
                elif col == 'vendor':
                    item['vendors'] = [v['name'] for v in project_rels['vendors']]
                elif col == 'technology':
                    item['technologies'] = [t['name'] for t in project_rels['technologies']]
                elif col == 'operator':
                    item['operators'] = [o['name'] for o in project_rels['operators']]
                elif col == 'offtaker':
                    item['offtakers'] = [o['name'] for o in project_rels['offtakers']]

            grouped_data[group_key]['items'].append(item)

    # Now add entities without relationships as empty groups
    if group_by in ['owner', 'vendor', 'operator', 'offtaker', 'constructor']:
        # Get all companies with this role
        role_code = AVAILABLE_COLUMNS[group_by]['role_code']
        role = db_session.query(CompanyRole).filter_by(role_code=role_code).first()

        if role:
            # Get all companies with this role
            company_ids = db_session.query(CompanyRoleAssignment.company_id).filter_by(
                role_id=role.role_id
            ).distinct().all()
            company_ids = [cid[0] for cid in company_ids]

            companies = db_session.query(Company).filter(
                Company.company_id.in_(company_ids)
            ).all() if company_ids else []

            for company in companies:
                group_key = f"{group_by}_{company.company_id}"
                if group_key not in grouped_data:
                    grouped_data[group_key] = {
                        'group_id': company.company_id,
                        'group_name': company.company_name,
                        'items': []
                    }

    elif group_by == 'technology':
        # Get all technologies that don't have any projects
        all_technologies = db_session.query(Product).all()
        for technology in all_technologies:
            group_key = f"technology_{technology.product_id}"
            if group_key not in grouped_data:
                grouped_data[group_key] = {
                    'group_id': technology.product_id,
                    'group_name': technology.product_name,
                    'items': []
                }

    # Convert to list and sort
    result = list(grouped_data.values())
    result.sort(key=lambda x: x['group_name'] or '')

    return result


@bp.route('/')
@login_required
def index():
    """
    Network view with dynamic columns and grouping

    Query params:
    - group_by: Entity to group by (project, owner, vendor, technology, operator, offtaker)
    - columns: Comma-separated list of columns to display
    """
    # Get parameters
    group_by = request.args.get('group_by', 'project')
    columns_param = request.args.get('columns', 'project,owner,vendor,technology')

    # Parse selected columns
    selected_columns = [col.strip() for col in columns_param.split(',') if col.strip()]

    # Ensure group_by is valid
    if group_by not in AVAILABLE_COLUMNS:
        group_by = 'project'

    # Ensure selected columns are valid
    selected_columns = [col for col in selected_columns if col in AVAILABLE_COLUMNS]

    # If no columns selected, default to project and owner
    if not selected_columns:
        selected_columns = ['project', 'owner']

    # Ensure group_by is in selected columns
    if group_by not in selected_columns:
        selected_columns.insert(0, group_by)

    # Build grouped data
    grouped_data = _build_grouped_data(group_by, selected_columns)

    return render_template(
        'network/view.html',
        available_columns=AVAILABLE_COLUMNS,
        selected_columns=selected_columns,
        group_by=group_by,
        grouped_data=grouped_data
    )
