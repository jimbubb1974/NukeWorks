"""Unified company views."""
from collections import defaultdict

from flask import Blueprint, render_template, request, url_for, redirect, flash, abort
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from werkzeug.routing import BuildError
from datetime import datetime

from app import db_session
from app.models import Company, CompanyRole, CompanyRoleAssignment
from app.forms.companies import CompanyForm
from app.forms.relationships import ConfirmActionForm

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
                    client_status=form.client_status.data or None,
                    relationship_strength=form.relationship_strength.data or None,
                    relationship_notes=form.relationship_notes.data or None,
                    last_contact_date=form.last_contact_date.data,
                    last_contact_type=form.last_contact_type.data or None,
                    next_planned_contact_date=form.next_planned_contact_date.data,
                    next_planned_contact_type=form.next_planned_contact_type.data or None,
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
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


@bp.route('/<int:company_id>')
@login_required
def view_company(company_id):
    """View company details"""
    company = _get_company_or_404(company_id)
    
    # Get role assignments for this company
    role_assignments = db_session.query(CompanyRoleAssignment).filter_by(
        company_id=company_id
    ).options(joinedload(CompanyRoleAssignment.role)).all()
    
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
        personnel=personnel,
        personnel_with_connections=personnel_with_connections,
        all_personnel=all_personnel,
        can_manage=can_manage,
        delete_form=delete_form
    )


@bp.route('/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
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
        form.client_status.data = company.client_profile.client_status
        form.relationship_strength.data = company.client_profile.relationship_strength
        form.relationship_notes.data = company.client_profile.relationship_notes
        form.last_contact_date.data = company.client_profile.last_contact_date
        form.last_contact_type.data = company.client_profile.last_contact_type
        form.next_planned_contact_date.data = company.client_profile.next_planned_contact_date
        form.next_planned_contact_type.data = company.client_profile.next_planned_contact_type
    
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
                client_profile.client_status = form.client_status.data or None
                client_profile.relationship_strength = form.relationship_strength.data or None
                client_profile.relationship_notes = form.relationship_notes.data or None
                client_profile.last_contact_date = form.last_contact_date.data
                client_profile.last_contact_type = form.last_contact_type.data or None
                client_profile.next_planned_contact_date = form.next_planned_contact_date.data
                client_profile.next_planned_contact_type = form.next_planned_contact_type.data or None
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

    return render_template(
        'companies/form.html',
        form=form,
        company=company,
        title=f'Edit Company: {company.company_name}'
    )


@bp.route('/<int:company_id>/delete', methods=['POST'])
@login_required
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
        
        # Unlink the personnel from the company
        personnel.company_id = None
        db_session.commit()
        flash(f'{personnel.full_name} unlinked from {company.company_name} successfully.', 'success')
        
    except Exception as exc:
        db_session.rollback()
        flash(f'Error unlinking personnel: {exc}', 'danger')
    
    return redirect(url_for('companies.view_company', company_id=company_id))


@bp.route('/<int:company_id>/toggle-mpr', methods=['POST'])
@login_required
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
