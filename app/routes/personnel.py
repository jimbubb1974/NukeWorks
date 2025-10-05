"""Personnel list and management routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db_session
from app.models import Personnel
from app.forms.personnel import PersonnelForm


bp = Blueprint('personnel', __name__, url_prefix='/personnel')


def _query_personnel(search_term: str | None, include_internal: bool | None) -> list[Personnel]:
    """Return personnel filtered by optional search term and type."""
    query = db_session.query(Personnel)

    if include_internal is True:
        query = query.filter(Personnel.personnel_type == 'Internal')
    elif include_internal is False:
        query = query.filter(Personnel.personnel_type != 'Internal')

    if search_term:
        like_term = f"%{search_term.strip()}%"
        query = query.filter(
            or_(
                Personnel.full_name.ilike(like_term),
                Personnel.email.ilike(like_term),
                Personnel.role.ilike(like_term),
                Personnel.personnel_type.ilike(like_term),
            )
        )

    return query.order_by(Personnel.full_name).all()


@bp.route('/')
@login_required
def list_personnel():
    """List internal and external personnel with optional search."""
    search_term = request.args.get('q', '').strip()

    internal_personnel = _query_personnel(search_term, include_internal=True)
    external_personnel = _query_personnel(search_term, include_internal=False)

    return render_template(
        'personnel/list.html',
        search_term=search_term,
        internal_personnel=internal_personnel,
        external_personnel=external_personnel,
    )


@bp.route('/<int:personnel_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_personnel(personnel_id: int):
    """Edit a personnel record."""
    person = db_session.get(Personnel, personnel_id)
    if not person:
        flash('Personnel record not found.', 'error')
        return redirect(url_for('personnel.list_personnel'))

    form = PersonnelForm(obj=person)
    if form.validate_on_submit():
        person.full_name = form.full_name.data
        person.email = form.email.data or None
        person.phone = form.phone.data or None
        person.role = form.role.data or None
        person.personnel_type = form.personnel_type.data
        person.organization_type = form.organization_type.data or None
        person.is_active = bool(form.is_active.data)
        person.notes = form.notes.data or None
        person.modified_by = current_user.user_id

        db_session.commit()
        flash('Personnel record updated.', 'success')
        return redirect(url_for('personnel.list_personnel'))

    return render_template('personnel/edit.html', form=form, person=person)
