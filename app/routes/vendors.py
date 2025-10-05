"""
Technology Vendor Routes - Complete CRUD Operations
Following docs/02_DATABASE_SCHEMA.md and docs/06_BUSINESS_RULES.md
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime

from app.models import (
    TechnologyVendor,
    Product,
    ProjectVendorRelationship,
    VendorSupplierRelationship,
    OwnerVendorRelationship,
    VendorPreferredConstructor,
    PersonnelEntityRelationship
)
from app.forms.vendors import VendorForm, DeleteVendorForm
from app.forms.relationships import (
    VendorSupplierRelationshipForm,
    VendorOwnerRelationshipForm,
    VendorProjectRelationshipForm,
    VendorPreferredConstructorForm,
    PersonnelEntityRelationshipForm,
    ConfirmActionForm
)
from app import db_session
from app.utils.permissions import admin_required, filter_relationships
from app.routes.relationship_utils import (
    get_vendor_choices,
    get_owner_choices,
    get_project_choices,
    get_constructor_choices,
    get_personnel_choices
)
from app.services.company_sync import sync_company_from_vendor
from app.services.company_query import get_company_for_vendor

bp = Blueprint('vendors', __name__, url_prefix='/vendors')


def _get_vendor_or_404(vendor_id: int) -> TechnologyVendor:
    """Return vendor or abort with 404"""
    vendor = db_session.get(TechnologyVendor, vendor_id)
    if not vendor:
        flash('Vendor not found', 'error')
        abort(404)
    return vendor


def _can_manage_relationships(user) -> bool:
    """Check if user can manage relationships"""
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


@bp.route('/')
@login_required
def list_vendors():
    """
    List all technology vendors

    Features:
    - Sorted alphabetically by vendor_name
    - Shows product count for each vendor
    - Search functionality
    """
    # Get search query
    search = request.args.get('search', '').strip()

    # Base query
    query = db_session.query(TechnologyVendor)

    # Apply search filter
    if search:
        query = query.filter(
            TechnologyVendor.vendor_name.ilike(f'%{search}%')
        )

    # Order by name
    vendors = query.order_by(TechnologyVendor.vendor_name).all()

    vendor_company_map = {
        vendor.vendor_id: get_company_for_vendor(vendor.vendor_id)
        for vendor in vendors
    }

    # Get product counts
    vendor_product_counts = {}
    for vendor in vendors:
        count = db_session.query(func.count(Product.product_id)).filter(
            Product.vendor_id == vendor.vendor_id
        ).scalar()
        vendor_product_counts[vendor.vendor_id] = count

    return render_template(
        'vendors/list.html',
        vendors=vendors,
        vendor_product_counts=vendor_product_counts,
        search=search,
        vendor_company_map=vendor_company_map,
    )


@bp.route('/<int:vendor_id>')
@login_required
def view_vendor(vendor_id):
    """
    View vendor details

    Features:
    - Full vendor information
    - List of products
    - List of relationships
    - Edit/delete buttons for authorized users
    """
    vendor = _get_vendor_or_404(vendor_id)
    company_record = get_company_for_vendor(vendor_id)

    # Get products for this vendor
    products = db_session.query(Product).filter(
        Product.vendor_id == vendor_id
    ).order_by(Product.product_name).all()

    # Relationships (respect confidentiality)
    supplier_relationships = filter_relationships(current_user, vendor.supplier_relationships)
    customer_relationships = filter_relationships(current_user, vendor.as_supplier_relationships)
    owner_relationships = filter_relationships(current_user, vendor.owner_relationships)
    project_relationships = filter_relationships(current_user, vendor.project_relationships)
    preferred_constructor_relationships = filter_relationships(current_user, vendor.preferred_constructor_relationships)
    personnel_relationships = filter_relationships(
        current_user,
        db_session.query(PersonnelEntityRelationship).filter_by(entity_type='Vendor', entity_id=vendor.vendor_id)
    )

    can_manage = _can_manage_relationships(current_user)

    supplier_form = owner_form = project_form = preferred_constructor_form = personnel_form = None

    if can_manage:
        supplier_form = VendorSupplierRelationshipForm()
        supplier_form.supplier_id.choices = get_vendor_choices(exclude_id=vendor.vendor_id)

        owner_form = VendorOwnerRelationshipForm()
        owner_form.owner_id.choices = get_owner_choices()

        project_form = VendorProjectRelationshipForm()
        project_form.project_id.choices = get_project_choices()

        preferred_constructor_form = VendorPreferredConstructorForm()
        preferred_constructor_form.constructor_id.choices = get_constructor_choices()

        personnel_form = PersonnelEntityRelationshipForm()
        personnel_form.personnel_id.choices = get_personnel_choices()

    return render_template(
        'vendors/detail.html',
        vendor=vendor,
        company_record=company_record,
        products=products,
        supplier_relationships=supplier_relationships,
        customer_relationships=customer_relationships,
        owner_relationships=owner_relationships,
        project_relationships=project_relationships,
        preferred_constructor_relationships=preferred_constructor_relationships,
        personnel_relationships=personnel_relationships,
        supplier_form=supplier_form,
        owner_form=owner_form,
        project_form=project_form,
        preferred_constructor_form=preferred_constructor_form,
        personnel_form=personnel_form,
        can_manage_relationships=can_manage,
        delete_form=ConfirmActionForm()
    )


@bp.route('/<int:vendor_id>/relationships/suppliers', methods=['POST'])
@login_required
def add_vendor_supplier_relationship(vendor_id):
    """Create a vendor-supplier relationship"""
    vendor = _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = VendorSupplierRelationshipForm()
    form.supplier_id.choices = get_vendor_choices(exclude_id=vendor.vendor_id)

    if form.validate_on_submit():
        supplier_id = form.supplier_id.data
        if supplier_id == 0:
            flash('Please select a supplier.', 'warning')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        if supplier_id == vendor.vendor_id:
            flash('A vendor cannot supply itself.', 'warning')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        existing = db_session.query(VendorSupplierRelationship).filter_by(
            vendor_id=vendor.vendor_id,
            supplier_id=supplier_id
        ).first()

        if existing:
            flash('Supplier relationship already exists.', 'info')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        relationship = VendorSupplierRelationship(
            vendor_id=vendor.vendor_id,
            supplier_id=supplier_id,
            component_type=form.component_type.data or None,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Supplier relationship added.', 'success')
        except Exception as exc:  # pragma: no cover - defensive
            db_session.rollback()
            flash(f'Error adding supplier relationship: {exc}', 'danger')

    else:
        flash('Unable to add supplier relationship. Please check the form inputs.', 'danger')

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/<int:vendor_id>/relationships/suppliers/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_vendor_supplier_relationship(vendor_id, relationship_id):
    """Remove a vendor-supplier relationship"""
    _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(VendorSupplierRelationship, relationship_id)
        if not relationship or relationship.vendor_id != vendor_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Supplier relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover - defensive
            db_session.rollback()
            flash(f'Error removing supplier relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/<int:vendor_id>/relationships/owners', methods=['POST'])
@login_required
def add_vendor_owner_relationship(vendor_id):
    """Associate vendor with an owner"""
    vendor = _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = VendorOwnerRelationshipForm()
    form.owner_id.choices = get_owner_choices()

    if form.validate_on_submit():
        owner_id = form.owner_id.data
        if owner_id == 0:
            flash('Please select an owner/developer.', 'warning')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        existing = db_session.query(OwnerVendorRelationship).filter_by(
            owner_id=owner_id,
            vendor_id=vendor.vendor_id
        ).first()

        if existing:
            flash('Owner relationship already exists.', 'info')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        relationship = OwnerVendorRelationship(
            owner_id=owner_id,
            vendor_id=vendor.vendor_id,
            relationship_type=form.relationship_type.data or None,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Owner relationship added.', 'success')
        except Exception as exc:  # pragma: no cover - defensive
            db_session.rollback()
            flash(f'Error adding owner relationship: {exc}', 'danger')

    else:
        flash('Unable to add owner relationship. Please check the form inputs.', 'danger')

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/<int:vendor_id>/relationships/owners/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_vendor_owner_relationship(vendor_id, relationship_id):
    """Remove owner-vendor relationship"""
    _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(OwnerVendorRelationship, relationship_id)
        if not relationship or relationship.vendor_id != vendor_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Owner relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing owner relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/<int:vendor_id>/relationships/projects', methods=['POST'])
@login_required
def add_vendor_project_relationship(vendor_id):
    """Associate vendor with a project"""
    vendor = _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = VendorProjectRelationshipForm()
    form.project_id.choices = get_project_choices()

    if form.validate_on_submit():
        project_id = form.project_id.data
        if project_id == 0:
            flash('Please select a project.', 'warning')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        existing = db_session.query(ProjectVendorRelationship).filter_by(
            project_id=project_id,
            vendor_id=vendor.vendor_id
        ).first()

        if existing:
            flash('Project relationship already exists.', 'info')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        relationship = ProjectVendorRelationship(
            project_id=project_id,
            vendor_id=vendor.vendor_id,
            notes=form.notes.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Project relationship added.', 'success')
        except Exception as exc:  # pragma: no cover - defensive
            db_session.rollback()
            flash(f'Error adding project relationship: {exc}', 'danger')

    else:
        flash('Unable to add project relationship. Please check the form inputs.', 'danger')

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/<int:vendor_id>/relationships/projects/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_vendor_project_relationship(vendor_id, relationship_id):
    """Remove vendor-project relationship"""
    _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(ProjectVendorRelationship, relationship_id)
        if not relationship or relationship.vendor_id != vendor_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Project relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing project relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/<int:vendor_id>/relationships/preferred-constructors', methods=['POST'])
@login_required
def add_vendor_preferred_constructor(vendor_id):
    """Add preferred constructor for vendor"""
    vendor = _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = VendorPreferredConstructorForm()
    form.constructor_id.choices = get_constructor_choices()

    if form.validate_on_submit():
        constructor_id = form.constructor_id.data
        if constructor_id == 0:
            flash('Please select a constructor.', 'warning')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        existing = db_session.query(VendorPreferredConstructor).filter_by(
            vendor_id=vendor.vendor_id,
            constructor_id=constructor_id
        ).first()

        if existing:
            flash('Preferred constructor already recorded.', 'info')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        relationship = VendorPreferredConstructor(
            vendor_id=vendor.vendor_id,
            constructor_id=constructor_id,
            preference_reason=form.preference_reason.data or None,
            is_confidential=form.is_confidential.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(relationship)
            db_session.commit()
            flash('Preferred constructor added.', 'success')
        except Exception as exc:  # pragma: no cover - defensive
            db_session.rollback()
            flash(f'Error adding preferred constructor: {exc}', 'danger')

    else:
        flash('Unable to add preferred constructor. Please check the form inputs.', 'danger')

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/<int:vendor_id>/relationships/preferred-constructors/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_vendor_preferred_constructor(vendor_id, relationship_id):
    """Remove preferred constructor relationship"""
    _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(VendorPreferredConstructor, relationship_id)
        if not relationship or relationship.vendor_id != vendor_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Preferred constructor removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing preferred constructor: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/<int:vendor_id>/relationships/personnel', methods=['POST'])
@login_required
def add_vendor_personnel_relationship(vendor_id):
    """Link personnel to vendor"""
    vendor = _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = PersonnelEntityRelationshipForm()
    form.personnel_id.choices = get_personnel_choices()

    if form.validate_on_submit():
        personnel_id = form.personnel_id.data
        if personnel_id == 0:
            flash('Please select personnel.', 'warning')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        existing = db_session.query(PersonnelEntityRelationship).filter_by(
            personnel_id=personnel_id,
            entity_type='Vendor',
            entity_id=vendor.vendor_id
        ).first()

        if existing:
            flash('Personnel relationship already exists.', 'info')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        relationship = PersonnelEntityRelationship(
            personnel_id=personnel_id,
            entity_type='Vendor',
            entity_id=vendor.vendor_id,
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

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/<int:vendor_id>/relationships/personnel/<int:relationship_id>/delete', methods=['POST'])
@login_required
def delete_vendor_personnel_relationship(vendor_id, relationship_id):
    """Remove personnel link from vendor"""
    _get_vendor_or_404(vendor_id)

    if not _can_manage_relationships(current_user):
        flash('You do not have permission to modify relationships.', 'danger')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    form = ConfirmActionForm()

    if form.validate_on_submit():
        relationship = db_session.get(PersonnelEntityRelationship, relationship_id)
        if not relationship or relationship.entity_type != 'Vendor' or relationship.entity_id != vendor_id:
            flash('Relationship not found.', 'error')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        try:
            db_session.delete(relationship)
            db_session.commit()
            flash('Personnel relationship removed.', 'success')
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error removing personnel relationship: {exc}', 'danger')
    else:
        flash('Action not confirmed.', 'warning')

    return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_vendor():
    """
    Create new technology vendor

    Validation:
    - vendor_name: required, unique, max 255 chars
    - notes: optional, max 10000 chars
    """
    form = VendorForm()

    if form.validate_on_submit():
        try:
            # Create new vendor
            vendor = TechnologyVendor(
                vendor_name=form.vendor_name.data,
                notes=form.notes.data,
                created_by=current_user.user_id,
                modified_by=current_user.user_id
            )

            db_session.add(vendor)
            db_session.flush()

            sync_company_from_vendor(vendor, current_user.user_id)
            db_session.commit()

            flash(f'Vendor "{vendor.vendor_name}" created successfully', 'success')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor.vendor_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error creating vendor: {str(e)}', 'error')

    return render_template('vendors/form.html', form=form, title='Create Vendor')


@bp.route('/<int:vendor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vendor(vendor_id):
    """
    Edit existing technology vendor

    Validation:
    - Same as create
    - Checks uniqueness excluding current vendor
    """
    vendor = db_session.get(TechnologyVendor, vendor_id)

    if not vendor:
        flash('Vendor not found', 'error')
        abort(404)

    form = VendorForm(vendor_id=vendor_id, obj=vendor)

    if form.validate_on_submit():
        try:
            # Update vendor
            vendor.vendor_name = form.vendor_name.data
            vendor.notes = form.notes.data
            vendor.modified_by = current_user.user_id
            vendor.modified_date = datetime.utcnow()

            sync_company_from_vendor(vendor, current_user.user_id)
            db_session.commit()

            flash(f'Vendor "{vendor.vendor_name}" updated successfully', 'success')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor.vendor_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error updating vendor: {str(e)}', 'error')

    return render_template(
        'vendors/form.html',
        form=form,
        title=f'Edit Vendor: {vendor.vendor_name}',
        vendor=vendor
    )


@bp.route('/<int:vendor_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_vendor(vendor_id):
    """
    Delete technology vendor

    Business Rules:
    - Only admins can delete
    - Cannot delete if products exist
    - Cannot delete if active relationships exist
    - Shows confirmation page with dependency information
    """
    vendor = db_session.get(TechnologyVendor, vendor_id)

    if not vendor:
        flash('Vendor not found', 'error')
        abort(404)

    # Check for dependencies
    product_count = db_session.query(func.count(Product.product_id)).filter(
        Product.vendor_id == vendor_id
    ).scalar()

    relationship_count = db_session.query(func.count(ProjectVendorRelationship.relationship_id)).filter(
        ProjectVendorRelationship.vendor_id == vendor_id
    ).scalar()

    has_dependencies = product_count > 0 or relationship_count > 0

    form = DeleteVendorForm()

    if form.validate_on_submit():
        if has_dependencies:
            flash(
                f'Cannot delete vendor "{vendor.vendor_name}" - it has {product_count} product(s) '
                f'and {relationship_count} relationship(s). Please remove dependencies first.',
                'error'
            )
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

        try:
            vendor_name = vendor.vendor_name
            db_session.delete(vendor)
            db_session.commit()

            flash(f'Vendor "{vendor_name}" deleted successfully', 'success')
            return redirect(url_for('vendors.list_vendors'))

        except Exception as e:
            db_session.rollback()
            flash(f'Error deleting vendor: {str(e)}', 'error')
            return redirect(url_for('vendors.view_vendor', vendor_id=vendor_id))

    return render_template(
        'vendors/delete.html',
        vendor=vendor,
        form=form,
        product_count=product_count,
        relationship_count=relationship_count,
        has_dependencies=has_dependencies
    )


# =============================================================================
# API ENDPOINTS (Optional - for AJAX operations)
# =============================================================================

@bp.route('/api/search')
@login_required
def api_search_vendors():
    """
    API endpoint for vendor search (autocomplete)

    Query params:
        q: search query
        limit: max results (default 10)

    Returns:
        JSON array of {id, name}
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query or len(query) < 2:
        return jsonify([])

    vendors = db_session.query(TechnologyVendor).filter(
        TechnologyVendor.vendor_name.ilike(f'%{query}%')
    ).order_by(TechnologyVendor.vendor_name).limit(limit).all()

    return jsonify([
        {
            'id': vendor.vendor_id,
            'name': vendor.vendor_name
        }
        for vendor in vendors
    ])


@bp.route('/api/<int:vendor_id>')
@login_required
def api_get_vendor(vendor_id):
    """
    API endpoint to get vendor details

    Returns:
        JSON object with vendor data
    """
    vendor = db_session.get(TechnologyVendor, vendor_id)

    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404

    return jsonify({
        'vendor_id': vendor.vendor_id,
        'vendor_name': vendor.vendor_name,
        'notes': vendor.notes,
        'created_date': vendor.created_date.isoformat() if vendor.created_date else None,
        'modified_date': vendor.modified_date.isoformat() if vendor.modified_date else None
    })
