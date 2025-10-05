"""Project routes (CRUD operations and relationship management)"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from datetime import datetime

from app.models import (
    Project,
    ProjectVendorRelationship,
    ProjectConstructorRelationship,
    ProjectOperatorRelationship,
    ProjectOwnerRelationship,
    ProjectOfftakerRelationship,
    PersonnelEntityRelationship,
    EntityTeamMember
)
from app.forms.relationships import (
    ProjectVendorRelationshipForm,
    ProjectConstructorRelationshipForm,
    ProjectOperatorRelationshipForm,
    ProjectOwnerLinkForm,
    ProjectOfftakerRelationshipForm,
    PersonnelEntityRelationshipForm,
    EntityTeamMemberForm,
    TeamAssignmentToggleForm,
    ConfirmActionForm
)
from app.forms.projects import ProjectForm
from app import db_session
from app.utils.permissions import filter_relationships
from app.routes.relationship_utils import (
    get_vendor_choices,
    get_constructor_choices,
    get_operator_choices,
    get_owner_choices,
    get_offtaker_choices,
    get_personnel_choices
)

bp = Blueprint('projects', __name__, url_prefix='/projects')


def _get_project_or_404(project_id: int) -> Project:
    project = db_session.get(Project, project_id)
    if not project:
        flash('Project not found', 'error')
        abort(404)
    return project


def _can_manage_relationships(user) -> bool:
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


@bp.route('/')
@login_required
def list_projects():
    """List all projects"""
    projects = db_session.query(Project).order_by(Project.project_name).all()
    return render_template('projects/list.html', projects=projects, can_manage=_can_manage_relationships(current_user))


@bp.route('/map')
@login_required
def map_view():
    """Interactive map of projects with geocoded coordinates."""
    projects = (
        db_session.query(Project)
        .filter(Project.latitude.isnot(None), Project.longitude.isnot(None))
        .order_by(Project.project_name)
        .all()
    )

    project_markers = []
    for project in projects:
        project_markers.append({
            'id': project.project_id,
            'name': project.project_name,
            'latitude': project.latitude,
            'longitude': project.longitude,
            'status': project.project_status,
            'location': project.location,
            'configuration': project.configuration,
            'target_cod': project.target_cod.strftime('%Y-%m-%d') if project.target_cod else None,
            'url': url_for('projects.view_project', project_id=project.project_id),
            'notes': project.notes,
        })

    return render_template('projects/map.html', projects_data=project_markers)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """Create a new project."""
    if not _can_manage_relationships(current_user):
        flash('You do not have permission to create projects.', 'danger')
        return redirect(url_for('projects.list_projects'))

    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            project_name=form.project_name.data,
            location=form.location.data or None,
            project_status=form.project_status.data or None,
            licensing_approach=form.licensing_approach.data or None,
            configuration=form.configuration.data or None,
            project_schedule=form.project_schedule.data or None,
            target_cod=form.target_cod.data or None,
            latitude=float(form.latitude.data) if form.latitude.data is not None else None,
            longitude=float(form.longitude.data) if form.longitude.data is not None else None,
            notes=form.notes.data or None,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(project)
            db_session.commit()
            flash('Project created successfully.', 'success')
            return redirect(url_for('projects.view_project', project_id=project.project_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error creating project: {exc}', 'danger')

    return render_template('projects/form.html', form=form, project=None, title='Create Project')


@bp.route('/<int:project_id>')
@login_required
def view_project(project_id):
    """View project details"""
    project = _get_project_or_404(project_id)

    vendor_relationships = filter_relationships(current_user, project.vendor_relationships)
    constructor_relationships = filter_relationships(current_user, project.constructor_relationships)
    operator_relationships = filter_relationships(current_user, project.operator_relationships)
    owner_relationships = filter_relationships(current_user, project.owner_relationships)
    offtaker_relationships = filter_relationships(current_user, project.offtaker_relationships)
    personnel_relationships = filter_relationships(
        current_user,
        db_session.query(PersonnelEntityRelationship).filter_by(entity_type='Project', entity_id=project.project_id)
    )

    team_assignments = db_session.query(EntityTeamMember).filter_by(
        entity_type='Project',
        entity_id=project.project_id
    ).order_by(EntityTeamMember.is_active.desc(), EntityTeamMember.assigned_date.desc().nullslast()).all()

    can_manage = _can_manage_relationships(current_user)

    vendor_form = constructor_form = operator_form = owner_form = offtaker_form = personnel_form = team_form = None
    if can_manage:
        vendor_form = ProjectVendorRelationshipForm()
        vendor_form.vendor_id.choices = get_vendor_choices()

        constructor_form = ProjectConstructorRelationshipForm()
        constructor_form.constructor_id.choices = get_constructor_choices()

        operator_form = ProjectOperatorRelationshipForm()
        operator_form.operator_id.choices = get_operator_choices()

        owner_form = ProjectOwnerLinkForm()
        owner_form.owner_id.choices = get_owner_choices()

        offtaker_form = ProjectOfftakerRelationshipForm()
        offtaker_form.offtaker_id.choices = get_offtaker_choices()

        personnel_form = PersonnelEntityRelationshipForm()
        personnel_form.personnel_id.choices = get_personnel_choices()

        team_form = EntityTeamMemberForm()
        team_form.personnel_id.choices = get_personnel_choices(internal_only=True, placeholder='-- Select Internal Personnel --')

    return render_template(
        'projects/detail.html',
        project=project,
        vendor_relationships=vendor_relationships,
        constructor_relationships=constructor_relationships,
        operator_relationships=operator_relationships,
        owner_relationships=owner_relationships,
        personnel_relationships=personnel_relationships,
        team_assignments=team_assignments,
        vendor_form=vendor_form,
        constructor_form=constructor_form,
        operator_form=operator_form,
        owner_form=owner_form,
        offtaker_form=offtaker_form,
        personnel_form=personnel_form,
        team_form=team_form,
        toggle_form=TeamAssignmentToggleForm(),
        delete_form=ConfirmActionForm(),
        can_manage_relationships=can_manage,
        offtaker_relationships=offtaker_relationships
    )


@bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Edit core project details."""
    project = _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to edit project details.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ProjectForm(project_id=project.project_id, obj=project)

    if not form.is_submitted():
        form.target_cod.data = project.target_cod

    if form.validate_on_submit():
        try:
            project.project_name = form.project_name.data
            project.location = form.location.data or None
            project.project_status = form.project_status.data or None
            project.licensing_approach = form.licensing_approach.data or None
            project.configuration = form.configuration.data or None
            project.project_schedule = form.project_schedule.data or None
            project.target_cod = form.target_cod.data or None
            project.latitude = float(form.latitude.data) if form.latitude.data is not None else None
            project.longitude = float(form.longitude.data) if form.longitude.data is not None else None
            project.notes = form.notes.data or None

            project.modified_by = current_user.user_id
            project.modified_date = datetime.utcnow()

            db_session.commit()

            flash('Project details updated successfully.', 'success')
            return redirect(url_for('projects.view_project', project_id=project.project_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error updating project: {exc}', 'danger')

    return render_template(
        'projects/form.html',
        form=form,
        project=project,
        title=f'Edit Project: {project.project_name}'
    )


@bp.route('/<int:project_id>/relationships/vendors', methods=['POST'])
@login_required
def add_project_vendor_relationship(project_id):
    project = _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ProjectVendorRelationshipForm()
    form.vendor_id.choices = get_vendor_choices()

    if form.validate_on_submit():
        vendor_id = form.vendor_id.data
        if vendor_id == 0:
            flash('Please select a vendor.', 'warning')
            return redirect(url_for('projects.view_project', project_id=project_id))

        existing = db_session.query(ProjectVendorRelationship).filter_by(
            project_id=project.project_id,
            vendor_id=vendor_id
        ).first()

        if existing:
            flash('Vendor relationship already exists.', 'info')
            return redirect(url_for('projects.view_project', project_id=project_id))

        relationship = ProjectVendorRelationship(
            project_id=project.project_id,
            vendor_id=vendor_id,
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

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/vendors/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_project_vendor_relationship(project_id, relationship_id):
    _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(ProjectVendorRelationship, relationship_id)
        if not relationship or relationship.project_id != project_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Vendor relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing vendor relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/constructors', methods=['POST'])
@login_required
def add_project_constructor_relationship(project_id):
    project = _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ProjectConstructorRelationshipForm()
    form.constructor_id.choices = get_constructor_choices()

    if form.validate_on_submit():
        constructor_id = form.constructor_id.data
        if constructor_id == 0:
            flash('Please select a constructor.', 'warning')
            return redirect(url_for('projects.view_project', project_id=project_id))

        existing = db_session.query(ProjectConstructorRelationship).filter_by(
            project_id=project.project_id,
            constructor_id=constructor_id
        ).first()

        if existing:
            flash('Constructor relationship already exists.', 'info')
            return redirect(url_for('projects.view_project', project_id=project_id))

        relationship = ProjectConstructorRelationship(
            project_id=project.project_id,
            constructor_id=constructor_id,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Constructor relationship added.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error adding constructor relationship: {exc}', 'danger')
    else:
        flash('Unable to add constructor relationship. Please check the form inputs.', 'danger')

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/constructors/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_project_constructor_relationship(project_id, relationship_id):
    _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(ProjectConstructorRelationship, relationship_id)
        if not relationship or relationship.project_id != project_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Constructor relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing constructor relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/operators', methods=['POST'])
@login_required
def add_project_operator_relationship(project_id):
    project = _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ProjectOperatorRelationshipForm()
    form.operator_id.choices = get_operator_choices()

    if form.validate_on_submit():
        operator_id = form.operator_id.data
        if operator_id == 0:
            flash('Please select an operator.', 'warning')
            return redirect(url_for('projects.view_project', project_id=project_id))

        existing = db_session.query(ProjectOperatorRelationship).filter_by(
            project_id=project.project_id,
            operator_id=operator_id
        ).first()

        if existing:
            flash('Operator relationship already exists.', 'info')
            return redirect(url_for('projects.view_project', project_id=project_id))

        relationship = ProjectOperatorRelationship(
            project_id=project.project_id,
            operator_id=operator_id,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Operator relationship added.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error adding operator relationship: {exc}', 'danger')
    else:
        flash('Unable to add operator relationship. Please check the form inputs.', 'danger')

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/operators/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_project_operator_relationship(project_id, relationship_id):
    _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(ProjectOperatorRelationship, relationship_id)
        if not relationship or relationship.project_id != project_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Operator relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing operator relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/offtakers', methods=['POST'])
@login_required
def add_project_offtaker_relationship(project_id):
    project = _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ProjectOfftakerRelationshipForm()
    form.offtaker_id.choices = get_offtaker_choices()

    if form.validate_on_submit():
        offtaker_id = form.offtaker_id.data
        if offtaker_id == 0:
            flash('Please select an off-taker.', 'warning')
            return redirect(url_for('projects.view_project', project_id=project_id))

        existing = db_session.query(ProjectOfftakerRelationship).filter_by(
            project_id=project.project_id,
            offtaker_id=offtaker_id
        ).first()

        if existing:
            flash('Off-taker relationship already exists.', 'info')
            return redirect(url_for('projects.view_project', project_id=project_id))

        relationship = ProjectOfftakerRelationship(
            project_id=project.project_id,
            offtaker_id=offtaker_id,
            agreement_type=form.agreement_type.data or None,
            contracted_volume=form.contracted_volume.data or None,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Off-taker relationship added.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error adding off-taker relationship: {exc}', 'danger')

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/offtakers/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_project_offtaker_relationship(project_id, relationship_id):
    project = _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    relationship = db_session.get(ProjectOfftakerRelationship, relationship_id)

    if not relationship or relationship.project_id != project.project_id:
        flash('Off-taker relationship not found.', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ConfirmActionForm()
    if form.validate_on_submit():
        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Off-taker relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing off-taker relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('projects.view_project', project_id=project_id))



@bp.route('/<int:project_id>/relationships/owners', methods=['POST'])
@login_required
def add_project_owner_relationship(project_id):
    project = _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ProjectOwnerLinkForm()
    form.owner_id.choices = get_owner_choices()

    if form.validate_on_submit():
        owner_id = form.owner_id.data
        if owner_id == 0:
            flash('Please select an owner.', 'warning')
            return redirect(url_for('projects.view_project', project_id=project_id))

        existing = db_session.query(ProjectOwnerRelationship).filter_by(
            project_id=project.project_id,
            owner_id=owner_id
        ).first()

        if existing:
            flash('Owner relationship already exists.', 'info')
            return redirect(url_for('projects.view_project', project_id=project_id))

        relationship = ProjectOwnerRelationship(
            project_id=project.project_id,
            owner_id=owner_id,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Owner relationship added.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error adding owner relationship: {exc}', 'danger')
    else:
        flash('Unable to add owner relationship. Please check the form inputs.', 'danger')

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/owners/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_project_owner_relationship(project_id, relationship_id):
    _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(ProjectOwnerRelationship, relationship_id)
        if not relationship or relationship.project_id != project_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Owner relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing owner relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/personnel', methods=['POST'])
@login_required
def add_project_personnel_relationship(project_id):
    project = _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = PersonnelEntityRelationshipForm()
    form.personnel_id.choices = get_personnel_choices()

    if form.validate_on_submit():
        personnel_id = form.personnel_id.data
        if personnel_id == 0:
            flash('Please select personnel.', 'warning')
            return redirect(url_for('projects.view_project', project_id=project_id))

        existing = db_session.query(PersonnelEntityRelationship).filter_by(
            personnel_id=personnel_id,
            entity_type='Project',
            entity_id=project.project_id
        ).first()

        if existing:
            flash('Personnel relationship already exists.', 'info')
            return redirect(url_for('projects.view_project', project_id=project_id))

        relationship = PersonnelEntityRelationship(
            personnel_id=personnel_id,
            entity_type='Project',
            entity_id=project.project_id,
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

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/personnel/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_project_personnel_relationship(project_id, relationship_id):
    _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(PersonnelEntityRelationship, relationship_id)
        if not relationship or relationship.entity_type != 'Project' or relationship.entity_id != project_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Personnel relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing personnel relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/team', methods=['POST'])
@login_required
def add_project_team_assignment(project_id):
    project = _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify team assignments.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = EntityTeamMemberForm()
    form.personnel_id.choices = get_personnel_choices(internal_only=True, placeholder='-- Select Internal Personnel --')

    if form.validate_on_submit():
        personnel_id = form.personnel_id.data
        if personnel_id == 0:
            flash('Please select team personnel.', 'warning')
            return redirect(url_for('projects.view_project', project_id=project_id))

        assignment = db_session.query(EntityTeamMember).filter_by(
            entity_type='Project',
            entity_id=project.project_id,
            personnel_id=personnel_id
        ).first()

        if assignment:
            assignment.assignment_type = form.assignment_type.data or None
            assignment.assigned_date = form.assigned_date.data
            assignment.is_active = form.is_active.data
        else:
            assignment = EntityTeamMember(
                entity_type='Project',
                entity_id=project.project_id,
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

    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/team/<int:assignment_id>/toggle', methods=['POST'])
@login_required
def toggle_project_team_assignment(project_id, assignment_id):
    _get_project_or_404(project_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify team assignments.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = TeamAssignmentToggleForm()

    if form.validate_on_submit() and form.assignment_id.data == str(assignment_id):
        assignment = db_session.get(EntityTeamMember, assignment_id)
        if not assignment or assignment.entity_type != 'Project' or assignment.entity_id != project_id:
            flash('Team assignment not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))

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

    return redirect(url_for('projects.view_project', project_id=project_id))
