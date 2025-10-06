"""Technology product routes."""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app import db_session
from app.forms.relationships import ConfirmActionForm
from app.forms.technologies import TechnologyForm
from app.models import Product, Company

bp = Blueprint('technologies', __name__, url_prefix='/technologies')


def _get_product_or_404(product_id: int) -> Product:
    product = (
        db_session.query(Product)
        .options(joinedload(Product.company))
        .filter_by(product_id=product_id)
        .first()
    )
    if not product:
        flash('Technology product not found.', 'error')
        abort(404)
    return product


def _can_manage(user) -> bool:
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


def _company_choices(include_placeholder: bool = True):
    companies = db_session.query(Company).order_by(Company.company_name).all()
    choices = [(company.company_id, company.company_name) for company in companies]
    if include_placeholder:
        choices.insert(0, (0, '-- Select Company --'))
    return choices


@bp.route('/')
@login_required
def list_technologies():
    products = (
        db_session.query(Product)
        .options(joinedload(Product.company))
        .order_by(Product.product_name)
        .all()
    )
    return render_template(
        'technologies/list.html',
        products=products,
        can_manage=_can_manage(current_user)
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_technology():
    if not _can_manage(current_user):
        flash('You do not have permission to create technologies.', 'danger')
        return redirect(url_for('technologies.list_technologies'))

    form = TechnologyForm()
    form.company_id.choices = _company_choices()

    preselected_company = request.args.get('company_id', type=int)
    if not form.is_submitted() and preselected_company:
        valid_ids = {choice[0] for choice in form.company_id.choices}
        if preselected_company in valid_ids:
            form.company_id.data = preselected_company

    if form.validate_on_submit():
        if form.company_id.data == 0:
            flash('Please select a company.', 'warning')
            return render_template('technologies/form.html', form=form, title='Create Technology', product=None)

        product = Product(
            product_name=form.product_name.data,
            company_id=form.company_id.data,
            reactor_type=form.reactor_type.data or None,
            generation=form.generation.data or None,
            thermal_capacity=form.gross_capacity_mwt.data or None,
            gross_capacity_mwt=form.gross_capacity_mwt.data or None,
            thermal_efficiency=form.thermal_efficiency.data or None,
            fuel_type=form.fuel_type.data or None,
            fuel_enrichment=form.fuel_enrichment.data or None,
            design_status=form.design_status.data or None,
            mpr_project_ids=form.mpr_project_ids.data or None,
            notes=form.notes.data or None,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )
        product.modified_date = datetime.utcnow()

        try:
            db_session.add(product)
            db_session.commit()
            flash('Technology created successfully.', 'success')
            return redirect(url_for('technologies.view_technology', product_id=product.product_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error creating technology: {exc}', 'danger')

    return render_template('technologies/form.html', form=form, title='Create Technology', product=None)


@bp.route('/<int:product_id>')
@login_required
def view_technology(product_id):
    product = _get_product_or_404(product_id)
    can_manage = _can_manage(current_user)
    delete_form = ConfirmActionForm()
    return render_template(
        'technologies/detail.html',
        product=product,
        can_manage=can_manage,
        delete_form=delete_form
    )


@bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_technology(product_id):
    product = _get_product_or_404(product_id)

    if not _can_manage(current_user):
        flash('You do not have permission to edit technologies.', 'danger')
        return redirect(url_for('technologies.view_technology', product_id=product_id))

    form = TechnologyForm(obj=product)
    form.company_id.choices = _company_choices(include_placeholder=False)
    if not form.is_submitted():
        form.company_id.data = product.company_id
        form.gross_capacity_mwt.data = product.gross_capacity_mwt or product.thermal_capacity
        form.thermal_efficiency.data = product.thermal_efficiency

    if form.validate_on_submit():
        if form.company_id.data == 0:
            flash('Please select a company.', 'warning')
            return render_template('technologies/form.html', form=form, title=f'Edit Technology: {product.product_name}', product=product)

        product.product_name = form.product_name.data
        product.company_id = form.company_id.data
        product.reactor_type = form.reactor_type.data or None
        product.generation = form.generation.data or None
        product.gross_capacity_mwt = form.gross_capacity_mwt.data or None
        product.thermal_capacity = form.gross_capacity_mwt.data or None
        product.thermal_efficiency = form.thermal_efficiency.data or None
        product.fuel_type = form.fuel_type.data or None
        product.fuel_enrichment = form.fuel_enrichment.data or None
        product.design_status = form.design_status.data or None
        product.mpr_project_ids = form.mpr_project_ids.data or None
        product.notes = form.notes.data or None
        product.modified_by = current_user.user_id
        product.modified_date = datetime.utcnow()

        try:
            db_session.commit()
            flash('Technology updated successfully.', 'success')
            return redirect(url_for('technologies.view_technology', product_id=product.product_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error updating technology: {exc}', 'danger')

    return render_template('technologies/form.html', form=form, title=f'Edit Technology: {product.product_name}', product=product)


@bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_technology(product_id):
    product = _get_product_or_404(product_id)

    if not current_user.is_admin:
        flash('Only administrators can delete technologies.', 'danger')
        return redirect(url_for('technologies.view_technology', product_id=product_id))

    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Invalid request.', 'danger')
        return redirect(url_for('technologies.view_technology', product_id=product_id))

    try:
        db_session.delete(product)
        db_session.commit()
        flash('Technology deleted.', 'success')
    except Exception as exc:  # pragma: no cover
        db_session.rollback()
        flash(f'Error deleting technology: {exc}', 'danger')
        return redirect(url_for('technologies.view_technology', product_id=product_id))

    return redirect(url_for('technologies.list_technologies'))
