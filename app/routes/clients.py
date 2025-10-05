"""
Client Routes - Complete CRUD Operations for CRM
Following vendor pattern from VENDOR_CRUD_IMPLEMENTATION.md
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, or_
from datetime import datetime

from app.models import (
    Client,
    ClientOwnerRelationship,
    ClientProjectRelationship,
    ClientVendorRelationship,
    ClientOperatorRelationship,
    ClientPersonnelRelationship,
    OwnerDeveloper,
    Project,
    TechnologyVendor,
    Operator,
    Personnel,
    ContactLog,
    RoundtableHistory
)
from app.forms.clients import (
    ClientForm,
    ClientAssessmentForm,
    ClientContactForm,
    DeleteClientForm
)
from app.forms.client_relationships import (
    ClientOwnerRelationshipForm,
    ClientProjectRelationshipForm,
    ClientVendorRelationshipForm,
    ClientOperatorRelationshipForm,
    ClientPersonnelRelationshipForm,
    RemoveRelationshipForm
)
from flask_wtf import FlaskForm
from app import db_session
from app.utils.permissions import admin_required, ned_team_required
from app.services.company_sync import sync_company_from_client
from app.services.company_query import get_company_for_client

bp = Blueprint('clients', __name__, url_prefix='/clients')


def _get_client_or_404(client_id: int) -> Client:
    """Return client or abort with 404"""
    client = db_session.get(Client, client_id)
    if not client:
        flash('Client not found', 'error')
        abort(404)
    return client


def _get_internal_personnel_choices():
    """Get list of internal personnel for dropdowns"""
    personnel = db_session.query(Personnel).filter(
        Personnel.personnel_type == 'Internal',
        Personnel.is_active == True
    ).order_by(Personnel.full_name).all()

    return [(p.personnel_id, p.full_name) for p in personnel]


def _can_manage_ned_fields(user) -> bool:
    """Check if user can manage NED Team fields"""
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


@bp.route('/')
@login_required
def list_clients():
    """
    List all CRM clients

    Features:
    - Sorted alphabetically by client_name
    - Shows linked entity counts
    - Search functionality
    - Filter by priority, status (NED Team only)
    """
    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    priority_filter = request.args.get('priority', '')
    status_filter = request.args.get('status', '')

    # Base query
    query = db_session.query(Client)

    # Apply search filter
    if search:
        query = query.filter(
            or_(
                Client.client_name.ilike(f'%{search}%'),
                Client.client_type.ilike(f'%{search}%')
            )
        )

    # Apply NED Team filters (if user has access)
    if _can_manage_ned_fields(current_user):
        if priority_filter:
            query = query.filter(Client.client_priority == priority_filter)
        if status_filter:
            query = query.filter(Client.client_status == status_filter)

    # Order by name
    clients = query.order_by(Client.client_name).all()

    # Get relationship counts for each client
    client_counts = {}
    for client in clients:
        client_counts[client.client_id] = {
            'owners': len(client.owner_relationships),
            'projects': len(client.project_relationships),
            'vendors': len(client.vendor_relationships),
            'personnel': len(client.personnel_relationships)
        }

    return render_template(
        'clients/list.html',
        clients=clients,
        client_counts=client_counts,
        search=search,
        priority_filter=priority_filter,
        status_filter=status_filter,
        can_see_ned_fields=_can_manage_ned_fields(current_user),
        today=datetime.now().date()
    )


@bp.route('/<int:client_id>')
@login_required
def view_client(client_id):
    """
    View client details

    Features:
    - Full client information
    - Contact tracking
    - All relationships
    - Roundtable history (NED Team only)
    - Internal assessment (NED Team only)
    """
    client = _get_client_or_404(client_id)

    company_record = get_company_for_client(client_id)

    # Get relationships
    owner_relationships = client.owner_relationships
    project_relationships = client.project_relationships
    vendor_relationships = client.vendor_relationships
    operator_relationships = client.operator_relationships
    personnel_relationships = client.personnel_relationships

    # Get contact logs (last 10)
    recent_contacts = db_session.query(ContactLog).filter(
        ContactLog.entity_type == 'Client',
        ContactLog.entity_id == client_id
    ).order_by(ContactLog.contact_date.desc()).limit(10).all()

    # Get roundtable history (NED Team only, last 3)
    roundtable_history = []
    if _can_manage_ned_fields(current_user):
        roundtable_history = db_session.query(RoundtableHistory).filter(
            RoundtableHistory.entity_type == 'Client',
            RoundtableHistory.entity_id == client_id
        ).order_by(RoundtableHistory.meeting_date.desc()).limit(3).all()

    # Create a remove form for CSRF protection
    remove_form = RemoveRelationshipForm()

    return render_template(
        'clients/detail.html',
        client=client,
        owner_relationships=owner_relationships,
        project_relationships=project_relationships,
        vendor_relationships=vendor_relationships,
        operator_relationships=operator_relationships,
        personnel_relationships=personnel_relationships,
        company_record=company_record,
        recent_contacts=recent_contacts,
        roundtable_history=roundtable_history,
        can_see_ned_fields=_can_manage_ned_fields(current_user),
        remove_form=remove_form
    )


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_client():
    """
    Create new CRM client

    Validation:
    - client_name required, trimmed
    - Notes optional, max 10000 chars
    """
    personnel_choices = _get_internal_personnel_choices()
    form = ClientForm(personnel_choices=personnel_choices)

    if form.validate_on_submit():
        try:
            # Create client
            client = Client(
                client_name=form.client_name.data,
                client_type=form.client_type.data if form.client_type.data else None,
                notes=form.notes.data,
                mpr_primary_poc=form.mpr_primary_poc.data if form.mpr_primary_poc.data else None,
                mpr_secondary_poc=form.mpr_secondary_poc.data if form.mpr_secondary_poc.data else None,
                created_by=current_user.user_id,
                modified_by=current_user.user_id
            )

            db_session.add(client)
            db_session.flush()
            sync_company_from_client(client, current_user.user_id)
            db_session.commit()

            flash(f'Client "{client.client_name}" created successfully', 'success')
            return redirect(url_for('clients.view_client', client_id=client.client_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error creating client: {str(e)}', 'error')

    return render_template(
        'clients/form.html',
        form=form,
        title='Create Client',
        client=None
    )


@bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    """
    Edit existing client

    Validation:
    - Same as create
    """
    client = _get_client_or_404(client_id)
    personnel_choices = _get_internal_personnel_choices()
    form = ClientForm(client_id=client_id, personnel_choices=personnel_choices, obj=client)

    # Add assessment form for NED Team
    assessment_form = None
    if _can_manage_ned_fields(current_user):
        assessment_form = ClientAssessmentForm(obj=client)

    if form.validate_on_submit():
        try:
            # Update client basic info
            client.client_name = form.client_name.data
            client.client_type = form.client_type.data if form.client_type.data else None
            client.notes = form.notes.data
            client.mpr_primary_poc = form.mpr_primary_poc.data if form.mpr_primary_poc.data else None
            client.mpr_secondary_poc = form.mpr_secondary_poc.data if form.mpr_secondary_poc.data else None

            # Update assessment fields if NED Team
            if assessment_form and assessment_form.validate():
                client.relationship_strength = assessment_form.relationship_strength.data if assessment_form.relationship_strength.data else None
                client.client_priority = assessment_form.client_priority.data if assessment_form.client_priority.data else None
                client.client_status = assessment_form.client_status.data if assessment_form.client_status.data else None
                client.relationship_notes = assessment_form.relationship_notes.data

            client.modified_by = current_user.user_id
            client.modified_date = datetime.utcnow()

            sync_company_from_client(client, current_user.user_id)
            db_session.commit()

            flash(f'Client "{client.client_name}" updated successfully', 'success')
            return redirect(url_for('clients.view_client', client_id=client.client_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error updating client: {str(e)}', 'error')

    return render_template(
        'clients/form.html',
        form=form,
        assessment_form=assessment_form,
        title='Edit Client',
        client=client
    )


@bp.route('/<int:client_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_client(client_id):
    """
    Delete client with dependency checking

    Business Rules:
    - Admin only
    - Cannot delete if relationships exist
    - Shows detailed dependency information
    """
    client = _get_client_or_404(client_id)

    # Check for dependencies
    owner_count = len(client.owner_relationships)
    project_count = len(client.project_relationships)
    vendor_count = len(client.vendor_relationships)
    operator_count = len(client.operator_relationships)
    personnel_count = len(client.personnel_relationships)

    contact_count = db_session.query(func.count(ContactLog.contact_id)).filter(
        ContactLog.entity_type == 'Client',
        ContactLog.entity_id == client_id
    ).scalar()

    roundtable_count = db_session.query(func.count(RoundtableHistory.history_id)).filter(
        RoundtableHistory.entity_type == 'Client',
        RoundtableHistory.entity_id == client_id
    ).scalar()

    has_dependencies = (
        owner_count > 0 or
        project_count > 0 or
        vendor_count > 0 or
        operator_count > 0 or
        personnel_count > 0 or
        contact_count > 0 or
        roundtable_count > 0
    )

    form = DeleteClientForm()

    if form.validate_on_submit():
        if has_dependencies:
            flash(
                f'Cannot delete client "{client.client_name}" - it has dependencies. '
                f'Please remove all relationships, contact logs, and roundtable history first.',
                'error'
            )
            return redirect(url_for('clients.view_client', client_id=client_id))

        try:
            client_name = client.client_name
            db_session.delete(client)
            db_session.commit()

            flash(f'Client "{client_name}" deleted successfully', 'success')
            return redirect(url_for('clients.list_clients'))

        except Exception as e:
            db_session.rollback()
            flash(f'Error deleting client: {str(e)}', 'error')
            return redirect(url_for('clients.view_client', client_id=client_id))

    return render_template(
        'clients/delete.html',
        client=client,
        form=form,
        owner_count=owner_count,
        project_count=project_count,
        vendor_count=vendor_count,
        operator_count=operator_count,
        personnel_count=personnel_count,
        contact_count=contact_count,
        roundtable_count=roundtable_count,
        has_dependencies=has_dependencies
    )


@bp.route('/<int:client_id>/assessment', methods=['POST'])
@login_required
@ned_team_required
def update_assessment(client_id):
    """
    Update client internal assessment (NED Team only)

    Updates:
    - relationship_strength
    - client_priority
    - client_status
    - relationship_notes
    """
    client = _get_client_or_404(client_id)
    form = ClientAssessmentForm()

    if form.validate_on_submit():
        try:
            client.relationship_strength = form.relationship_strength.data if form.relationship_strength.data else None
            client.client_priority = form.client_priority.data if form.client_priority.data else None
            client.client_status = form.client_status.data if form.client_status.data else None
            client.relationship_notes = form.relationship_notes.data
            client.modified_by = current_user.user_id
            client.modified_date = datetime.utcnow()

            db_session.commit()

            flash('Client assessment updated successfully', 'success')

        except Exception as e:
            db_session.rollback()
            flash(f'Error updating assessment: {str(e)}', 'error')

    return redirect(url_for('clients.view_client', client_id=client_id))


@bp.route('/<int:client_id>/contact', methods=['POST'])
@login_required
def update_contact_info(client_id):
    """
    Update client contact tracking information

    Updates:
    - last_contact_*
    - next_planned_contact_*
    """
    client = _get_client_or_404(client_id)
    personnel_choices = _get_internal_personnel_choices()
    form = ClientContactForm(personnel_choices=personnel_choices)

    if form.validate_on_submit():
        try:
            client.last_contact_date = form.last_contact_date.data
            client.last_contact_type = form.last_contact_type.data if form.last_contact_type.data else None
            client.last_contact_by = form.last_contact_by.data if form.last_contact_by.data else None
            client.last_contact_notes = form.last_contact_notes.data
            client.next_planned_contact_date = form.next_planned_contact_date.data
            client.next_planned_contact_type = form.next_planned_contact_type.data if form.next_planned_contact_type.data else None
            client.next_planned_contact_assigned_to = form.next_planned_contact_assigned_to.data if form.next_planned_contact_assigned_to.data else None
            client.modified_by = current_user.user_id
            client.modified_date = datetime.utcnow()

            db_session.commit()

            flash('Contact information updated successfully', 'success')

        except Exception as e:
            db_session.rollback()
            flash(f'Error updating contact info: {str(e)}', 'error')

    return redirect(url_for('clients.view_client', client_id=client_id))


# ============================================================================
# API ENDPOINTS
# ============================================================================

@bp.route('/api/search')
@login_required
def api_search_clients():
    """
    Autocomplete endpoint for client selection

    Query params:
    - q: search query
    - limit: max results (default 10)

    Returns:
    - JSON array of {id, name, type}
    """
    query_str = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query_str:
        return jsonify([])

    clients = db_session.query(Client).filter(
        or_(
            Client.client_name.ilike(f'%{query_str}%'),
            Client.client_type.ilike(f'%{query_str}%')
        )
    ).order_by(Client.client_name).limit(limit).all()

    return jsonify([
        {
            'id': c.client_id,
            'name': c.client_name,
            'type': c.client_type or 'N/A'
        }
        for c in clients
    ])


@bp.route('/api/<int:client_id>')
@login_required
def api_get_client(client_id):
    """
    Get client data as JSON

    Returns:
    - Full client information (respecting NED Team permissions)
    """
    client = _get_client_or_404(client_id)

    return jsonify(client.to_dict(user=current_user))


# ============================================================================
# RELATIONSHIP MANAGEMENT
# ============================================================================

@bp.route('/<int:client_id>/relationships/owner/add', methods=['GET', 'POST'])
@login_required
def add_owner_relationship(client_id):
    """Add owner/developer relationship to client"""
    client = _get_client_or_404(client_id)

    # Get all owners for dropdown
    owners = db_session.query(OwnerDeveloper).order_by(OwnerDeveloper.company_name).all()
    owner_choices = [(o.owner_id, o.company_name) for o in owners]

    form = ClientOwnerRelationshipForm(owner_choices=owner_choices)

    if form.validate_on_submit():
        try:
            # Check if relationship already exists
            existing = db_session.query(ClientOwnerRelationship).filter_by(
                client_id=client_id,
                owner_id=form.owner_id.data
            ).first()

            if existing:
                flash('This owner/developer is already linked to this client', 'warning')
            else:
                relationship = ClientOwnerRelationship(
                    client_id=client_id,
                    owner_id=form.owner_id.data,
                    notes=form.notes.data,
                    created_by=current_user.user_id
                )
                db_session.add(relationship)
                db_session.commit()
                flash('Owner/developer linked successfully', 'success')

            return redirect(url_for('clients.view_client', client_id=client_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error linking owner/developer: {str(e)}', 'error')

    return render_template('clients/add_relationship.html',
                         client=client,
                         form=form,
                         relationship_type='Owner/Developer')


@bp.route('/<int:client_id>/relationships/owner/<int:owner_id>/remove', methods=['POST'])
@login_required
def remove_owner_relationship(client_id, owner_id):
    """Remove owner/developer relationship from client"""
    client = _get_client_or_404(client_id)

    relationship = db_session.query(ClientOwnerRelationship).filter_by(
        client_id=client_id,
        owner_id=owner_id
    ).first()

    if relationship:
        db_session.delete(relationship)
        db_session.commit()
        flash('Owner/developer relationship removed', 'success')
    else:
        flash('Relationship not found', 'error')

    return redirect(url_for('clients.view_client', client_id=client_id))


@bp.route('/<int:client_id>/relationships/project/add', methods=['GET', 'POST'])
@login_required
def add_project_relationship(client_id):
    """Add project relationship to client"""
    client = _get_client_or_404(client_id)

    # Get all projects for dropdown
    projects = db_session.query(Project).order_by(Project.project_name).all()
    project_choices = [(p.project_id, p.project_name) for p in projects]

    form = ClientProjectRelationshipForm(project_choices=project_choices)

    if form.validate_on_submit():
        try:
            # Check if relationship already exists
            existing = db_session.query(ClientProjectRelationship).filter_by(
                client_id=client_id,
                project_id=form.project_id.data
            ).first()

            if existing:
                flash('This project is already linked to this client', 'warning')
            else:
                relationship = ClientProjectRelationship(
                    client_id=client_id,
                    project_id=form.project_id.data,
                    relationship_type=form.relationship_type.data,
                    notes=form.notes.data,
                    created_by=current_user.user_id
                )
                db_session.add(relationship)
                db_session.commit()
                flash('Project linked successfully', 'success')

            return redirect(url_for('clients.view_client', client_id=client_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error linking project: {str(e)}', 'error')

    return render_template('clients/add_relationship.html',
                         client=client,
                         form=form,
                         relationship_type='Project')


@bp.route('/<int:client_id>/relationships/project/<int:project_id>/remove', methods=['POST'])
@login_required
def remove_project_relationship(client_id, project_id):
    """Remove project relationship from client"""
    client = _get_client_or_404(client_id)

    relationship = db_session.query(ClientProjectRelationship).filter_by(
        client_id=client_id,
        project_id=project_id
    ).first()

    if relationship:
        db_session.delete(relationship)
        db_session.commit()
        flash('Project relationship removed', 'success')
    else:
        flash('Relationship not found', 'error')

    return redirect(url_for('clients.view_client', client_id=client_id))


@bp.route('/<int:client_id>/relationships/vendor/add', methods=['GET', 'POST'])
@login_required
def add_vendor_relationship(client_id):
    """Add technology vendor relationship to client"""
    client = _get_client_or_404(client_id)

    # Get all vendors for dropdown
    vendors = db_session.query(TechnologyVendor).order_by(TechnologyVendor.vendor_name).all()
    vendor_choices = [(v.vendor_id, v.vendor_name) for v in vendors]

    form = ClientVendorRelationshipForm(vendor_choices=vendor_choices)

    if form.validate_on_submit():
        try:
            # Check if relationship already exists
            existing = db_session.query(ClientVendorRelationship).filter_by(
                client_id=client_id,
                vendor_id=form.vendor_id.data
            ).first()

            if existing:
                flash('This technology vendor is already linked to this client', 'warning')
            else:
                relationship = ClientVendorRelationship(
                    client_id=client_id,
                    vendor_id=form.vendor_id.data,
                    notes=form.notes.data,
                    created_by=current_user.user_id
                )
                db_session.add(relationship)
                db_session.commit()
                flash('Technology vendor linked successfully', 'success')

            return redirect(url_for('clients.view_client', client_id=client_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error linking technology vendor: {str(e)}', 'error')

    return render_template('clients/add_relationship.html',
                         client=client,
                         form=form,
                         relationship_type='Technology Vendor')


@bp.route('/<int:client_id>/relationships/vendor/<int:vendor_id>/remove', methods=['POST'])
@login_required
def remove_vendor_relationship(client_id, vendor_id):
    """Remove technology vendor relationship from client"""
    client = _get_client_or_404(client_id)

    relationship = db_session.query(ClientVendorRelationship).filter_by(
        client_id=client_id,
        vendor_id=vendor_id
    ).first()

    if relationship:
        db_session.delete(relationship)
        db_session.commit()
        flash('Technology vendor relationship removed', 'success')
    else:
        flash('Relationship not found', 'error')

    return redirect(url_for('clients.view_client', client_id=client_id))


@bp.route('/<int:client_id>/relationships/operator/add', methods=['GET', 'POST'])
@login_required
def add_operator_relationship(client_id):
    """Add operator relationship to client"""
    client = _get_client_or_404(client_id)

    # Get all operators for dropdown
    operators = db_session.query(Operator).order_by(Operator.company_name).all()
    operator_choices = [(op.operator_id, op.company_name) for op in operators]

    form = ClientOperatorRelationshipForm(operator_choices=operator_choices)

    if form.validate_on_submit():
        try:
            # Check if relationship already exists
            existing = db_session.query(ClientOperatorRelationship).filter_by(
                client_id=client_id,
                operator_id=form.operator_id.data
            ).first()

            if existing:
                flash('This operator is already linked to this client', 'warning')
            else:
                relationship = ClientOperatorRelationship(
                    client_id=client_id,
                    operator_id=form.operator_id.data,
                    notes=form.notes.data,
                    created_by=current_user.user_id
                )
                db_session.add(relationship)
                db_session.commit()
                flash('Operator linked successfully', 'success')

            return redirect(url_for('clients.view_client', client_id=client_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error linking operator: {str(e)}', 'error')

    return render_template('clients/add_relationship.html',
                         client=client,
                         form=form,
                         relationship_type='Operator')


@bp.route('/<int:client_id>/relationships/operator/<int:operator_id>/remove', methods=['POST'])
@login_required
def remove_operator_relationship(client_id, operator_id):
    """Remove operator relationship from client"""
    client = _get_client_or_404(client_id)

    relationship = db_session.query(ClientOperatorRelationship).filter_by(
        client_id=client_id,
        operator_id=operator_id
    ).first()

    if relationship:
        db_session.delete(relationship)
        db_session.commit()
        flash('Operator relationship removed', 'success')
    else:
        flash('Relationship not found', 'error')

    return redirect(url_for('clients.view_client', client_id=client_id))


@bp.route('/<int:client_id>/relationships/personnel/add', methods=['GET', 'POST'])
@login_required
def add_personnel_relationship(client_id):
    """Add key personnel relationship to client"""
    client = _get_client_or_404(client_id)

    # Get all external personnel for dropdown (excluding Internal MPR staff)
    personnel = db_session.query(Personnel).filter(
        Personnel.personnel_type != 'Internal'
    ).order_by(Personnel.full_name).all()
    personnel_choices = [(p.personnel_id, f"{p.full_name} ({p.personnel_type})") for p in personnel]

    form = ClientPersonnelRelationshipForm(personnel_choices=personnel_choices)

    if form.validate_on_submit():
        try:
            # Check if relationship already exists
            existing = db_session.query(ClientPersonnelRelationship).filter_by(
                client_id=client_id,
                personnel_id=form.personnel_id.data
            ).first()

            if existing:
                flash('This person is already linked to this client', 'warning')
            else:
                relationship = ClientPersonnelRelationship(
                    client_id=client_id,
                    personnel_id=form.personnel_id.data,
                    role_at_client=form.role_at_client.data,
                    is_primary_contact=form.is_primary_contact.data,
                    mpr_relationship_strength=form.mpr_relationship_strength.data,
                    notes=form.notes.data,
                    created_by=current_user.user_id
                )
                db_session.add(relationship)
                db_session.commit()
                flash('Key personnel linked successfully', 'success')

            return redirect(url_for('clients.view_client', client_id=client_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error linking personnel: {str(e)}', 'error')

    return render_template('clients/add_relationship.html',
                         client=client,
                         form=form,
                         relationship_type='Key Personnel')


@bp.route('/<int:client_id>/relationships/personnel/<int:personnel_id>/remove', methods=['POST'])
@login_required
def remove_personnel_relationship(client_id, personnel_id):
    """Remove personnel relationship from client"""
    client = _get_client_or_404(client_id)

    relationship = db_session.query(ClientPersonnelRelationship).filter_by(
        client_id=client_id,
        personnel_id=personnel_id
    ).first()

    if relationship:
        db_session.delete(relationship)
        db_session.commit()
        flash('Key personnel relationship removed', 'success')
    else:
        flash('Relationship not found', 'error')

    return redirect(url_for('clients.view_client', client_id=client_id))
