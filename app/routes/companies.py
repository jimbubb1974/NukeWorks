"""Unified company views."""
from collections import defaultdict

from flask import Blueprint, render_template, request, url_for, redirect, flash, abort
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from werkzeug.routing import BuildError
from datetime import datetime

from app import db_session
from app.models import (
    Company, CompanyRole, CompanyRoleAssignment, Project,
    ExternalPersonnel, InternalPersonnel, PersonnelRelationship,
)
from app.forms.companies import CompanyForm
from app.forms.relationships import ConfirmActionForm, ProjectCompanyRelationshipForm
from app.utils.permissions import edit_required, filter_relationships

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


@bp.route('/create', methods=['GET', 'POST'])
@login_required
@edit_required
def create_company():
    """Create a new company"""
    if not _can_manage_companies(current_user):
        flash('You do not have permission to create companies.', 'danger')
        return redirect(url_for('companies.list_companies'))

    form = CompanyForm()
    
    if form.validate_on_submit():
        try:
            company = Company(
                company_name=form.company_name.data,
                company_type=form.company_type.data or None,
                website=form.website.data or None,
                headquarters_country=form.headquarters_country.data or None,
                is_mpr_client=bool(form.is_mpr_client.data),
                is_internal=bool(form.is_internal.data),
                notes=form.notes.data or None,
                created_by=current_user.user_id,
                modified_by=current_user.user_id,
                created_date=datetime.utcnow(),
                modified_date=datetime.utcnow()
            )

            db_session.add(company)
            db_session.flush()  # Get the company_id

            # Create ClientProfile if MPR client
            if company.is_mpr_client:
                from app.models import ClientProfile
                client_profile = ClientProfile(
                    company_id=company.company_id,
                    client_priority=form.client_priority.data or None,
                    client_tier=form.client_tier.data or None,
                    relationship_notes=form.relationship_notes.data or None,
                    created_by=current_user.user_id,
                    modified_by=current_user.user_id,
                    created_date=datetime.utcnow(),
                    modified_date=datetime.utcnow()
                )
                db_session.add(client_profile)

            db_session.commit()
            flash('Company created successfully.', 'success')
            return redirect(url_for('companies.view_company', company_id=company.company_id))
        except Exception as exc:
            db_session.rollback()
            flash(f'Error creating company: {exc}', 'danger')

    return render_template(
        'companies/form.html',
        form=form,
        company=None,
        title='Create New Company'
    )


@bp.route('/')
@login_required
def list_companies():
    from sqlalchemy import func

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

    # Get company counts by role for statistics
    role_counts = {}
    for role in roles:
        count = (
            db_session.query(func.count(func.distinct(CompanyRoleAssignment.company_id)))
            .filter(CompanyRoleAssignment.role_id == role.role_id)
            .scalar() or 0
        )
        role_counts[role.role_code] = count

    total_companies = db_session.query(Company).count()

    return render_template(
        'companies/list.html',
        companies=companies,
        assignments_map=assignments_map,
        roles=roles,
        active_role=role_filter,
        role_counts=role_counts,
        total_companies=total_companies,
    )


def _get_company_or_404(company_id: int) -> Company:
    """Return company or abort with 404"""
    company = db_session.get(Company, company_id)
    if not company:
        flash('Company not found', 'error')
        abort(404)
    return company


def _can_manage_companies(user) -> bool:
    """Check if user can manage companies"""
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)) and user.can_edit())


def _normalize_project_role_code(role_code: str | None) -> str | None:
    """Normalize aliases used by project-company relationship forms."""
    if role_code in ('owner', 'developer'):
        return 'developer'
    return role_code


def _get_or_create_company_role(role_code: str) -> CompanyRole:
    """Fetch a company role by code, creating it when missing."""
    role = db_session.query(CompanyRole).filter_by(role_code=role_code).first()
    if role:
        return role

    role = CompanyRole(
        role_code=role_code,
        role_label=role_code.title(),
        description=f"Role for {role_code} relationships"
    )
    db_session.add(role)
    db_session.flush()
    return role


@bp.route('/<int:company_id>')
@login_required
def view_company(company_id):
    """View company details"""
    company = _get_company_or_404(company_id)
    
    # Get role assignments for this company, filtered by confidentiality access
    all_role_assignments = db_session.query(CompanyRoleAssignment).filter_by(
        company_id=company_id
    ).options(joinedload(CompanyRoleAssignment.role)).all()
    role_assignments = filter_relationships(current_user, all_role_assignments)
    hidden_relationships_count = len(all_role_assignments) - len(role_assignments)

    can_view_confidential = bool(getattr(current_user, 'is_admin', False) or
                                 getattr(current_user, 'has_confidential_access', False))

    project_ids = [
        assignment.context_id
        for assignment in role_assignments
        if assignment.context_type == 'Project' and assignment.context_id
    ]
    projects_by_id = {
        project.project_id: project
        for project in db_session.query(Project).filter(Project.project_id.in_(project_ids)).all()
    } if project_ids else {}
    
    # Get external personnel linked to this company
    from app.models import ExternalPersonnel, PersonnelRelationship, InternalPersonnel
    personnel = db_session.query(ExternalPersonnel).filter_by(
        company_id=company_id
    ).order_by(ExternalPersonnel.full_name).all()
    
    # Get MPR connections for each external personnel
    personnel_with_connections = []
    for person in personnel:
        # Get internal personnel relationships for this external person
        relationships = db_session.query(PersonnelRelationship).filter_by(
            external_personnel_id=person.personnel_id
        ).options(joinedload(PersonnelRelationship.internal_personnel)).all()
        
        # Create connections with relationship info
        mpr_connections = []
        for rel in relationships:
            mpr_connections.append({
                'personnel': rel.internal_personnel,
                'relationship_type': rel.relationship_type,
                'is_primary': rel.relationship_type == 'Primary Contact' if rel.relationship_type else False
            })
        
        personnel_with_connections.append({
            'person': person,
            'mpr_connections': mpr_connections
        })
    
    # Get all external personnel for the dropdown (excluding those already linked)
    all_personnel = db_session.query(ExternalPersonnel).filter(
        ExternalPersonnel.company_id != company_id
    ).order_by(ExternalPersonnel.full_name).all()
    
    can_manage = _can_manage_companies(current_user)
    delete_form = ConfirmActionForm()
    
    return render_template(
        'companies/detail.html',
        company=company,
        role_assignments=role_assignments,
        hidden_relationships_count=hidden_relationships_count,
        can_view_confidential=can_view_confidential,
        projects_by_id=projects_by_id,
        personnel=personnel,
        personnel_with_connections=personnel_with_connections,
        all_personnel=all_personnel,
        can_manage=can_manage,
        delete_form=delete_form
    )


@bp.route('/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
@edit_required
def edit_company(company_id):
    """Edit company details"""
    company = _get_company_or_404(company_id)
    
    if not _can_manage_companies(current_user):
        flash('You do not have permission to edit companies.', 'danger')
        return redirect(url_for('companies.view_company', company_id=company_id))

    # Populate form with existing data including ClientProfile
    form = CompanyForm(obj=company)
    
    # Populate MPR client fields from ClientProfile if it exists
    if company.client_profile:
        form.client_priority.data = company.client_profile.client_priority
        form.client_tier.data = company.client_profile.client_tier
        form.relationship_notes.data = company.client_profile.relationship_notes
    
    if form.validate_on_submit():
        try:
            # Update basic company fields
            company.company_name = form.company_name.data
            company.company_type = form.company_type.data or None
            company.website = form.website.data or None
            company.headquarters_country = form.headquarters_country.data or None
            company.is_mpr_client = bool(form.is_mpr_client.data)
            company.is_internal = bool(form.is_internal.data)
            company.notes = form.notes.data or None
            company.modified_by = current_user.user_id
            company.modified_date = datetime.utcnow()

            # Handle MPR client CRM data
            if company.is_mpr_client:
                # Create or update ClientProfile
                from app.models import ClientProfile
                client_profile = company.client_profile
                if not client_profile:
                    client_profile = ClientProfile(company_id=company.company_id)
                    db_session.add(client_profile)
                
                # Update CRM fields
                client_profile.client_priority = form.client_priority.data or None
                client_profile.client_tier = form.client_tier.data or None
                client_profile.relationship_notes = form.relationship_notes.data or None
                client_profile.modified_by = current_user.user_id
                client_profile.modified_date = datetime.utcnow()
            else:
                # Remove ClientProfile if MPR client flag is turned off
                if company.client_profile:
                    db_session.delete(company.client_profile)

            db_session.commit()
            
            # DEBUG: Log successful commit with timestamp
            import time
            print(f"\n{'='*60}")
            print(f"[DB COMMIT] Company #{company_id} updated")
            print(f"[DB COMMIT] User: {current_user.username}")
            print(f"[DB COMMIT] Company: {company.company_name}")
            print(f"[DB COMMIT] Timestamp: {time.time()}")
            print(f"[DB COMMIT] Modified Date: {company.modified_date}")
            
            # Force a fresh query to verify the change is visible
            from app import db_session as verify_session
            verify_company = verify_session.query(Company).filter_by(company_id=company_id).first()
            if verify_company:
                print(f"[DB VERIFY] Re-queried company modified_date: {verify_company.modified_date}")
                if verify_company.client_profile:
                    print(f"[DB VERIFY] Client priority: {verify_company.client_profile.client_priority}")
            print(f"{'='*60}\n")
            
            flash('Company updated successfully.', 'success')
            return redirect(url_for('companies.view_company', company_id=company.company_id))
        except Exception as exc:
            db_session.rollback()
            flash(f'Error updating company: {exc}', 'danger')

    external_personnel = (
        db_session.query(ExternalPersonnel)
        .filter_by(company_id=company_id)
        .options(joinedload(ExternalPersonnel.internal_relationships)
                 .joinedload(PersonnelRelationship.internal_personnel))
        .order_by(ExternalPersonnel.full_name)
        .all()
    )
    internal_personnel = (
        db_session.query(InternalPersonnel)
        .filter_by(is_active=True)
        .order_by(InternalPersonnel.full_name)
        .all()
    )
    project_relationships = (
        db_session.query(CompanyRoleAssignment)
        .filter_by(company_id=company_id, context_type='Project')
        .options(
            joinedload(CompanyRoleAssignment.role),
            joinedload(CompanyRoleAssignment.company)
        )
        .order_by(CompanyRoleAssignment.context_id, CompanyRoleAssignment.assignment_id)
        .all()
    )
    projects_by_id = {
        project.project_id: project
        for project in db_session.query(Project).order_by(Project.project_name).all()
    }
    project_company_form = ProjectCompanyRelationshipForm()
    project_company_form.company_id.choices = [(company.company_id, company.company_name)]

    return render_template(
        'companies/form.html',
        form=form,
        company=company,
        title=f'Edit Company: {company.company_name}',
        external_personnel=external_personnel,
        internal_personnel=internal_personnel,
        project_relationships=project_relationships,
        projects_by_id=projects_by_id,
        project_company_form=project_company_form,
    )


@bp.route('/<int:company_id>/relationships/projects/<int:assignment_id>/edit', methods=['POST'])
@login_required
@edit_required
def update_project_relationship(company_id, assignment_id):
    """Update a project-company relationship from the company edit page."""
    _get_company_or_404(company_id)
    next_url = request.form.get('next') or url_for('companies.edit_company', company_id=company_id)

    if not _can_manage_companies(current_user):
        flash('You do not have permission to manage company relationships.', 'danger')
        return redirect(next_url)

    relationship = (
        db_session.query(CompanyRoleAssignment)
        .filter_by(
            assignment_id=assignment_id,
            company_id=company_id,
            context_type='Project',
        )
        .options(joinedload(CompanyRoleAssignment.company))
        .first()
    )
    if not relationship:
        flash('Project relationship not found.', 'error')
        return redirect(next_url)

    form = ProjectCompanyRelationshipForm()
    form.company_id.choices = [(company_id, relationship.company.company_name if relationship.company else 'Company')]

    if not form.validate_on_submit():
        flash('Please correct the relationship form errors.', 'warning')
        return redirect(next_url)

    try:
        normalized_role_code = _normalize_project_role_code(form.role_type.data)
        duplicate_relationship = (
            db_session.query(CompanyRoleAssignment)
            .join(CompanyRole)
            .filter(
                CompanyRoleAssignment.assignment_id != relationship.assignment_id,
                CompanyRoleAssignment.company_id == company_id,
                CompanyRoleAssignment.context_type == 'Project',
                CompanyRoleAssignment.context_id == relationship.context_id,
                CompanyRole.role_code == normalized_role_code,
            )
            .first()
        )
        if duplicate_relationship:
            flash(f'This company already has a {normalized_role_code} role for that project.', 'warning')
            return redirect(next_url)

        role = _get_or_create_company_role(normalized_role_code)
        relationship.role_id = role.role_id
        relationship.notes = form.notes.data or None
        relationship.is_confidential = bool(form.is_confidential.data)
        relationship.modified_by = current_user.user_id
        relationship.modified_date = datetime.utcnow()

        db_session.commit()
        flash('Project relationship updated successfully.', 'success')
    except Exception as exc:
        db_session.rollback()
        flash(f'Error updating project relationship: {exc}', 'danger')

    return redirect(next_url)


@bp.route('/<int:company_id>/relationships/projects/add', methods=['POST'])
@login_required
@edit_required
def add_project_relationship(company_id):
    """Add a new project-company relationship from the company edit page."""
    company = _get_company_or_404(company_id)
    next_url = request.form.get('next') or url_for('companies.edit_company', company_id=company_id)

    if not _can_manage_companies(current_user):
        flash('You do not have permission to manage company relationships.', 'danger')
        return redirect(next_url)

    project_id = request.form.get('project_id', type=int)
    role_code_raw = request.form.get('role_type', '').strip()
    notes = request.form.get('notes', '').strip() or None
    is_confidential = bool(request.form.get('is_confidential'))

    if not project_id or not role_code_raw:
        flash('Project and role are required.', 'warning')
        return redirect(next_url)

    project = db_session.query(Project).filter_by(project_id=project_id).first()
    if not project:
        flash('Project not found.', 'danger')
        return redirect(next_url)

    try:
        normalized_role_code = _normalize_project_role_code(role_code_raw)
        duplicate = (
            db_session.query(CompanyRoleAssignment)
            .join(CompanyRole)
            .filter(
                CompanyRoleAssignment.company_id == company_id,
                CompanyRoleAssignment.context_type == 'Project',
                CompanyRoleAssignment.context_id == project_id,
                CompanyRole.role_code == normalized_role_code,
            )
            .first()
        )
        if duplicate:
            flash(f'{company.company_name} already has a {normalized_role_code} role on that project.', 'warning')
            return redirect(next_url)

        role = _get_or_create_company_role(normalized_role_code)
        assignment = CompanyRoleAssignment(
            company_id=company_id,
            role_id=role.role_id,
            context_type='Project',
            context_id=project_id,
            notes=notes,
            is_confidential=is_confidential,
        )
        db_session.add(assignment)
        db_session.commit()
        flash(f'Added {role.role_label} relationship with {project.project_name}.', 'success')
    except Exception as exc:
        db_session.rollback()
        flash(f'Error adding project relationship: {exc}', 'danger')

    return redirect(next_url)


@bp.route('/<int:company_id>/employees/add', methods=['POST'])
@login_required
@edit_required
def add_employee(company_id):
    """Add an external personnel record linked to this company."""
    _get_company_or_404(company_id)
    next_url = request.form.get('next') or url_for('companies.edit_company', company_id=company_id)
    full_name = request.form.get('full_name', '').strip()
    if not full_name:
        flash('External contact name is required.', 'danger')
        return redirect(next_url)
    try:
        person = ExternalPersonnel(
            full_name=full_name,
            email=request.form.get('email', '').strip() or None,
            phone=request.form.get('phone', '').strip() or None,
            role=request.form.get('role', '').strip() or None,
            contact_type=request.form.get('contact_type', '').strip() or None,
            company_id=company_id,
            is_active=True,
            notes=request.form.get('notes', '').strip() or None,
            created_by=current_user.user_id,
            modified_by=current_user.user_id,
        )
        db_session.add(person)
        db_session.commit()
        flash(f'{full_name} added as an external contact.', 'success')
    except Exception as exc:
        db_session.rollback()
        flash(f'Error adding external contact: {exc}', 'danger')
    return redirect(next_url)


@bp.route('/<int:company_id>/employees/<int:personnel_id>/delete', methods=['POST'])
@login_required
@edit_required
def delete_employee(company_id, personnel_id):
    """Delete an external personnel record belonging to this company."""
    person = db_session.get(ExternalPersonnel, personnel_id)
    if not person or person.company_id != company_id:
        flash('Employee not found.', 'danger')
        return redirect(url_for('companies.edit_company', company_id=company_id))
    try:
        db_session.delete(person)
        db_session.commit()
        flash(f'{person.full_name} removed.', 'success')
    except Exception as exc:
        db_session.rollback()
        flash(f'Error removing employee: {exc}', 'danger')
    return redirect(url_for('companies.edit_company', company_id=company_id))


@bp.route('/<int:company_id>/employees/<int:personnel_id>/relationships/add', methods=['POST'])
@login_required
@edit_required
def add_employee_relationship(company_id, personnel_id):
    """Link an external personnel record to an internal MPR person."""
    person = db_session.get(ExternalPersonnel, personnel_id)
    if not person or person.company_id != company_id:
        flash('Employee not found.', 'danger')
        return redirect(url_for('companies.edit_company', company_id=company_id))
    try:
        internal_id = int(request.form.get('internal_personnel_id', 0))
    except (TypeError, ValueError):
        flash('Invalid MPR person selected.', 'danger')
        return redirect(url_for('companies.edit_company', company_id=company_id))
    if not internal_id:
        flash('Please select an MPR person to link.', 'warning')
        return redirect(url_for('companies.edit_company', company_id=company_id))
    existing = db_session.query(PersonnelRelationship).filter_by(
        internal_personnel_id=internal_id,
        external_personnel_id=personnel_id,
    ).first()
    if existing:
        flash('That relationship already exists.', 'warning')
        return redirect(url_for('companies.edit_company', company_id=company_id))
    try:
        rel = PersonnelRelationship(
            internal_personnel_id=internal_id,
            external_personnel_id=personnel_id,
            relationship_type=request.form.get('relationship_type', '').strip() or None,
        )
        db_session.add(rel)
        db_session.commit()
        flash('MPR link added.', 'success')
    except Exception as exc:
        db_session.rollback()
        flash(f'Error adding MPR link: {exc}', 'danger')
    return redirect(url_for('companies.edit_company', company_id=company_id))


@bp.route('/<int:company_id>/employees/<int:personnel_id>/relationships/<int:relationship_id>/delete', methods=['POST'])
@login_required
@edit_required
def delete_employee_relationship(company_id, personnel_id, relationship_id):
    """Remove an MPR link from an external personnel record."""
    rel = db_session.get(PersonnelRelationship, relationship_id)
    if not rel or rel.external_personnel_id != personnel_id:
        flash('Relationship not found.', 'danger')
        return redirect(url_for('companies.edit_company', company_id=company_id))
    try:
        db_session.delete(rel)
        db_session.commit()
        flash('MPR link removed.', 'success')
    except Exception as exc:
        db_session.rollback()
        flash(f'Error removing MPR link: {exc}', 'danger')
    return redirect(url_for('companies.edit_company', company_id=company_id))


@bp.route('/<int:company_id>/delete', methods=['POST'])
@login_required
@edit_required
def delete_company(company_id):
    """Delete a company"""
    company = _get_company_or_404(company_id)
    
    if not _can_manage_companies(current_user):
        flash('You do not have permission to delete companies.', 'danger')
        return redirect(url_for('companies.view_company', company_id=company_id))

    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Action not confirmed.', 'warning')
        return redirect(url_for('companies.view_company', company_id=company_id))

    try:
        db_session.delete(company)
        db_session.commit()
        flash('Company deleted successfully.', 'success')
        return redirect(url_for('companies.list_companies'))
    except Exception as exc:
        db_session.rollback()
        flash(f'Error deleting company: {exc}', 'danger')
        return redirect(url_for('companies.view_company', company_id=company_id))


@bp.route('/<int:company_id>/personnel', methods=['POST'])
@login_required
@edit_required
def link_personnel_to_company(company_id):
    """Link personnel to a company"""
    company = _get_company_or_404(company_id)
    
    if not _can_manage_companies(current_user):
        flash('You do not have permission to manage company personnel.', 'danger')
        return redirect(url_for('companies.view_company', company_id=company_id))
    
    personnel_id = request.form.get('personnel_id')
    if not personnel_id:
        flash('Please select a person to link.', 'warning')
        return redirect(url_for('companies.view_company', company_id=company_id))
    
    try:
        from app.models import ExternalPersonnel
        personnel = db_session.query(ExternalPersonnel).filter_by(personnel_id=personnel_id).first()
        if not personnel:
            flash('Person not found.', 'error')
            return redirect(url_for('companies.view_company', company_id=company_id))
        
        # Check if already linked
        if personnel.company_id == company_id:
            flash(f'{personnel.full_name} is already linked to this company.', 'warning')
            return redirect(url_for('companies.view_company', company_id=company_id))
        
        # Link the personnel to the company
        personnel.company_id = company_id
        db_session.commit()
        flash(f'{personnel.full_name} linked to {company.company_name} successfully.', 'success')
        
    except Exception as exc:
        db_session.rollback()
        flash(f'Error linking personnel: {exc}', 'danger')
    
    return redirect(url_for('companies.view_company', company_id=company_id))


@bp.route('/<int:company_id>/personnel/<int:personnel_id>/unlink', methods=['POST'])
@login_required
@edit_required
def unlink_personnel_from_company(company_id, personnel_id):
    """Unlink personnel from a company"""
    company = _get_company_or_404(company_id)
    
    if not _can_manage_companies(current_user):
        flash('You do not have permission to manage company personnel.', 'danger')
        return redirect(url_for('companies.view_company', company_id=company_id))
    
    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Action not confirmed.', 'warning')
        return redirect(url_for('companies.view_company', company_id=company_id))
    
    try:
        from app.models import ExternalPersonnel
        personnel = db_session.query(ExternalPersonnel).filter_by(
            personnel_id=personnel_id,
            company_id=company_id
        ).first()
        
        if not personnel:
            flash('Person not found or not linked to this company.', 'error')
            return redirect(url_for('companies.view_company', company_id=company_id))
        
        name = personnel.full_name
        db_session.delete(personnel)
        db_session.commit()
        flash(f'{name} removed from {company.company_name}.', 'success')
        
    except Exception as exc:
        db_session.rollback()
        flash(f'Error unlinking personnel: {exc}', 'danger')
    
    return redirect(url_for('companies.view_company', company_id=company_id))


@bp.route('/<int:company_id>/toggle-mpr', methods=['POST'])
@login_required
@edit_required
def toggle_mpr_client(company_id):
    """Toggle MPR client status for a company"""
    company = _get_company_or_404(company_id)
    
    if not _can_manage_companies(current_user):
        return {'success': False, 'message': 'You do not have permission to modify companies.'}, 403
    
    try:
        # Toggle the MPR client status
        company.is_mpr_client = not company.is_mpr_client
        company.modified_by = current_user.user_id
        company.modified_date = datetime.utcnow()
        
        db_session.commit()
        
        status_text = 'Yes' if company.is_mpr_client else 'No'
        badge_class = 'bg-success' if company.is_mpr_client else 'bg-secondary'
        
        return {
            'success': True,
            'is_mpr_client': company.is_mpr_client,
            'status_text': status_text,
            'badge_class': badge_class,
            'message': f'{company.company_name} is now {"an" if company.is_mpr_client else "not an"} MPR client.'
        }
        
    except Exception as exc:
        db_session.rollback()
        return {'success': False, 'message': f'Error updating MPR client status: {exc}'}, 500
