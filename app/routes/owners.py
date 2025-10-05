"""Owner/Developer routes (CRUD operations and relationship management)"""
from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.models import (
    OwnerDeveloper,
    OwnerVendorRelationship,
    ProjectOwnerRelationship,
    PersonnelEntityRelationship,
    EntityTeamMember,
    ContactLog,
    RoundtableHistory
)
from app.forms.relationships import (
    OwnerVendorRelationshipForm,
    OwnerProjectRelationshipForm,
    PersonnelEntityRelationshipForm,
    EntityTeamMemberForm,
    TeamAssignmentToggleForm,
    ConfirmActionForm
)
from app.forms.roundtable import RoundtableEntryForm
from app.forms.owners import OwnerDeveloperForm
from app import db_session
from app.utils.permissions import filter_relationships, can_view_relationship, ned_team_required
from app.utils.system_settings import get_roundtable_history_limit, enforce_roundtable_history_limit
from app.routes.relationship_utils import (
    get_vendor_choices,
    get_project_choices,
    get_personnel_choices
)
from app.services.company_sync import sync_company_from_owner
from app.services.company_query import get_company_for_owner
from app.services.company_query import get_company_for_owner

bp = Blueprint('owners', __name__, url_prefix='/owners')


def _get_owner_or_404(owner_id: int) -> OwnerDeveloper:
    owner = db_session.get(OwnerDeveloper, owner_id)
    if not owner:
        flash('Owner/Developer not found', 'error')
        abort(404)
    return owner


def _can_manage_relationships(user) -> bool:
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


@bp.route('/')
@login_required
def list_owners():
    """List all owners/developers"""
    owners = db_session.query(OwnerDeveloper).order_by(OwnerDeveloper.company_name).all()
    owner_company_map = {
        owner.owner_id: get_company_for_owner(owner.owner_id)
        for owner in owners
    }
    return render_template(
        'owners/list.html',
        owners=owners,
        can_manage=_can_manage_relationships(current_user),
        owner_company_map=owner_company_map,
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_owner():
    """Create a new owner/developer"""
    if not _can_manage_relationships(current_user):
        flash('You do not have permission to create owners.', 'danger')
        return redirect(url_for('owners.list_owners'))

    form = OwnerDeveloperForm()

    if form.validate_on_submit():
        owner = OwnerDeveloper(
            company_name=form.company_name.data,
            company_type=form.company_type.data or None,
            engagement_level=form.engagement_level.data or None,
            client_status=form.client_status.data or None,
            client_priority=form.client_priority.data or None,
            notes=form.notes.data or None,
            created_by=current_user.user_id,
            modified_by=current_user.user_id,
        )
        owner.modified_date = datetime.utcnow()

        try:
            db_session.add(owner)
            db_session.flush()
            sync_company_from_owner(owner, current_user.user_id)
            db_session.commit()
            flash('Owner/Developer created successfully.', 'success')
            return redirect(url_for('owners.view_owner', owner_id=owner.owner_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error creating owner/developer: {exc}', 'danger')

    return render_template(
        'owners/form.html',
        form=form,
        owner=None,
        title='Create Owner/Developer'
    )


@bp.route('/<int:owner_id>')
@login_required
def view_owner(owner_id):
    """View owner details"""
    owner = _get_owner_or_404(owner_id)

    vendor_relationships = filter_relationships(current_user, owner.vendor_relationships)
    project_relationships = filter_relationships(current_user, owner.project_relationships)
    personnel_relationships = filter_relationships(
        current_user,
        db_session.query(PersonnelEntityRelationship).filter_by(entity_type='Owner', entity_id=owner.owner_id)
    )

    contact_logs_query = db_session.query(ContactLog).filter_by(entity_type='Owner', entity_id=owner.owner_id).order_by(ContactLog.contact_date.desc(), ContactLog.contact_id.desc())
    contact_logs_all = contact_logs_query.all()
    visible_contacts = [log for log in contact_logs_all if can_view_relationship(current_user, log)]
    hidden_contacts_count = max(len(contact_logs_all) - len(visible_contacts), 0)
    recent_contacts = visible_contacts[:5]

    roundtable_entries = []
    roundtable_limit = get_roundtable_history_limit()
    can_view_roundtable = current_user.is_admin or getattr(current_user, 'is_ned_team', False)
    if can_view_roundtable:
        roundtable_entries = db_session.query(RoundtableHistory).filter_by(
            entity_type='Owner',
            entity_id=owner.owner_id
        ).order_by(RoundtableHistory.meeting_date.desc(), RoundtableHistory.history_id.desc()).limit(roundtable_limit).all()

    team_assignments = db_session.query(EntityTeamMember).filter_by(
        entity_type='Owner',
        entity_id=owner.owner_id
    ).order_by(EntityTeamMember.is_active.desc(), EntityTeamMember.assigned_date.desc().nullslast()).all()

    can_manage = _can_manage_relationships(current_user)
    company_record = get_company_for_owner(owner.owner_id)

    vendor_form = project_form = personnel_form = team_form = None
    if can_manage:
        vendor_form = OwnerVendorRelationshipForm()
        vendor_form.vendor_id.choices = get_vendor_choices()

        project_form = OwnerProjectRelationshipForm()
        project_form.project_id.choices = get_project_choices()

        personnel_form = PersonnelEntityRelationshipForm()
        personnel_form.personnel_id.choices = get_personnel_choices()

        team_form = EntityTeamMemberForm()
        team_form.personnel_id.choices = get_personnel_choices(internal_only=True, placeholder='-- Select Internal Personnel --')

    return render_template(
        'owners/detail.html',
        owner=owner,
        company_record=company_record,
        vendor_relationships=vendor_relationships,
        project_relationships=project_relationships,
        personnel_relationships=personnel_relationships,
        team_assignments=team_assignments,
        vendor_form=vendor_form,
        project_form=project_form,
        personnel_form=personnel_form,
        team_form=team_form,
        toggle_form=TeamAssignmentToggleForm(),
        delete_form=ConfirmActionForm(),
        can_manage_relationships=can_manage,
        recent_contacts=recent_contacts,
        hidden_contacts_count=hidden_contacts_count,
        total_contact_logs=len(visible_contacts),
        roundtable_entries=roundtable_entries,
        roundtable_limit=roundtable_limit,
        can_view_roundtable=can_view_roundtable
    )


@bp.route('/<int:owner_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_owner(owner_id):
    """Edit owner/developer details"""
    owner = _get_owner_or_404(owner_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to edit owners.', 'danger')
        return redirect(url_for('owners.view_owner', owner_id=owner_id))

    form = OwnerDeveloperForm(obj=owner)

    if not form.is_submitted():
        form.company_type.data = owner.company_type or ''
        form.engagement_level.data = owner.engagement_level or ''
        form.client_status.data = owner.client_status or ''
        form.client_priority.data = owner.client_priority or ''

    if form.validate_on_submit():
        owner.company_name = form.company_name.data
        owner.company_type = form.company_type.data or None
        owner.engagement_level = form.engagement_level.data or None
        owner.client_status = form.client_status.data or None
        owner.client_priority = form.client_priority.data or None
        owner.notes = form.notes.data or None
        owner.modified_by = current_user.user_id
        owner.modified_date = datetime.utcnow()

        try:
            sync_company_from_owner(owner, current_user.user_id)
            db_session.commit()
            flash('Owner/Developer updated successfully.', 'success')
            return redirect(url_for('owners.view_owner', owner_id=owner.owner_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error updating owner/developer: {exc}', 'danger')

    return render_template(
        'owners/form.html',
        form=form,
        owner=owner,
        title=f'Edit Owner/Developer: {owner.company_name}'
    )


@bp.route('/<int:owner_id>/relationships/vendors', methods=['POST'])
@login_required
def add_owner_vendor_relationship(owner_id):
    owner = _get_owner_or_404(owner_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('owners.view_owner', owner_id=owner_id))

    form = OwnerVendorRelationshipForm()
    form.vendor_id.choices = get_vendor_choices()

    if form.validate_on_submit():
        vendor_id = form.vendor_id.data
        if vendor_id == 0:
            flash('Please select a vendor.', 'warning')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        existing = db_session.query(OwnerVendorRelationship).filter_by(
            owner_id=owner.owner_id,
            vendor_id=vendor_id
        ).first()

        if existing:
            flash('This vendor relationship already exists.', 'info')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        relationship = OwnerVendorRelationship(
            owner_id=owner.owner_id,
            vendor_id=vendor_id,
            relationship_type=form.relationship_type.data or None,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Vendor relationship added.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error adding vendor relationship: {exc}', 'danger')
    else:
        flash('Unable to add vendor relationship. Please check the form inputs.', 'danger')

    return redirect(url_for('owners.view_owner', owner_id=owner_id))


@bp.route('/<int:owner_id>/relationships/vendors/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_owner_vendor_relationship(owner_id, relationship_id):
    _get_owner_or_404(owner_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('owners.view_owner', owner_id=owner_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(OwnerVendorRelationship, relationship_id)
        if not relationship or relationship.owner_id != owner_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Vendor relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing vendor relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('owners.view_owner', owner_id=owner_id))


@bp.route('/<int:owner_id>/relationships/projects', methods=['POST'])
@login_required
def add_owner_project_relationship(owner_id):
    owner = _get_owner_or_404(owner_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('owners.view_owner', owner_id=owner_id))

    form = OwnerProjectRelationshipForm()
    form.project_id.choices = get_project_choices()

    if form.validate_on_submit():
        project_id = form.project_id.data
        if project_id == 0:
            flash('Please select a project.', 'warning')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        existing = db_session.query(ProjectOwnerRelationship).filter_by(
            project_id=project_id,
            owner_id=owner.owner_id
        ).first()

        if existing:
            flash('This project relationship already exists.', 'info')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        relationship = ProjectOwnerRelationship(
            project_id=project_id,
            owner_id=owner.owner_id,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Project relationship added.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error adding project relationship: {exc}', 'danger')
    else:
        flash('Unable to add project relationship. Please check the form inputs.', 'danger')

    return redirect(url_for('owners.view_owner', owner_id=owner_id))


@bp.route('/<int:owner_id>/relationships/projects/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_owner_project_relationship(owner_id, relationship_id):
    _get_owner_or_404(owner_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('owners.view_owner', owner_id=owner_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(ProjectOwnerRelationship, relationship_id)
        if not relationship or relationship.owner_id != owner_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Project relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing project relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('owners.view_owner', owner_id=owner_id))


@bp.route('/<int:owner_id>/relationships/personnel', methods=['POST'])
@login_required
def add_owner_personnel_relationship(owner_id):
    owner = _get_owner_or_404(owner_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('owners.view_owner', owner_id=owner_id))

    form = PersonnelEntityRelationshipForm()
    form.personnel_id.choices = get_personnel_choices()

    if form.validate_on_submit():
        personnel_id = form.personnel_id.data
        if personnel_id == 0:
            flash('Please select personnel.', 'warning')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        existing = db_session.query(PersonnelEntityRelationship).filter_by(
            personnel_id=personnel_id,
            entity_type='Owner',
            entity_id=owner.owner_id
        ).first()

        if existing:
            flash('This personnel relationship already exists.', 'info')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        relationship = PersonnelEntityRelationship(
            personnel_id=personnel_id,
            entity_type='Owner',
            entity_id=owner.owner_id,
            role_at_entity=form.role_at_entity.data or None,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Personnel relationship added.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error adding personnel relationship: {exc}', 'danger')
    else:
        flash('Unable to add personnel relationship. Please check the form inputs.', 'danger')

    return redirect(url_for('owners.view_owner', owner_id=owner_id))


@bp.route('/<int:owner_id>/relationships/personnel/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_owner_personnel_relationship(owner_id, relationship_id):
    _get_owner_or_404(owner_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('owners.view_owner', owner_id=owner_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(PersonnelEntityRelationship, relationship_id)
        if not relationship or relationship.entity_type != 'Owner' or relationship.entity_id != owner_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Personnel relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing personnel relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('owners.view_owner', owner_id=owner_id))


@bp.route('/<int:owner_id>/team', methods=['POST'])
@login_required
def add_owner_team_assignment(owner_id):
    owner = _get_owner_or_404(owner_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify team assignments.', 'danger')
        return redirect(url_for('owners.view_owner', owner_id=owner_id))

    form = EntityTeamMemberForm()
    form.personnel_id.choices = get_personnel_choices(internal_only=True, placeholder='-- Select Internal Personnel --')

    if form.validate_on_submit():
        personnel_id = form.personnel_id.data
        if personnel_id == 0:
            flash('Please select team personnel.', 'warning')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        assignment = db_session.query(EntityTeamMember).filter_by(
            entity_type='Owner',
            entity_id=owner.owner_id,
            personnel_id=personnel_id
        ).first()

        if assignment:
            assignment.assignment_type = form.assignment_type.data or None
            assignment.assigned_date = form.assigned_date.data
            assignment.is_active = form.is_active.data
        else:
            assignment = EntityTeamMember(
                entity_type='Owner',
                entity_id=owner.owner_id,
                personnel_id=personnel_id,
                assignment_type=form.assignment_type.data or None,
                assigned_date=form.assigned_date.data,
                is_active=form.is_active.data
            )
            db_session.add(assignment)

        try:
            db_session.commit()
            flash('Team assignment saved.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error saving team assignment: {exc}', 'danger')
    else:
        flash('Unable to save team assignment. Please check the form inputs.', 'danger')

    return redirect(url_for('owners.view_owner', owner_id=owner_id))


@bp.route('/<int:owner_id>/team/<int:assignment_id>/toggle', methods=['POST'])
@login_required
def toggle_owner_team_assignment(owner_id, assignment_id):
    _get_owner_or_404(owner_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify team assignments.', 'danger')
        return redirect(url_for('owners.view_owner', owner_id=owner_id))

    form = TeamAssignmentToggleForm()

    if form.validate_on_submit() and form.assignment_id.data == str(assignment_id):
        assignment = db_session.get(EntityTeamMember, assignment_id)
        if not assignment or assignment.entity_type != 'Owner' or assignment.entity_id != owner_id:
            flash('Team assignment not found.', 'error')
            return redirect(url_for('owners.view_owner', owner_id=owner_id))

        assignment.is_active = not assignment.is_active

        try:
            db_session.commit()
            state = 'activated' if assignment.is_active else 'deactivated'
            flash(f'Team assignment {state}.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error updating team assignment: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('owners.view_owner', owner_id=owner_id))


@bp.route('/<int:owner_id>/roundtable/add', methods=['GET', 'POST'])
@login_required
@ned_team_required
def add_roundtable_entry(owner_id):
    owner = _get_owner_or_404(owner_id)

    form = RoundtableEntryForm()
    if request.method == 'GET':
        form.meeting_date.data = date.today()

    if form.validate_on_submit():
        entry = RoundtableHistory(
            entity_type='Owner',
            entity_id=owner.owner_id,
            meeting_date=form.meeting_date.data,
            discussion=form.discussion.data,
            action_items=form.action_items.data,
            created_by=current_user.user_id
        )

        try:
            db_session.add(entry)
            db_session.commit()
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error saving roundtable entry: {exc}', 'danger')
            return render_template('owners/roundtable_form.html', owner=owner, form=form, roundtable_limit=get_roundtable_history_limit(), today=date.today().isoformat())

        enforce_roundtable_history_limit('Owner', owner.owner_id)

        flash('Roundtable entry saved.', 'success')
        return redirect(url_for('owners.view_owner', owner_id=owner.owner_id))

    return render_template('owners/roundtable_form.html', owner=owner, form=form, roundtable_limit=get_roundtable_history_limit(), today=date.today().isoformat())
