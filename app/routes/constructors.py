"""Constructor routes for viewing and managing constructors."""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db_session
from app.forms.constructors import ConstructorForm
from app.forms.relationships import ConfirmActionForm
from app.models import Constructor, ProjectConstructorRelationship, VendorPreferredConstructor
from app.utils.permissions import filter_relationships
from app.services.company_sync import sync_company_from_constructor
from app.services.company_query import get_company_for_constructor

bp = Blueprint('constructors', __name__, url_prefix='/constructors')


def _get_constructor_or_404(constructor_id: int) -> Constructor:
    constructor = db_session.get(Constructor, constructor_id)
    if not constructor:
        flash('Constructor not found.', 'error')
        abort(404)
    return constructor


def _can_manage(user) -> bool:
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


@bp.route('/')
@login_required
def list_constructors():
    """List all constructors."""
    constructors = db_session.query(Constructor).order_by(Constructor.company_name).all()
    constructor_company_map = {
        constructor.constructor_id: get_company_for_constructor(constructor.constructor_id)
        for constructor in constructors
    }
    return render_template(
        'constructors/list.html',
        constructors=constructors,
        can_manage=_can_manage(current_user),
        constructor_company_map=constructor_company_map
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_constructor():
    """Create a new constructor."""
    if not _can_manage(current_user):
        flash('You do not have permission to create constructors.', 'danger')
        return redirect(url_for('constructors.list_constructors'))

    form = ConstructorForm()

    if form.validate_on_submit():
        constructor = Constructor(
            company_name=form.company_name.data,
            notes=form.notes.data or None,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )
        try:
            db_session.add(constructor)
            db_session.flush()
            sync_company_from_constructor(constructor, current_user.user_id)
            db_session.commit()
            flash('Constructor created successfully.', 'success')
            return redirect(url_for('constructors.view_constructor', constructor_id=constructor.constructor_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error creating constructor: {exc}', 'danger')

    return render_template('constructors/form.html', form=form, title='Create Constructor', constructor=None)


@bp.route('/<int:constructor_id>')
@login_required
def view_constructor(constructor_id):
    """Display constructor details and relationships."""
    constructor = _get_constructor_or_404(constructor_id)
    project_relationships = filter_relationships(current_user, constructor.project_relationships)
    preferred_by_vendors = filter_relationships(current_user, constructor.vendor_preferences)
    can_manage = _can_manage(current_user)
    company_record = get_company_for_constructor(constructor.constructor_id)

    project_count = db_session.query(func.count(ProjectConstructorRelationship.relationship_id)).filter(
        ProjectConstructorRelationship.constructor_id == constructor.constructor_id
    ).scalar()

    vendor_preference_count = db_session.query(func.count(VendorPreferredConstructor.relationship_id)).filter(
        VendorPreferredConstructor.constructor_id == constructor.constructor_id
    ).scalar()

    return render_template(
        'constructors/detail.html',
        constructor=constructor,
        project_relationships=project_relationships,
        preferred_by_vendors=preferred_by_vendors,
        can_manage=can_manage,
        project_count=project_count,
        vendor_preference_count=vendor_preference_count,
        delete_form=ConfirmActionForm(),
        company_record=company_record,
    )


@bp.route('/<int:constructor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_constructor(constructor_id):
    """Edit constructor details."""
    constructor = _get_constructor_or_404(constructor_id)

    if not _can_manage(current_user):
        flash('You do not have permission to edit constructors.', 'danger')
        return redirect(url_for('constructors.view_constructor', constructor_id=constructor_id))

    form = ConstructorForm(obj=constructor)

    if form.validate_on_submit():
        constructor.company_name = form.company_name.data
        constructor.notes = form.notes.data or None
        constructor.modified_by = current_user.user_id
        constructor.modified_date = datetime.utcnow()

        try:
            sync_company_from_constructor(constructor, current_user.user_id)
            db_session.commit()
            flash('Constructor updated successfully.', 'success')
            return redirect(url_for('constructors.view_constructor', constructor_id=constructor.constructor_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error updating constructor: {exc}', 'danger')

    return render_template('constructors/form.html', form=form, title=f'Edit Constructor: {constructor.company_name}', constructor=constructor)


@bp.route('/<int:constructor_id>/delete', methods=['POST'])
@login_required
def delete_constructor(constructor_id):
    """Delete a constructor if there are no blocking relationships."""
    constructor = _get_constructor_or_404(constructor_id)

    if not current_user.is_admin:
        flash('Only administrators can delete constructors.', 'danger')
        return redirect(url_for('constructors.view_constructor', constructor_id=constructor_id))

    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Invalid request.', 'danger')
        return redirect(url_for('constructors.view_constructor', constructor_id=constructor_id))

    project_count = db_session.query(func.count(ProjectConstructorRelationship.relationship_id)).filter(
        ProjectConstructorRelationship.constructor_id == constructor.constructor_id
    ).scalar()

    vendor_preference_count = db_session.query(func.count(VendorPreferredConstructor.relationship_id)).filter(
        VendorPreferredConstructor.constructor_id == constructor.constructor_id
    ).scalar()

    if project_count > 0 or vendor_preference_count > 0:
        flash(
            'Cannot delete constructor with existing project or vendor preference relationships. '
            'Remove dependencies first.',
            'warning'
        )
        return redirect(url_for('constructors.view_constructor', constructor_id=constructor_id))

    try:
        db_session.delete(constructor)
        db_session.commit()
        flash('Constructor deleted.', 'success')
    except Exception as exc:  # pragma: no cover
        db_session.rollback()
        flash(f'Error deleting constructor: {exc}', 'danger')

    return redirect(url_for('constructors.list_constructors'))
