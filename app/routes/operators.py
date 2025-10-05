"""Operator routes for viewing and managing operators."""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db_session
from app.forms.operators import OperatorForm
from app.forms.relationships import ConfirmActionForm
from app.models import Operator, ProjectOperatorRelationship
from app.utils.permissions import filter_relationships

bp = Blueprint('operators', __name__, url_prefix='/operators')


def _get_operator_or_404(operator_id: int) -> Operator:
    operator = db_session.get(Operator, operator_id)
    if not operator:
        flash('Operator not found.', 'error')
        abort(404)
    return operator


def _can_manage(user) -> bool:
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


@bp.route('/')
@login_required
def list_operators():
    """List all operators."""
    operators = db_session.query(Operator).order_by(Operator.company_name).all()
    return render_template('operators/list.html', operators=operators, can_manage=_can_manage(current_user))


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_operator():
    """Create a new operator."""
    if not _can_manage(current_user):
        flash('You do not have permission to create operators.', 'danger')
        return redirect(url_for('operators.list_operators'))

    form = OperatorForm()

    if form.validate_on_submit():
        operator = Operator(
            company_name=form.company_name.data,
            notes=form.notes.data or None,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )
        try:
            db_session.add(operator)
            db_session.commit()
            flash('Operator created successfully.', 'success')
            return redirect(url_for('operators.view_operator', operator_id=operator.operator_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error creating operator: {exc}', 'danger')

    return render_template('operators/form.html', form=form, title='Create Operator', operator=None)


@bp.route('/<int:operator_id>')
@login_required
def view_operator(operator_id):
    """Display operator details and related projects."""
    operator = _get_operator_or_404(operator_id)
    project_relationships = filter_relationships(current_user, operator.project_relationships)
    can_manage = _can_manage(current_user)

    dependent_count = db_session.query(func.count(ProjectOperatorRelationship.relationship_id)).filter(
        ProjectOperatorRelationship.operator_id == operator.operator_id
    ).scalar()

    return render_template(
        'operators/detail.html',
        operator=operator,
        project_relationships=project_relationships,
        can_manage=can_manage,
        delete_form=ConfirmActionForm(),
        dependent_count=dependent_count
    )


@bp.route('/<int:operator_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_operator(operator_id):
    """Edit operator details."""
    operator = _get_operator_or_404(operator_id)

    if not _can_manage(current_user):
        flash('You do not have permission to edit operators.', 'danger')
        return redirect(url_for('operators.view_operator', operator_id=operator_id))

    form = OperatorForm(obj=operator)

    if form.validate_on_submit():
        operator.company_name = form.company_name.data
        operator.notes = form.notes.data or None
        operator.modified_by = current_user.user_id
        operator.modified_date = datetime.utcnow()

        try:
            db_session.commit()
            flash('Operator updated successfully.', 'success')
            return redirect(url_for('operators.view_operator', operator_id=operator.operator_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error updating operator: {exc}', 'danger')

    return render_template('operators/form.html', form=form, title=f'Edit Operator: {operator.company_name}', operator=operator)


@bp.route('/<int:operator_id>/delete', methods=['POST'])
@login_required
def delete_operator(operator_id):
    """Delete an operator if no active project relationships."""
    operator = _get_operator_or_404(operator_id)

    if not current_user.is_admin:
        flash('Only administrators can delete operators.', 'danger')
        return redirect(url_for('operators.view_operator', operator_id=operator_id))

    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Invalid request.', 'danger')
        return redirect(url_for('operators.view_operator', operator_id=operator_id))

    dependent_count = db_session.query(func.count(ProjectOperatorRelationship.relationship_id)).filter(
        ProjectOperatorRelationship.operator_id == operator.operator_id
    ).scalar()

    if dependent_count > 0:
        flash('Cannot delete operator with existing project relationships. Remove relationships first.', 'warning')
        return redirect(url_for('operators.view_operator', operator_id=operator_id))

    try:
        db_session.delete(operator)
        db_session.commit()
        flash('Operator deleted.', 'success')
    except Exception as exc:  # pragma: no cover
        db_session.rollback()
        flash(f'Error deleting operator: {exc}', 'danger')

    return redirect(url_for('operators.list_operators'))
