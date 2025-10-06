"""Personnel list and management routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app import db_session
from app.models import (
    Personnel,
    OwnerDeveloper,
    Project,
    Client,
    ContactLog,
    ClientPersonnelRelationship,
    TechnologyVendor,
    Operator,
    Offtaker,
)
from app.models.relationships import PersonnelEntityRelationship, EntityTeamMember
from app.forms.personnel import PersonnelForm, PersonnelClientLinkForm
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


def _gather_external_contacts_for_internal(person: Personnel) -> list[dict]:
    linked_clients = set()
    for attr in (
        'clients_as_primary_poc',
        'clients_as_secondary_poc',
        'last_contacted_clients',
        'assigned_next_client_contacts'
    ):
        linked_clients.update(getattr(person, attr, []) or [])

    external_people = []
    for client in linked_clients:
        for rel in client.personnel_relationships:
            ext = rel.person
            if not ext or ext.personnel_type == 'Internal' or ext.personnel_id == person.personnel_id:
                continue
            external_people.append(ext)

    external_people = _unique_people(external_people)
    return [
        {
            'name': ext.full_name,
            'url': url_for('personnel.edit_personnel', personnel_id=ext.personnel_id)
        }
        for ext in external_people
    ]


_ORG_ROUTE_MAP = {
    'Client': ('clients.view_client', 'client_id', Client, 'client_name'),
    'Owner': ('owners.view_owner', 'owner_id', OwnerDeveloper, 'company_name'),
    'Vendor': ('vendors.view_vendor', 'vendor_id', TechnologyVendor, 'vendor_name'),
    'Operator': ('operators.view_operator', 'operator_id', Operator, 'company_name'),
    'Offtaker': ('offtakers.view_offtaker', 'offtaker_id', Offtaker, 'organization_name'),
}


def _gather_company_links_for_external(person: Personnel) -> list[dict]:
    links = []
    org_type = person.organization_type
    org_id = person.organization_id
    if org_type and org_id:
        route_info = _ORG_ROUTE_MAP.get(org_type)
        if route_info:
            endpoint, param_name, model, label_attr = route_info
            entity = db_session.get(model, org_id)
            if entity:
                label = getattr(entity, label_attr, f"{org_type} #{org_id}")
                links.append({'name': label, 'url': url_for(endpoint, **{param_name: org_id})})

    if not links:
        for rel in person.client_relationships:
            if rel.client:
                links.append({
                    'name': rel.client.client_name,
                    'url': url_for('clients.view_client', client_id=rel.client.client_id)
                })

    return links


def _query_personnel(search_term: str | None, include_internal: bool | None) -> list[Personnel]:
    """Return personnel filtered by optional search term and type."""
    query = db_session.query(Personnel).options(
        joinedload(Personnel.client_relationships).joinedload(ClientPersonnelRelationship.client),
        joinedload(Personnel.clients_as_primary_poc)
        .joinedload(Client.personnel_relationships)
        .joinedload(ClientPersonnelRelationship.person),
        joinedload(Personnel.clients_as_secondary_poc)
        .joinedload(Client.personnel_relationships)
        .joinedload(ClientPersonnelRelationship.person),
        joinedload(Personnel.last_contacted_clients)
        .joinedload(Client.personnel_relationships)
        .joinedload(ClientPersonnelRelationship.person),
        joinedload(Personnel.assigned_next_client_contacts)
        .joinedload(Client.personnel_relationships)
        .joinedload(ClientPersonnelRelationship.person),
    )

    if include_internal is True:
        query = query.filter(Personnel.personnel_type == 'Internal')
    elif include_internal is False:
        query = query.filter(Personnel.personnel_type != 'Internal')

    if search_term:
        like_term = f"%{search_term.strip()}%"
        query = query.filter(
            or_(
                Personnel.full_name.ilike(like_term),
                Personnel.email.ilike(like_term),
                Personnel.role.ilike(like_term),
                Personnel.personnel_type.ilike(like_term),
            )
        )

    return query.order_by(Personnel.full_name).all()


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
    """Create a new personnel record."""
    from app.models import Company
    
    # Get company choices
    companies = db_session.query(Company).order_by(Company.company_name).all()
    company_choices = [(0, '-- Select Company --')] + [(company.company_id, company.company_name) for company in companies]

    form = PersonnelForm()
    form.company_id.choices = company_choices

    if form.validate_on_submit():
        person = Personnel(
            full_name=form.full_name.data,
            email=form.email.data or None,
            phone=form.phone.data or None,
            role=form.role.data or None,
            organization_id=form.company_id.data if form.company_id.data else None,
            is_active=bool(form.is_active.data),
            notes=form.notes.data or None,
            created_by=current_user.user_id,
            modified_by=current_user.user_id,
        )

        db_session.add(person)
        db_session.commit()
        flash('Personnel record created.', 'success')
        return redirect(url_for('personnel.list_personnel'))

    return render_template('personnel/create.html', form=form)


@bp.route('/<int:personnel_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_personnel(personnel_id: int):
    """Edit a personnel record."""
    from app.models import Company
    
    person = db_session.get(Personnel, personnel_id)
    if not person:
        flash('Personnel record not found.', 'error')
        return redirect(url_for('personnel.list_personnel'))

    # Get company choices
    companies = db_session.query(Company).order_by(Company.company_name).all()
    company_choices = [(0, '-- Select Company --')] + [(company.company_id, company.company_name) for company in companies]

    form = PersonnelForm(obj=person)
    form.company_id.choices = company_choices
    
    # Set current company if person has organization_id
    if person.organization_id:
        form.company_id.data = person.organization_id

    if form.validate_on_submit():
        person.full_name = form.full_name.data
        person.email = form.email.data or None
        person.phone = form.phone.data or None
        person.role = form.role.data or None
        person.organization_id = form.company_id.data if form.company_id.data else None
        person.is_active = bool(form.is_active.data)
        person.notes = form.notes.data or None
        person.modified_by = current_user.user_id

        db_session.commit()
        flash('Personnel record updated.', 'success')
        return redirect(url_for('personnel.list_personnel'))

    return render_template('personnel/edit.html', form=form, person=person)


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

    # Null out references in owners, projects, clients, and contact logs
    owner_updates = {
        OwnerDeveloper.primary_poc: None,
        OwnerDeveloper.secondary_poc: None,
        OwnerDeveloper.last_contact_by: None,
        OwnerDeveloper.next_planned_contact_assigned_to: None,
    }
    for column in owner_updates:
        db_session.query(OwnerDeveloper).filter(column == personnel_id).update({column: None}, synchronize_session=False)

    project_updates = {
        Project.primary_firm_contact: None,
        Project.last_project_interaction_by: None,
    }
    for column in project_updates:
        db_session.query(Project).filter(column == personnel_id).update({column: None}, synchronize_session=False)

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
