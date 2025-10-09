"""Personnel list and management routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app import db_session
from app.models import (
    Personnel,  # Keep for backward compatibility
    InternalPersonnel,
    ExternalPersonnel,
    PersonnelRelationship,
    Company,
    Project,
    Client,
    ContactLog,
    ClientPersonnelRelationship,
    ClientProfile,
    PersonCompanyAffiliation,
)
from app.models.relationships import PersonnelEntityRelationship, EntityTeamMember
from app.forms.personnel import PersonnelForm, PersonnelClientLinkForm, PersonnelRelationshipForm
from app.forms.relationships import ConfirmActionForm


bp = Blueprint('personnel', __name__, url_prefix='/personnel')


def _unique_people(people):
    seen = set()
    unique = []
    for person in people:
        if not person:
            continue
        pid = person.personnel_id
        if pid in seen:
            continue
        seen.add(pid)
        unique.append(person)
    return unique


def _gather_external_contacts_for_internal(person: InternalPersonnel) -> list[dict]:
    # Note: Internal personnel client relationships will be updated separately
    # For now, return empty list since the old client relationships are not migrated
    return []


_ORG_ROUTE_MAP = {
    'Client': ('companies.view_company', 'company_id', Company, 'company_name'),
    'Company': ('companies.view_company', 'company_id', Company, 'company_name'),
    # Legacy entity types mapped to unified company route
    'Owner': ('companies.view_company', 'company_id', Company, 'company_name'),
    'Developer': ('companies.view_company', 'company_id', Company, 'company_name'),
    'Vendor': ('companies.view_company', 'company_id', Company, 'company_name'),
    'Operator': ('companies.view_company', 'company_id', Company, 'company_name'),
    'Constructor': ('companies.view_company', 'company_id', Company, 'company_name'),
    'Offtaker': ('companies.view_company', 'company_id', Company, 'company_name'),
}


def _gather_company_links_for_external(person: ExternalPersonnel) -> list[dict]:
    links = []
    
    # Check for direct company relationship
    if person.company_id and person.company:
        links.append({
            'name': person.company.company_name,
            'url': url_for('companies.view_company', company_id=person.company_id)
        })

    return links


def _query_personnel(search_term: str | None, include_internal: bool | None):
    """Return personnel filtered by optional search term and type."""
    if include_internal is True:
        # Query internal personnel
        query = db_session.query(InternalPersonnel)
        if search_term:
            like_term = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    InternalPersonnel.full_name.ilike(like_term),
                    InternalPersonnel.email.ilike(like_term),
                    InternalPersonnel.role.ilike(like_term),
                )
            )
        return query.order_by(InternalPersonnel.full_name).all()
    
    elif include_internal is False:
        # Query external personnel
        query = db_session.query(ExternalPersonnel).options(
            joinedload(ExternalPersonnel.company)
        )
        if search_term:
            like_term = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    ExternalPersonnel.full_name.ilike(like_term),
                    ExternalPersonnel.email.ilike(like_term),
                    ExternalPersonnel.role.ilike(like_term),
                )
            )
        return query.order_by(ExternalPersonnel.full_name).all()
    
    else:
        # Return empty list if neither internal nor external specified
        return []


@bp.route('/')
@login_required
def list_personnel():
    """List internal and external personnel with optional search."""
    search_term = request.args.get('q', '').strip()

    internal_personnel = _query_personnel(search_term, include_internal=True)
    external_personnel = _query_personnel(search_term, include_internal=False)

    internal_connections = {
        person.personnel_id: _gather_external_contacts_for_internal(person)
        for person in internal_personnel
    }

    external_company_links = {
        person.personnel_id: _gather_company_links_for_external(person)
        for person in external_personnel
    }

    return render_template(
        'personnel/list.html',
        search_term=search_term,
        internal_personnel=internal_personnel,
        external_personnel=external_personnel,
        delete_form=ConfirmActionForm(),
        can_delete=current_user.is_admin,
        internal_connections=internal_connections,
        external_company_links=external_company_links,
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_personnel():
    """Create a new external personnel record."""
    from app.models import Company
    from app.forms.personnel import ExternalPersonnelForm
    
    # Get company choices
    companies = db_session.query(Company).order_by(Company.company_name).all()
    company_choices = [(company.company_id, company.company_name) for company in companies]

    form = ExternalPersonnelForm()
    form.company_id.choices = company_choices

    if form.validate_on_submit():
        try:
            person = ExternalPersonnel(
                full_name=form.full_name.data,
                email=form.email.data or None,
                phone=form.phone.data or None,
                role=form.role.data or None,
                company_id=form.company_id.data,
                is_active=bool(form.is_active.data),
                notes=form.notes.data or None,
                created_by=current_user.user_id,
                modified_by=current_user.user_id,
            )

            db_session.add(person)
            db_session.commit()
            flash('External personnel record created successfully.', 'success')
            return redirect(url_for('personnel.list_personnel'))
        except Exception as exc:
            db_session.rollback()
            flash(f'Error creating personnel record: {exc}', 'danger')

    return render_template('personnel/create.html', form=form)


@bp.route('/<int:personnel_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_personnel(personnel_id: int):
    """Edit a personnel record."""
    from app.models import Company
    from app.forms.personnel import InternalPersonnelForm, ExternalPersonnelForm
    
    # Check if personnel_type is specified in query params to determine which table to check
    personnel_type = request.args.get('type', '').lower()
    
    person = None
    is_internal = None
    
    if personnel_type == 'internal':
        # Look in internal personnel only
        person = db_session.get(InternalPersonnel, personnel_id)
        is_internal = person is not None
    elif personnel_type == 'external':
        # Look in external personnel only
        person = db_session.get(ExternalPersonnel, personnel_id)
        is_internal = False
    else:
        # Try both tables - this is the problematic case with overlapping IDs
        # First try internal
        person = db_session.get(InternalPersonnel, personnel_id)
        if person:
            is_internal = True
        else:
            # Try external
            person = db_session.get(ExternalPersonnel, personnel_id)
            if person:
                is_internal = False
    
    if not person:
        flash('Personnel record not found.', 'error')
        return redirect(url_for('personnel.list_personnel'))
    
    # Get company choices for external personnel
    companies = db_session.query(Company).order_by(Company.company_name).all()
    company_choices = [(company.company_id, company.company_name) for company in companies]

    if is_internal:
        form = InternalPersonnelForm(obj=person)
        relationship_form = None
        relationships = []
    else:
        form = ExternalPersonnelForm(obj=person)
        form.company_id.choices = company_choices
        # Set current company if person has company_id
        if person.company_id:
            form.company_id.data = person.company_id
        # Force form to process request data for proper company_id binding
        if request.method == 'POST':
            form.company_id.process(request.form)
        
        # Personnel relationships feature not yet implemented - table doesn't exist
        relationships = []
        relationship_form = None

    if form.validate_on_submit():
        person.full_name = form.full_name.data
        person.email = form.email.data or None
        person.phone = form.phone.data or None
        person.role = form.role.data or None
        person.is_active = bool(form.is_active.data)
        person.notes = form.notes.data or None
        
        if is_internal:
            # Update internal-specific fields
            person.department = form.department.data or None
        else:
            # Update external-specific fields
            # Company is required for external personnel
            person.company_id = form.company_id.data

        try:
            db_session.commit()
            flash(f'{person.full_name} updated successfully.', 'success')
            return redirect(url_for('personnel.list_personnel'))
        except Exception as exc:
            db_session.rollback()
            flash(f'Error updating personnel: {exc}', 'danger')
    
    # Personnel relationships feature not yet implemented - table doesn't exist
    # Relationship form submission disabled until personnel_relationships table is created
    
    return render_template('personnel/edit.html', 
                         form=form, 
                         person=person, 
                         is_internal=is_internal,
                         relationship_form=relationship_form,
                         relationships=relationships)


@bp.route('/<int:personnel_id>/relationships/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_personnel_relationship(personnel_id: int, relationship_id: int):
    """Delete a personnel relationship."""
    # Personnel relationships feature not yet implemented - table doesn't exist
    flash('Personnel relationships feature is not yet available.', 'warning')
    return redirect(url_for('personnel.edit_personnel', personnel_id=personnel_id, type='external'))


@bp.route('/<int:personnel_id>/clients', methods=['GET', 'POST'])
@login_required
def manage_personnel_clients(personnel_id: int):
    """View and manage client relationships for the selected personnel."""
    person = db_session.get(Personnel, personnel_id)
    if not person:
        flash('Personnel record not found.', 'error')
        return redirect(url_for('personnel.list_personnel'))

    clients = db_session.query(Client).order_by(Client.client_name).all()
    client_choices = [(client.client_id, client.client_name) for client in clients]

    form = PersonnelClientLinkForm(client_choices=client_choices)
    delete_form = ConfirmActionForm()

    if form.validate_on_submit():
        existing = (
            db_session.query(ClientPersonnelRelationship)
            .filter_by(client_id=form.client_id.data, personnel_id=personnel_id)
            .first()
        )
        if existing:
            flash('This client is already linked to the selected person.', 'warning')
        else:
            relationship = ClientPersonnelRelationship(
                client_id=form.client_id.data,
                personnel_id=personnel_id,
                role_at_client=form.role_at_client.data or None,
                is_primary_contact=bool(form.is_primary_contact.data),
                is_confidential=bool(form.is_confidential.data),
                notes=form.notes.data or None,
                created_by=current_user.user_id,
                modified_by=current_user.user_id,
            )
            db_session.add(relationship)
            db_session.commit()
            flash('Client relationship added.', 'success')
            return redirect(url_for('personnel.manage_personnel_clients', personnel_id=personnel_id))

    relationships = (
        db_session.query(ClientPersonnelRelationship)
        .options(joinedload(ClientPersonnelRelationship.client))
        .filter_by(personnel_id=personnel_id)
        .order_by(ClientPersonnelRelationship.is_primary_contact.desc(), ClientPersonnelRelationship.role_at_client)
        .all()
    )

    return render_template(
        'personnel/manage_clients.html',
        person=person,
        relationships=relationships,
        form=form,
        delete_form=delete_form,
    )


@bp.route('/<int:personnel_id>/clients/<int:relationship_id>/remove', methods=['POST'])
@login_required
def remove_personnel_client(personnel_id: int, relationship_id: int):
    person = db_session.get(Personnel, personnel_id)
    if not person:
        flash('Personnel record not found.', 'error')
        return redirect(url_for('personnel.list_personnel'))

    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Removal request was not confirmed.', 'error')
        return redirect(url_for('personnel.manage_personnel_clients', personnel_id=personnel_id))

    relationship = db_session.get(ClientPersonnelRelationship, relationship_id)
    if not relationship or relationship.personnel_id != personnel_id:
        flash('Client relationship not found.', 'error')
        return redirect(url_for('personnel.manage_personnel_clients', personnel_id=personnel_id))

    db_session.delete(relationship)
    db_session.commit()
    flash('Client relationship removed.', 'success')
    return redirect(url_for('personnel.manage_personnel_clients', personnel_id=personnel_id))


class PersonnelDeletionError(Exception):
    """Raised when a personnel record cannot be safely deleted."""


def _cleanup_personnel_references(personnel_id: int) -> None:
    """Clear nullable references and remove dependent records before deletion.

    Raises:
        PersonnelDeletionError: if non-nullable references block deletion.
    """
    blocking_logs = (
        db_session.query(ContactLog)
        .filter(ContactLog.contacted_by == personnel_id)
        .count()
    )
    if blocking_logs:
        raise PersonnelDeletionError(
            f'Cannot delete personnel; they are listed as the contacting party in {blocking_logs} contact log(s). '
            'Reassign or remove those contact logs first.'
        )

    # Null out references in client profiles, projects, clients (legacy), and contact logs
    # Update ClientProfile records that reference this personnel
    client_profile_updates = {
        ClientProfile.last_contact_by: None,
        ClientProfile.next_planned_contact_assigned_to: None,
    }
    for column in client_profile_updates:
        db_session.query(ClientProfile).filter(column == personnel_id).update({column: None}, synchronize_session=False)

    project_updates = {
        Project.primary_firm_contact: None,
        Project.last_project_interaction_by: None,
    }
    for column in project_updates:
        db_session.query(Project).filter(column == personnel_id).update({column: None}, synchronize_session=False)

    # Legacy Client table (if still in use)
    client_updates = {
        Client.mpr_primary_poc: None,
        Client.mpr_secondary_poc: None,
        Client.last_contact_by: None,
        Client.next_planned_contact_assigned_to: None,
    }
    for column in client_updates:
        db_session.query(Client).filter(column == personnel_id).update({column: None}, synchronize_session=False)

    db_session.query(ContactLog).filter(ContactLog.contact_person_id == personnel_id).update({ContactLog.contact_person_id: None}, synchronize_session=False)
    db_session.query(ContactLog).filter(ContactLog.follow_up_assigned_to == personnel_id).update({ContactLog.follow_up_assigned_to: None}, synchronize_session=False)

    # Remove junction-table relationships that point at this personnel
    db_session.query(PersonnelEntityRelationship).filter_by(personnel_id=personnel_id).delete(synchronize_session=False)
    db_session.query(PersonCompanyAffiliation).filter_by(personnel_id=personnel_id).delete(synchronize_session=False)
    db_session.query(EntityTeamMember).filter_by(personnel_id=personnel_id).delete(synchronize_session=False)
    db_session.query(ClientPersonnelRelationship).filter_by(personnel_id=personnel_id).delete(synchronize_session=False)


@bp.route('/<int:personnel_id>/delete', methods=['POST'])
@login_required
def delete_personnel(personnel_id: int):
    """Delete a personnel record after clearing dependent references."""
    if not current_user.is_admin:
        flash('Only administrators may delete personnel records.', 'error')
        return redirect(url_for('personnel.list_personnel'))

    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Deletion request was not confirmed.', 'error')
        return redirect(url_for('personnel.list_personnel'))

    person = db_session.get(Personnel, personnel_id)
    if not person:
        flash('Personnel record not found.', 'error')
        return redirect(url_for('personnel.list_personnel'))

    try:
        _cleanup_personnel_references(personnel_id)
        db_session.delete(person)
        db_session.commit()
        flash('Personnel record deleted.', 'success')
    except PersonnelDeletionError as exc:
        db_session.rollback()
        flash(str(exc), 'error')
    except Exception as exc:  # pragma: no cover - safeguard
        db_session.rollback()
        flash(f'Unable to delete personnel record: {exc}', 'error')

    return redirect(url_for('personnel.list_personnel'))
