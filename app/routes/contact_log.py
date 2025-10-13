"""Contact log routes for CRM tracking"""
from datetime import date

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db_session
from app.models import (
    ContactLog,
    Company,
    ClientProfile,
    Project,
    Personnel
)
from app.forms.contact_log import ContactLogForm
from app.utils.permissions import can_view_relationship
from app.utils.validators import VALID_CONTACT_TYPES
from app.services.company_query import (
    get_company_for_vendor,
    get_company_for_owner,
    get_company_for_operator,
    get_company_for_constructor,
    get_company_for_offtaker,
    get_company_for_client,
)


bp = Blueprint('contact_log', __name__, url_prefix='/contact-log')


# -----------------------------------------------------------------------------
# Helper utilities
# -----------------------------------------------------------------------------


def _user_can_view(log: ContactLog) -> bool:
    """Return True if current user can view the contact log"""
    return can_view_relationship(current_user, log)


_LEGACY_COMPANY_LOOKUPS = {
    'Vendor': get_company_for_vendor,
    'Owner': get_company_for_owner,
    'Developer': get_company_for_owner,
    'Operator': get_company_for_operator,
    'Constructor': get_company_for_constructor,
    'Offtaker': get_company_for_offtaker,
    'Client': get_company_for_client,
}


def _resolve_company(entity_type: str, entity_id: int) -> Company | None:
    """Return the unified company record for the supplied entity_type/id."""
    if entity_type == 'Company':
        return db_session.get(Company, entity_id)

    lookup = _LEGACY_COMPANY_LOOKUPS.get(entity_type)
    if lookup:
        return lookup(entity_id)
    return None


def _get_entity_label(entity_type: str, entity_id: int) -> str:
    """Return a friendly label for the entity referenced by a contact log"""
    if entity_type == 'Project':
        project = db_session.get(Project, entity_id)
        return project.project_name if project else f'Project #{entity_id}'

    company = _resolve_company(entity_type, entity_id)
    if company:
        return company.company_name

    return f'{entity_type} #{entity_id}'


def _ensure_entity_exists(entity_type: str, entity_id: int):
    """Ensure referenced entity exists; abort with 404 otherwise"""
    record = None
    if entity_type == 'Project':
        record = db_session.get(Project, entity_id)
    elif entity_type in {'Company', *tuple(_LEGACY_COMPANY_LOOKUPS.keys())}:
        record = _resolve_company(entity_type, entity_id)

    if entity_type in {'Company', 'Owner', 'Vendor', 'Developer', 'Operator', 'Constructor', 'Offtaker', 'Client', 'Project'} and record is None:
        abort(404)


def _internal_personnel_choices():
    """Return choices list for internal personnel (active)"""
    personnel = db_session.query(Personnel).filter_by(personnel_type='Internal', is_active=True).order_by(Personnel.full_name).all()
    return [(person.personnel_id, person.full_name) for person in personnel]


def _contact_person_choices(entity_type: str, entity_id: int):
    """Return personnel choices related to the entity"""
    query = db_session.query(Personnel).order_by(Personnel.full_name)
    if entity_type in {'Owner', 'Vendor', 'Project'}:
        query = query.filter(
            Personnel.organization_type == entity_type,
            Personnel.organization_id == entity_id
        )
    contacts = query.all()
    return [(person.personnel_id, person.full_name) for person in contacts]


def _current_user_personnel_id():
    """Best-effort mapping of current user to a personnel record"""
    if not current_user or not getattr(current_user, 'email', None):
        return None
    person = db_session.query(Personnel).filter(
        Personnel.personnel_type == 'Internal',
        Personnel.email.ilike(current_user.email)
    ).first()
    if person:
        return person.personnel_id

    # Fallback to matching full name
    if getattr(current_user, 'full_name', None):
        person = db_session.query(Personnel).filter(
            Personnel.personnel_type == 'Internal',
            Personnel.full_name.ilike(current_user.full_name)
        ).first()
        if person:
            return person.personnel_id

    return None


def _apply_contact_filters(query, entity_type=None, entity_id=None, search=None):
    """Apply common filters for contact log list views"""
    if entity_type:
        query = query.filter(ContactLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(ContactLog.entity_id == entity_id)

    if search:
        like_term = f'%{search.lower()}%'
        query = query.filter(
            or_(
                ContactLog.summary.ilike(like_term),
                ContactLog.contact_person_freetext.ilike(like_term)
            )
        )

    if not (current_user.is_admin or current_user.has_confidential_access):
        query = query.filter(ContactLog.is_confidential.is_(False))

    return query


def _update_company_contact_metrics(company_id: int):
    """Update company's client profile last/next contact fields based on contact log data"""
    company = db_session.get(Company, company_id)
    if not company:
        return

    # Get or create client profile for this company
    client_profile = db_session.get(ClientProfile, company_id)
    if not client_profile:
        client_profile = ClientProfile(company_id=company_id)
        db_session.add(client_profile)

    # Query contact logs - support both 'Company' and legacy entity types
    logs = db_session.query(ContactLog).filter(
        (ContactLog.entity_type == 'Company') |
        (ContactLog.entity_type.in_(['Owner', 'Vendor', 'Developer', 'Client'])),
        ContactLog.entity_id == company_id
    ).order_by(ContactLog.contact_date.desc(), ContactLog.contact_id.desc()).all()

    if logs:
        latest = logs[0]
        client_profile.last_contact_date = latest.contact_date
        client_profile.last_contact_type = latest.contact_type
        client_profile.last_contact_by = latest.contacted_by
    else:
        client_profile.last_contact_date = None
        client_profile.last_contact_type = None
        client_profile.last_contact_by = None

    # Determine next planned contact (earliest future follow-up)
    upcoming = [log for log in logs if log.follow_up_needed and log.follow_up_date]
    upcoming = [log for log in upcoming if log.follow_up_date > date.today()]

    if upcoming:
        upcoming.sort(key=lambda l: (l.follow_up_date, l.contact_id))
        next_contact = upcoming[0]
        client_profile.next_planned_contact_date = next_contact.follow_up_date
        client_profile.next_planned_contact_type = next_contact.contact_type
        client_profile.next_planned_contact_assigned_to = next_contact.follow_up_assigned_to
    else:
        client_profile.next_planned_contact_date = None
        client_profile.next_planned_contact_type = None
        client_profile.next_planned_contact_assigned_to = None


def _redirect_after_save(entity_type: str, entity_id: int):
    """Redirect to appropriate view after saving a contact log.

    For legacy entity types (Owner, Vendor, etc.), redirect to the unified companies view.
    """
    if entity_type == 'Project':
        return redirect(url_for('projects.view_project', project_id=entity_id))
    elif entity_type in ('Company', 'Owner', 'Vendor', 'Developer', 'Operator', 'Constructor', 'Offtaker', 'Client'):
        # All company-related entity types redirect to unified companies view
        return redirect(url_for('companies.view_company', company_id=entity_id))
    else:
        # Fallback to contact log list
        return redirect(url_for('contact_log.list_contact_logs'))


def _populate_form_choices(form: ContactLogForm, entity_type: str, entity_id: int):
    personnel_choices = _internal_personnel_choices()
    contact_person_choices = _contact_person_choices(entity_type, entity_id)
    follow_up_choices = personnel_choices

    form.contact_type.choices = [('', '-- Select contact type --')] + [(value, value) for value in VALID_CONTACT_TYPES]
    form.contacted_by.choices = [(0, '-- Select representative --')] + personnel_choices
    form.contact_person_id.choices = [(0, '-- Select contact (optional) --')] + contact_person_choices
    form.follow_up_assigned_to.choices = [(0, '-- Select assignee --')] + follow_up_choices


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@bp.route('/')
@login_required
def list_contact_logs():
    """List contact logs with optional filters"""
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id', type=int)
    search = request.args.get('search', '').strip()

    query = db_session.query(ContactLog).order_by(ContactLog.contact_date.desc(), ContactLog.contact_id.desc())
    query = _apply_contact_filters(query, entity_type, entity_id, search or None)

    contact_logs = query.all()

    # Separate visibility to inform message
    hidden_count = 0
    if not (current_user.is_admin or current_user.has_confidential_access) and entity_type and entity_id:
        total_count = db_session.query(ContactLog).filter_by(entity_type=entity_type, entity_id=entity_id).count()
        hidden_count = max(total_count - len(contact_logs), 0)

    enriched_logs = []
    for log in contact_logs:
        enriched_logs.append({
            'log': log,
            'entity_label': _get_entity_label(log.entity_type, log.entity_id)
        })

    return render_template(
        'contact_log/list.html',
        contact_logs=enriched_logs,
        hidden_count=hidden_count,
        visible_count=len(contact_logs),
        entity_type=entity_type,
        entity_id=entity_id,
        search=search
    )


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_contact_log():
    entity_type = request.args.get('entity_type', 'Owner')
    entity_id = request.args.get('entity_id', type=int)

    if not entity_id:
        flash('An entity must be specified to log a contact.', 'warning')
        return redirect(url_for('contact_log.list_contact_logs'))

    _ensure_entity_exists(entity_type, entity_id)

    form = ContactLogForm()
    _populate_form_choices(form, entity_type, entity_id)
    form.entity_type.data = entity_type
    form.entity_id.data = str(entity_id)

    current_personnel_id = _current_user_personnel_id()
    if request.method == 'GET' and current_personnel_id:
        form.contacted_by.data = current_personnel_id
    elif request.method == 'POST' and form.contacted_by.data is None:
        form.contacted_by.data = current_personnel_id or 0

    if form.validate_on_submit():
        contact_log = ContactLog(
            entity_type=form.entity_type.data,
            entity_id=int(form.entity_id.data),
            contact_date=form.contact_date.data,
            contact_type=form.contact_type.data,
            contacted_by=form.contacted_by.data,
            contact_person_id=form.contact_person_id.data or None,
            contact_person_freetext=form.contact_person_freetext.data or None,
            summary=form.summary.data,
            is_confidential=form.is_confidential.data,
            follow_up_needed=form.follow_up_needed.data,
            follow_up_date=form.follow_up_date.data if form.follow_up_needed.data else None,
            follow_up_assigned_to=form.follow_up_assigned_to.data or None,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )

        try:
            db_session.add(contact_log)
            db_session.commit()
        except Exception as exc:  # pragma: no cover - defensive
            db_session.rollback()
            flash(f'Error saving contact log: {exc}', 'danger')
            return render_template('contact_log/form.html', form=form, title='Add Contact Log', entity_label=_get_entity_label(entity_type, entity_id))

        # Update contact metrics for Company/Client entities
        if entity_type in ('Company', 'Owner', 'Vendor', 'Developer', 'Client'):
            _update_company_contact_metrics(contact_log.entity_id)
            db_session.commit()

        flash('Contact log entry saved.', 'success')
        return _redirect_after_save(contact_log.entity_type, contact_log.entity_id)

    if form.follow_up_needed.data:
        # ensure follow-up fields display when returning form with errors
        followup_checked = True
    else:
        followup_checked = False

    return render_template(
        'contact_log/form.html',
        form=form,
        title='Add Contact Log Entry',
        entity_label=_get_entity_label(entity_type, entity_id),
        followup_checked=followup_checked,
        today=date.today().isoformat()
    )


@bp.route('/<int:contact_id>')
@login_required
def view_contact_log(contact_id):
    contact_log = db_session.get(ContactLog, contact_id)
    if not contact_log:
        abort(404)

    if not _user_can_view(contact_log):
        flash('You do not have permission to view this contact log.', 'warning')
        return redirect(url_for('contact_log.list_contact_logs'))

    return render_template(
        'contact_log/detail.html',
        contact_log=contact_log,
        entity_label=_get_entity_label(contact_log.entity_type, contact_log.entity_id)
    )


@bp.route('/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact_log(contact_id):
    contact_log = db_session.get(ContactLog, contact_id)
    if not contact_log:
        abort(404)

    if not _user_can_view(contact_log):
        flash('You do not have permission to edit this contact log.', 'warning')
        return redirect(url_for('contact_log.list_contact_logs'))

    form = ContactLogForm()
    _populate_form_choices(form, contact_log.entity_type, contact_log.entity_id)

    if request.method == 'GET':
        form.entity_type.data = contact_log.entity_type
        form.entity_id.data = str(contact_log.entity_id)
        form.contact_date.data = contact_log.contact_date
        form.contact_type.data = contact_log.contact_type
        form.contacted_by.data = contact_log.contacted_by
        form.contact_person_id.data = contact_log.contact_person_id or 0
        form.contact_person_freetext.data = contact_log.contact_person_freetext
        form.summary.data = contact_log.summary
        form.follow_up_needed.data = contact_log.follow_up_needed
        form.follow_up_date.data = contact_log.follow_up_date
        form.follow_up_assigned_to.data = contact_log.follow_up_assigned_to or 0
        form.is_confidential.data = contact_log.is_confidential

    if form.validate_on_submit():
        contact_log.contact_date = form.contact_date.data
        contact_log.contact_type = form.contact_type.data
        contact_log.contacted_by = form.contacted_by.data
        contact_log.contact_person_id = form.contact_person_id.data or None
        contact_log.contact_person_freetext = form.contact_person_freetext.data or None
        contact_log.summary = form.summary.data
        contact_log.is_confidential = form.is_confidential.data
        contact_log.follow_up_needed = form.follow_up_needed.data
        if form.follow_up_needed.data:
            contact_log.follow_up_date = form.follow_up_date.data
            contact_log.follow_up_assigned_to = form.follow_up_assigned_to.data or None
        else:
            contact_log.follow_up_date = None
            contact_log.follow_up_assigned_to = None
        contact_log.modified_by = current_user.user_id

        try:
            db_session.commit()
        except Exception as exc:  # pragma: no cover
            db_session.rollback()
            flash(f'Error updating contact log: {exc}', 'danger')
            return render_template('contact_log/form.html', form=form, title='Edit Contact Log', entity_label=_get_entity_label(contact_log.entity_type, contact_log.entity_id), followup_checked=form.follow_up_needed.data)

        # Update contact metrics for Company/Client entities
        if contact_log.entity_type in ('Company', 'Owner', 'Vendor', 'Developer', 'Client'):
            _update_company_contact_metrics(contact_log.entity_id)
            db_session.commit()

        flash('Contact log updated.', 'success')
        return _redirect_after_save(contact_log.entity_type, contact_log.entity_id)

    followup_checked = form.follow_up_needed.data or bool(contact_log.follow_up_needed)

    return render_template(
        'contact_log/form.html',
        form=form,
        title='Edit Contact Log Entry',
        entity_label=_get_entity_label(contact_log.entity_type, contact_log.entity_id),
        followup_checked=followup_checked,
        today=date.today().isoformat()
    )
