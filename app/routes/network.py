"""Network diagram and table view routes."""
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from collections import defaultdict

from app.services.network_diagram import get_network_data
from app.models import (
    Project,
    OwnerDeveloper,
    TechnologyVendor,
    Product,
    Operator,
    Offtaker,
    ProjectOwnerRelationship,
    ProjectVendorRelationship,
    ProjectOperatorRelationship,
    ProjectOfftakerRelationship
)
from app import db_session

bp = Blueprint("network", __name__)

# Available columns for table view
AVAILABLE_COLUMNS = {
    'project': {'label': 'Project', 'model': Project, 'field': 'project_name'},
    'owner': {'label': 'Owner/Developer', 'model': OwnerDeveloper, 'field': 'company_name'},
    'vendor': {'label': 'Technology Vendor', 'model': TechnologyVendor, 'field': 'vendor_name'},
    'technology': {'label': 'Technology/Product', 'model': Product, 'field': 'product_name'},
    'operator': {'label': 'Operator', 'model': Operator, 'field': 'company_name'},
    'offtaker': {'label': 'Offtaker', 'model': Offtaker, 'field': 'organization_name'},
}


@bp.route("/network-diagram")
@login_required
def network_diagram():
    """Render network diagram page."""
    return render_template("network/diagram.html")


@bp.route("/api/network-diagram", methods=["GET", "POST"])
@login_required
def network_data():
    """Return serialized network data for Vis.js."""
    if request.method == "POST":
        filters = request.get_json(silent=True) or {}
    else:
        # Allow GET requests with query params for convenience
        filters = {
            "entity_types": request.args.getlist("entity_types") or None,
            "relationship_types": request.args.getlist("relationship_types") or None,
        }
        focus_type = request.args.get("focus_type")
        focus_id = request.args.get("focus_id")
        depth = request.args.get("depth")
        if focus_type and focus_id is not None:
            try:
                focus_id_value = int(focus_id)
            except (TypeError, ValueError):
                focus_id_value = focus_id
            filters["focus_entity"] = {"type": focus_type, "id": focus_id_value}
        if depth:
            filters["depth"] = depth

    data = get_network_data(current_user, filters)
    return jsonify(data)


def _get_project_relationships(project_id):
    """Get all relationships for a project"""
    relationships = {
        'owners': [],
        'vendors': [],
        'technologies': [],
        'operators': [],
        'offtakers': []
    }

    # Get owners
    owner_rels = db_session.query(ProjectOwnerRelationship).filter_by(project_id=project_id).all()
    for rel in owner_rels:
        if rel.owner:
            relationships['owners'].append({
                'id': rel.owner.owner_id,
                'name': rel.owner.company_name
            })

    # Get vendors and technologies
    vendor_rels = db_session.query(ProjectVendorRelationship).filter_by(project_id=project_id).all()
    for rel in vendor_rels:
        if rel.vendor:
            relationships['vendors'].append({
                'id': rel.vendor.vendor_id,
                'name': rel.vendor.vendor_name
            })
            # Get all products from this vendor's company
            # Note: TechnologyVendor now links to Company, and products are linked to Company
            if hasattr(rel.vendor, 'company') and rel.vendor.company:
                for product in rel.vendor.company.products:
                    relationships['technologies'].append({
                        'id': product.product_id,
                        'name': product.product_name
                    })

    # Get operators
    operator_rels = db_session.query(ProjectOperatorRelationship).filter_by(project_id=project_id).all()
    for rel in operator_rels:
        if rel.operator:
            relationships['operators'].append({
                'id': rel.operator.operator_id,
                'name': rel.operator.company_name
            })

    # Get offtakers
    offtaker_rels = db_session.query(ProjectOfftakerRelationship).filter_by(project_id=project_id).all()
    for rel in offtaker_rels:
        if rel.offtaker:
            relationships['offtakers'].append({
                'id': rel.offtaker.offtaker_id,
                'name': rel.offtaker.organization_name
            })

    return relationships


def _build_grouped_data(group_by, selected_columns):
    """Build data grouped by the specified entity, including entities without relationships"""
    # Get all projects with their relationships
    projects = db_session.query(Project).all()

    # Build network data
    grouped_data = defaultdict(lambda: {
        'group_id': None,
        'group_name': None,
        'projects': []
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

            grouped_data[group_key]['projects'].append(item)

    # Now add entities without relationships as empty groups
    if group_by == 'owner':
        # Get all owners that don't have any projects
        all_owners = db_session.query(AVAILABLE_COLUMNS['owner']['model']).all()
        for owner in all_owners:
            group_key = f"owner_{owner.owner_id}"
            if group_key not in grouped_data:
                grouped_data[group_key] = {
                    'group_id': owner.owner_id,
                    'group_name': owner.company_name,
                    'projects': []
                }
        
    elif group_by == 'vendor':
        # Get all vendors that don't have any projects
        all_vendors = db_session.query(AVAILABLE_COLUMNS['vendor']['model']).all()
        for vendor in all_vendors:
            group_key = f"vendor_{vendor.vendor_id}"
            if group_key not in grouped_data:
                grouped_data[group_key] = {
                    'group_id': vendor.vendor_id,
                    'group_name': vendor.vendor_name,
                    'projects': []
                }
    elif group_by == 'operator':
        # Get all operators that don't have any projects
        all_operators = db_session.query(AVAILABLE_COLUMNS['operator']['model']).all()
        for operator in all_operators:
            group_key = f"operator_{operator.operator_id}"
            if group_key not in grouped_data:
                grouped_data[group_key] = {
                    'group_id': operator.operator_id,
                    'group_name': operator.company_name,
                    'projects': []
                }
    elif group_by == 'offtaker':
        # Get all offtakers that don't have any projects
        all_offtakers = db_session.query(AVAILABLE_COLUMNS['offtaker']['model']).all()
        for offtaker in all_offtakers:
            group_key = f"offtaker_{offtaker.offtaker_id}"
            if group_key not in grouped_data:
                grouped_data[group_key] = {
                    'group_id': offtaker.offtaker_id,
                    'group_name': offtaker.organization_name,
                    'projects': []
                }
    elif group_by == 'technology':
        # Get all technologies that don't have any projects
        all_technologies = db_session.query(AVAILABLE_COLUMNS['technology']['model']).all()
        for technology in all_technologies:
            group_key = f"technology_{technology.product_id}"
            if group_key not in grouped_data:
                grouped_data[group_key] = {
                    'group_id': technology.product_id,
                    'group_name': technology.product_name,
                    'projects': []
                }

    # Convert to list and sort
    result = list(grouped_data.values())
    result.sort(key=lambda x: x['group_name'] or '')

    return result


@bp.route("/network-table")
@login_required
def network_table():
    """
    Network table view with dynamic columns and grouping

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
        'network/table_view.html',
        available_columns=AVAILABLE_COLUMNS,
        selected_columns=selected_columns,
        group_by=group_by,
        grouped_data=grouped_data
    )
