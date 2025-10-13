"""Project routes (CRUD operations and relationship management)"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy.orm import joinedload

from app.models import (
    Project,
    Company,
    CompanyRole,
    CompanyRoleAssignment,
)
from app.forms.relationships import (
    ProjectCompanyRelationshipForm,
    PersonnelEntityRelationshipForm,
    EntityTeamMemberForm,
    TeamAssignmentToggleForm,
    ConfirmActionForm
)
from app.forms.projects import ProjectForm
from app import db_session
from app.utils.permissions import filter_relationships
from app.services.company_sync import sync_personnel_affiliation
from app.routes.relationship_utils import get_personnel_choices

bp = Blueprint('projects', __name__, url_prefix='/projects')


def _get_project_or_404(project_id: int) -> Project:
    project = db_session.get(Project, project_id)
    if not project:
        flash('Project not found', 'error')
        abort(404)
    return project


def _can_manage_relationships(user) -> bool:
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


def _get_company_choices():
    """Get all companies for relationship forms"""
    companies = db_session.query(Company).order_by(Company.company_name).all()
    return [(company.company_id, company.company_name) for company in companies]


def _process_relationship_assignments(project: Project, form_data, user_id: int):
    """Process relationship assignments from the project form.

    Handles vendor, owner, operator, constructor, and offtaker relationships
    by creating CompanyRoleAssignment records.
    """
    # Mapping of form field names to role codes
    relationship_mapping = {
        'vendor': 'vendor',
        'owner': 'developer',
        'operator': 'operator',
        'constructor': 'constructor',
        'offtaker': 'offtaker'
    }

    # Get all role IDs upfront
    roles = db_session.query(CompanyRole).all()
    role_id_map = {role.role_code: role.role_id for role in roles}

    # Delete existing relationships for this project
    db_session.query(CompanyRoleAssignment).filter_by(
        context_type='Project',
        context_id=project.project_id
    ).delete()

    # Process each relationship type
    for rel_type, role_code in relationship_mapping.items():
        entity_ids = form_data.getlist(f'{rel_type}_entity_id[]')
        confidential_flags = form_data.getlist(f'{rel_type}_confidential[]')
        notes_list = form_data.getlist(f'{rel_type}_notes[]')

        role_id = role_id_map.get(role_code)
        if not role_id:
            continue

        # Process each relationship in the list
        for idx, entity_id in enumerate(entity_ids):
            if not entity_id or entity_id == '':
                continue

            try:
                company_id = int(entity_id)
            except (ValueError, TypeError):
                continue

            # Get confidential flag for this index
            is_confidential = idx < len(confidential_flags)

            # Get notes for this index
            notes = notes_list[idx] if idx < len(notes_list) else None

            # Create the assignment
            assignment = CompanyRoleAssignment(
                company_id=company_id,
                role_id=role_id,
                context_type='Project',
                context_id=project.project_id,
                is_confidential=is_confidential,
                notes=notes or None,
                created_by=user_id,
                modified_by=user_id
            )
            db_session.add(assignment)


@bp.route('/')
@login_required
def list_projects():
    """List all projects"""
    projects = db_session.query(Project).order_by(Project.project_name).all()
    delete_form = ConfirmActionForm()
    return render_template('projects/list.html', projects=projects, can_manage=_can_manage_relationships(current_user), delete_form=delete_form)


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
            db_session.flush()  # Flush to get project_id

            # Process relationship assignments
            _process_relationship_assignments(project, request.form, current_user.user_id)

            db_session.commit()
            flash('Project created successfully.', 'success')
            return redirect(url_for('projects.view_project', project_id=project.project_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error creating project: {exc}', 'danger')

    # Get all companies for relationship dropdowns
    companies = db_session.query(Company).order_by(Company.company_name).all()

    return render_template(
        'projects/form.html',
        form=form,
        project=None,
        title='Create Project',
        companies=companies,
        vendor_assignments=[],
        owner_assignments=[],
        operator_assignments=[],
        constructor_assignments=[],
        offtaker_assignments=[]
    )


@bp.route('/<int:project_id>')
@login_required
def view_project(project_id):
    """View project details"""
    project = _get_project_or_404(project_id)

    # Get company relationships for this project
    company_relationships = db_session.query(CompanyRoleAssignment).filter_by(
        context_type='Project',
        context_id=project.project_id
    ).options(joinedload(CompanyRoleAssignment.company), joinedload(CompanyRoleAssignment.role)).all()
    
    # Apply confidentiality filter so users without access do not see confidential relationships
    visible_company_relationships = filter_relationships(current_user, company_relationships)

    # Group relationships by role type (only visible ones)
    vendor_relationships = [r for r in visible_company_relationships if r.role and r.role.role_code == 'vendor']
    constructor_relationships = [r for r in visible_company_relationships if r.role and r.role.role_code == 'constructor']
    operator_relationships = [r for r in visible_company_relationships if r.role and r.role.role_code == 'operator']
    owner_relationships = [r for r in visible_company_relationships if r.role and r.role.role_code == 'developer']
    offtaker_relationships = [r for r in visible_company_relationships if r.role and r.role.role_code == 'offtaker']
    
    # TODO: Personnel relationships feature disabled - models PersonnelEntityRelationship and EntityTeamMember removed
    personnel_relationships = []
    team_assignments = []
    # personnel_relationships = filter_relationships(
    #     current_user,
    #     db_session.query(PersonnelEntityRelationship).filter_by(entity_type='Project', entity_id=project.project_id)
    # )
    # team_assignments = db_session.query(EntityTeamMember).filter_by(
    #     entity_type='Project',
    #     entity_id=project.project_id
    # ).order_by(EntityTeamMember.is_active.desc(), EntityTeamMember.assigned_date.desc().nullslast()).all()

    can_manage = _can_manage_relationships(current_user)

    company_form = personnel_form = team_form = None
    if can_manage:
        company_form = ProjectCompanyRelationshipForm()
        company_form.company_id.choices = _get_company_choices()

        # TODO: Personnel forms disabled - models removed
        # personnel_form = PersonnelEntityRelationshipForm()
        # personnel_form.personnel_id.choices = get_personnel_choices()
        # team_form = EntityTeamMemberForm()
        # team_form.personnel_id.choices = get_personnel_choices(internal_only=True, placeholder='-- Select Internal Personnel --')

    return render_template(
        'projects/detail.html',
        project=project,
        vendor_relationships=vendor_relationships,
        constructor_relationships=constructor_relationships,
        operator_relationships=operator_relationships,
        owner_relationships=owner_relationships,
        offtaker_relationships=offtaker_relationships,
        personnel_relationships=personnel_relationships,
        team_assignments=team_assignments,
        company_form=company_form,
        personnel_form=personnel_form,
        team_form=team_form,
        toggle_form=TeamAssignmentToggleForm(),
        delete_form=ConfirmActionForm(),
        can_manage_relationships=can_manage
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
            # Update basic project fields
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

            # Process relationship assignments
            _process_relationship_assignments(project, request.form, current_user.user_id)

            db_session.commit()

            flash('Project details updated successfully.', 'success')
            return redirect(url_for('projects.view_project', project_id=project.project_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error updating project: {exc}', 'danger')

    # Get all companies for relationship dropdowns
    companies = db_session.query(Company).order_by(Company.company_name).all()

    # Build relationship assignments from unified schema for form display
    assignments_all = (
        db_session.query(CompanyRoleAssignment)
        .join(CompanyRole)
        .filter(
            CompanyRoleAssignment.context_type == 'Project',
            CompanyRoleAssignment.context_id == project.project_id
        )
        .all()
    )

    def _by_role(code: str):
        return [
            {
                'company_id': a.company_id,
                'is_confidential': bool(getattr(a, 'is_confidential', False)),
                'notes': a.notes or ''
            }
            for a in assignments_all
            if a.role and a.role.role_code == code
        ]

    vendor_assignments = _by_role('vendor')
    owner_assignments = _by_role('developer')
    operator_assignments = _by_role('operator')
    constructor_assignments = _by_role('constructor')
    offtaker_assignments = _by_role('offtaker')

    return render_template(
        'projects/form.html',
        form=form,
        project=project,
        title=f'Edit Project: {project.project_name}',
        companies=companies,
        vendor_assignments=vendor_assignments,
        owner_assignments=owner_assignments,
        operator_assignments=operator_assignments,
        constructor_assignments=constructor_assignments,
        offtaker_assignments=offtaker_assignments
    )


@bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Delete a project"""
    project = _get_project_or_404(project_id)
    
    if not _can_manage_relationships(current_user):
        flash('You do not have permission to delete projects.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Action not confirmed.', 'warning')
        return redirect(url_for('projects.view_project', project_id=project_id))

    try:
        db_session.delete(project)
        db_session.commit()
        flash('Project deleted successfully.', 'success')
        return redirect(url_for('projects.list_projects'))
    except Exception as exc:
        db_session.rollback()
        flash(f'Error deleting project: {exc}', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))


# TODO: Personnel relationship routes disabled - models PersonnelEntityRelationship and EntityTeamMember removed
# @bp.route('/<int:project_id>/relationships/personnel', methods=['POST'])
# @login_required
# def add_project_personnel_relationship(project_id):
#     ... (commented out)

# @bp.route('/<int:project_id>/relationships/personnel/<int:relationship_id>/delete', methods=['POST'])
# @login_required
# def delete_project_personnel_relationship(project_id, relationship_id):
#     ... (commented out)

# @bp.route('/<int:project_id>/team', methods=['POST'])
# @login_required
# def add_project_team_assignment(project_id):
#     ... (commented out)

# @bp.route('/<int:project_id>/team/<int:assignment_id>/toggle', methods=['POST'])
# @login_required
# def toggle_project_team_assignment(project_id, assignment_id):
#     ... (commented out)


@bp.route('/<int:project_id>/relationships/companies', methods=['POST'])
@login_required
def add_project_company_relationship(project_id):
    """Add a company relationship to a project"""
    project = _get_project_or_404(project_id)
    
    if not _can_manage_relationships(current_user):
        flash('You do not have permission to manage project relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ProjectCompanyRelationshipForm()
    form.company_id.choices = _get_company_choices()
    
    if form.validate_on_submit():
        try:
            # Check if this company already has this role for this project
            existing_relationship = db_session.query(CompanyRoleAssignment).filter_by(
                company_id=form.company_id.data,
                context_type='Project',
                context_id=project.project_id
            ).join(CompanyRole).filter(CompanyRole.role_code == form.role_type.data).first()
            
            if existing_relationship:
                company_name = db_session.query(Company).filter_by(company_id=form.company_id.data).first().company_name
                flash(f'{company_name} already has a {form.role_type.data} role for this project.', 'warning')
                return redirect(url_for('projects.view_project', project_id=project_id))
            
            # Get or create the role
            role = db_session.query(CompanyRole).filter_by(role_code=form.role_type.data).first()
            if not role:
                role = CompanyRole(
                    role_code=form.role_type.data,
                    role_label=form.role_type.data.title(),
                    description=f"Role for {form.role_type.data} relationships"
                )
                db_session.add(role)
                db_session.flush()  # Get the role_id
            
            # Create the relationship
            relationship = CompanyRoleAssignment(
                company_id=form.company_id.data,
                role_id=role.role_id,
                context_type='Project',
                context_id=project.project_id,
                notes=form.notes.data or None,
                is_confidential=bool(form.is_confidential.data),
                created_by=current_user.user_id,
                modified_by=current_user.user_id
            )
            
            db_session.add(relationship)
            db_session.commit()
            
            flash(f'Company relationship added successfully.', 'success')
        except Exception as exc:
            db_session.rollback()
            flash(f'Error adding company relationship: {exc}', 'danger')
    else:
        flash('Please correct the form errors.', 'warning')
    
    return redirect(url_for('projects.view_project', project_id=project_id))


@bp.route('/<int:project_id>/relationships/companies/<int:assignment_id>/delete', methods=['POST'])
@login_required
def delete_project_company_relationship(project_id, assignment_id):
    """Delete a company relationship from a project"""
    project = _get_project_or_404(project_id)
    
    if not _can_manage_relationships(current_user):
        flash('You do not have permission to manage project relationships.', 'danger')
        return redirect(url_for('projects.view_project', project_id=project_id))

    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Action not confirmed.', 'warning')
        return redirect(url_for('projects.view_project', project_id=project_id))

    try:
        # Find the relationship
        relationship = db_session.query(CompanyRoleAssignment).filter_by(
            assignment_id=assignment_id,
            context_type='Project',
            context_id=project.project_id
        ).first()
        
        if not relationship:
            flash('Company relationship not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        db_session.delete(relationship)
        db_session.commit()
        flash('Company relationship removed successfully.', 'success')
    except Exception as exc:
        db_session.rollback()
        flash(f'Error removing company relationship: {exc}', 'danger')
    
    return redirect(url_for('projects.view_project', project_id=project_id))
