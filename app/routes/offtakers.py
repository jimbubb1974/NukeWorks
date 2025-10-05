"""Energy off-taker routes."""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db_session
from app.forms.offtakers import OfftakerForm
from app.forms.relationships import ConfirmActionForm
from app.models import Offtaker, ProjectOfftakerRelationship
from app.utils.permissions import filter_relationships

bp = Blueprint('offtakers', __name__, url_prefix='/offtakers')


def _get_offtaker_or_404(offtaker_id: int) -> Offtaker:
    offtaker = db_session.get(Offtaker, offtaker_id)
    if not offtaker:
        flash('Off-taker not found.', 'error')
        abort(404)
    return offtaker


def _can_manage(user) -> bool:
    return bool(user and (user.is_admin or getattr(user, 'is_ned_team', False)))


@bp.route('/')
@login_required
def list_offtakers():
    offtakers = db_session.query(Offtaker).order_by(Offtaker.organization_name).all()
    return render_template(
        'offtakers/list.html',
        offtakers=offtakers,
        can_manage=_can_manage(current_user)
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_offtaker():
    if not _can_manage(current_user):
        flash('You do not have permission to create off-takers.', 'danger')
        return redirect(url_for('offtakers.list_offtakers'))

    form = OfftakerForm()
    if form.validate_on_submit():
        offtaker = Offtaker(
            organization_name=form.organization_name.data,
            sector=form.sector.data or None,
            notes=form.notes.data or None,
            created_by=current_user.user_id,
            modified_by=current_user.user_id,
        )
        offtaker.modified_date = datetime.utcnow()

        try:
            db_session.add(offtaker)
            db_session.commit()
            flash('Off-taker created successfully.', 'success')
            return redirect(url_for('offtakers.view_offtaker', offtaker_id=offtaker.offtaker_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error creating off-taker: {exc}', 'danger')

    return render_template('offtakers/form.html', form=form, offtaker=None, title='Create Off-taker')


@bp.route('/<int:offtaker_id>')
@login_required
def view_offtaker(offtaker_id):
    offtaker = _get_offtaker_or_404(offtaker_id)
    relationships = filter_relationships(current_user, offtaker.project_relationships)
    dependent_count = db_session.query(func.count(ProjectOfftakerRelationship.relationship_id)).filter_by(offtaker_id=offtaker.offtaker_id).scalar()
    delete_form = ConfirmActionForm()

    return render_template(
        'offtakers/detail.html',
        offtaker=offtaker,
        relationships=relationships,
        dependent_count=dependent_count,
        can_manage=_can_manage(current_user),
        delete_form=delete_form
    )


@bp.route('/<int:offtaker_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_offtaker(offtaker_id):
    offtaker = _get_offtaker_or_404(offtaker_id)

    if not _can_manage(current_user):
        flash('You do not have permission to edit off-takers.', 'danger')
        return redirect(url_for('offtakers.view_offtaker', offtaker_id=offtaker_id))

    form = OfftakerForm(obj=offtaker)
    if form.validate_on_submit():
        offtaker.organization_name = form.organization_name.data
        offtaker.sector = form.sector.data or None
        offtaker.notes = form.notes.data or None
        offtaker.modified_by = current_user.user_id
        offtaker.modified_date = datetime.utcnow()

        try:
            db_session.commit()
            flash('Off-taker updated successfully.', 'success')
            return redirect(url_for('offtakers.view_offtaker', offtaker_id=offtaker.offtaker_id))
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error updating off-taker: {exc}', 'danger')

    return render_template('offtakers/form.html', form=form, offtaker=offtaker, title=f'Edit Off-taker: {offtaker.organization_name}')


@bp.route('/<int:offtaker_id>/delete', methods=['POST'])
@login_required
def delete_offtaker(offtaker_id):
    offtaker = _get_offtaker_or_404(offtaker_id)

    if not current_user.is_admin:
        flash('Only administrators can delete off-takers.', 'danger')
        return redirect(url_for('offtakers.view_offtaker', offtaker_id=offtaker_id))

    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash('Invalid request.', 'danger')
        return redirect(url_for('offtakers.view_offtaker', offtaker_id=offtaker_id))

    dependent_count = db_session.query(func.count(ProjectOfftakerRelationship.relationship_id)).filter_by(offtaker_id=offtaker.offtaker_id).scalar()
    if dependent_count > 0:
        flash('Cannot delete off-taker with linked projects. Remove associations first.', 'warning')
        return redirect(url_for('offtakers.view_offtaker', offtaker_id=offtaker_id))

    try:
        db_session.delete(offtaker)
        db_session.commit()
        flash('Off-taker deleted.', 'success')
    except Exception as exc:  # pragma: no cover
        db_session.rollback()
        flash(f'Error deleting off-taker: {exc}', 'danger')
        return redirect(url_for('offtakers.view_offtaker', offtaker_id=offtaker_id))

    return redirect(url_for('offtakers.list_offtakers'))
