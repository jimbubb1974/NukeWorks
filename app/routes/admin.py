"""Admin routes for user management and system configuration"""
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app import db_session
from app.forms.auth import CreateUserForm, EditUserForm, AdminChangePasswordForm
from app.forms.system_settings import CompanySettingsForm, BackupSettingsForm, CrmSettingsForm
from app.forms.snapshots import ManualSnapshotForm, SnapshotActionForm
from app.forms.relationships import ConfirmActionForm
from app.models import (
    User,
    ConfidentialFieldFlag,
    ContactLog,
    Project,
    OwnerDeveloper,
    TechnologyVendor,
    VendorSupplierRelationship,
    OwnerVendorRelationship,
    ProjectVendorRelationship,
    ProjectConstructorRelationship,
    ProjectOperatorRelationship,
    ProjectOwnerRelationship,
    VendorPreferredConstructor,
    DatabaseSnapshot,
    AuditLog,
)
from app.utils.permissions import admin_required, mark_field_confidential
from app.utils.system_settings import (
    get_system_setting,
    set_system_setting,
    get_roundtable_history_limit,
)
from app.utils.validators import validate_password_strength, ValidationError as ValidatorError
from app.services.snapshots import (
    create_snapshot,
    restore_snapshot,
    enforce_snapshot_retention,
    get_next_snapshot_run,
    last_snapshot_info,
    should_run_automated_snapshot,
)
from sqlalchemy import or_

bp = Blueprint('admin', __name__, url_prefix='/admin')


AUDIT_ACTIONS = ('CREATE', 'UPDATE', 'DELETE')


def _parse_timestamp(value: str | None):
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


RELATIONSHIP_CONFIG = {
    'vendor_supplier': (
        VendorSupplierRelationship,
        lambda rel: f"{rel.vendor.vendor_name if rel and rel.vendor else 'Vendor'} ↔ {rel.supplier.vendor_name if rel and rel.supplier else 'Supplier'}",
    ),
    'owner_vendor': (
        OwnerVendorRelationship,
        lambda rel: f"{rel.owner.company_name if rel and rel.owner else 'Owner'} ↔ {rel.vendor.vendor_name if rel and rel.vendor else 'Vendor'}",
    ),
    'project_vendor': (
        ProjectVendorRelationship,
        lambda rel: f"{rel.project.project_name if rel and rel.project else 'Project'} ↔ {rel.vendor.vendor_name if rel and rel.vendor else 'Vendor'}",
    ),
    'project_constructor': (
        ProjectConstructorRelationship,
        lambda rel: f"{rel.project.project_name if rel and rel.project else 'Project'} ↔ {rel.constructor.company_name if rel and rel.constructor else 'Constructor'}",
    ),
    'project_operator': (
        ProjectOperatorRelationship,
        lambda rel: f"{rel.project.project_name if rel and rel.project else 'Project'} ↔ {rel.operator.company_name if rel and rel.operator else 'Operator'}",
    ),
    'project_owner': (
        ProjectOwnerRelationship,
        lambda rel: f"{rel.project.project_name if rel and rel.project else 'Project'} ↔ {rel.owner.company_name if rel and rel.owner else 'Owner'}",
    ),
    'vendor_preferred_constructor': (
        VendorPreferredConstructor,
        lambda rel: f"{rel.vendor.vendor_name if rel and rel.vendor else 'Vendor'} ↔ {rel.constructor.company_name if rel and rel.constructor else 'Constructor'}",
    ),
}


def _snapshot_dashboard_context(manual_form: ManualSnapshotForm | None = None):
    snapshots = db_session.query(DatabaseSnapshot).order_by(DatabaseSnapshot.snapshot_timestamp.desc()).all()
    manual_form = manual_form or ManualSnapshotForm()
    restore_forms = {snap.snapshot_id: SnapshotActionForm() for snap in snapshots}

    automated_count = sum(1 for s in snapshots if (s.snapshot_type or '').upper().startswith('AUTOMATED'))
    manual_count = sum(1 for s in snapshots if (s.snapshot_type or '').upper().startswith('MANUAL'))
    retained_count = sum(1 for s in snapshots if s.is_retained)
    total_size = sum((s.snapshot_size_bytes or 0) for s in snapshots)

    enabled, next_run = get_next_snapshot_run()
    now = datetime.utcnow()
    is_overdue = enabled and next_run < now and should_run_automated_snapshot(now)
    last_auto = next((s for s in snapshots if (s.snapshot_type or '').upper().startswith('AUTOMATED')), None)

    stats = {
        'total': len(snapshots),
        'automated': automated_count,
        'manual': manual_count,
        'retained': retained_count,
        'disk_usage_bytes': total_size,
        'last_automated': last_auto,
    }

    return {
        'snapshots': snapshots,
        'manual_form': manual_form,
        'restore_forms': restore_forms,
        'schedule_enabled': enabled,
        'next_run': next_run,
        'schedule_overdue': is_overdue,
        'stats': stats,
        'now': now,
    }


def _resolve_field_display(flag: ConfidentialFieldFlag):
    table = flag.table_name
    record_id = flag.record_id

    entity_label = f"{table.title()} #{record_id}"
    if table == 'projects':
        obj = db_session.get(Project, record_id)
        if obj:
            entity_label = obj.project_name or entity_label
    elif table == 'owners_developers':
        obj = db_session.get(OwnerDeveloper, record_id)
        if obj:
            entity_label = obj.company_name or entity_label
    elif table == 'technology_vendors':
        obj = db_session.get(TechnologyVendor, record_id)
        if obj:
            entity_label = obj.vendor_name or entity_label

    return entity_label, flag.field_name


def _collect_relationship_entries():
    entries = []
    for key, (model, label_func) in RELATIONSHIP_CONFIG.items():
        items = db_session.query(model).order_by(model.relationship_id).all()
        for rel in items:
            entries.append({
                'type': key,
                'id': rel.relationship_id,
                'label': label_func(rel),
                'notes': getattr(rel, 'notes', None) or getattr(rel, 'component_type', None) or getattr(rel, 'preference_reason', None),
                'is_confidential': bool(getattr(rel, 'is_confidential', False)),
            })
    return entries


def _collect_confidential_contacts():
    return db_session.query(ContactLog).filter(ContactLog.is_confidential.is_(True)).order_by(ContactLog.contact_date.desc(), ContactLog.contact_id.desc()).all()


@bp.route('/')
@login_required
@admin_required
def index():
    total_users = db_session.query(User).count()
    active_users = db_session.query(User).filter_by(is_active=True).count()
    inactive_users = total_users - active_users
    return render_template('admin/index.html', user_count=total_users, active_users=active_users, inactive_users=inactive_users)


@bp.route('/snapshots')
@login_required
@admin_required
def snapshots():
    context = _snapshot_dashboard_context()
    context['last_snapshot'] = last_snapshot_info()
    return render_template('admin/snapshots.html', **context)


@bp.route('/snapshots/create', methods=['POST'])
@login_required
@admin_required
def create_manual_snapshot():
    form = ManualSnapshotForm()
    if form.validate_on_submit():
        try:
            snapshot = create_snapshot(
                snapshot_type='MANUAL',
                user_id=current_user.user_id,
                description=form.description.data or None,
                retain=form.retain.data,
            )
            enforce_snapshot_retention()
            flash('Manual snapshot created successfully.', 'success')
            current_app.logger.info('Manual snapshot created: %s', snapshot.file_path)
            return redirect(url_for('admin.snapshots'))
        except FileNotFoundError as exc:
            flash(str(exc), 'danger')
        except Exception as exc:  # pragma: no cover - defensive logging
            current_app.logger.exception('Manual snapshot creation failed: %s', exc)
            flash('Failed to create snapshot. Check server logs for details.', 'danger')
        return redirect(url_for('admin.snapshots'))

    context = _snapshot_dashboard_context(manual_form=form)
    context['last_snapshot'] = last_snapshot_info()
    return render_template('admin/snapshots.html', **context), 400


@bp.route('/snapshots/<int:snapshot_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_snapshot_view(snapshot_id):
    form = SnapshotActionForm()
    if not form.validate_on_submit():
        flash('Restore confirmation failed. Please try again.', 'warning')
        return redirect(url_for('admin.snapshots'))

    try:
        requested_id = int(form.snapshot_id.data)
    except (TypeError, ValueError):
        requested_id = None

    if requested_id != snapshot_id:
        flash('Snapshot mismatch detected. Restore cancelled.', 'warning')
        return redirect(url_for('admin.snapshots'))

    snapshot = db_session.get(DatabaseSnapshot, snapshot_id)
    if not snapshot:
        flash('Snapshot not found.', 'warning')
        return redirect(url_for('admin.snapshots'))

    try:
        backup_path = restore_snapshot(snapshot)
        flash('Database restored from snapshot. Previous database saved to %s.' % backup_path, 'success')
        current_app.logger.warning('Database restored from snapshot %s', snapshot.file_path)
    except FileNotFoundError as exc:
        flash(str(exc), 'danger')
    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.exception('Snapshot restore failed: %s', exc)
        flash('Snapshot restore failed. Check server logs for details.', 'danger')

    return redirect(url_for('admin.snapshots'))


@bp.route('/audit')
@login_required
@admin_required
def audit_log():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = max(10, min(per_page, 200))

    action_filter = request.args.get('action', '').upper().strip()
    table_filter = request.args.get('table', '').strip()
    user_filter = request.args.get('user', type=int)
    search_terms = request.args.get('search', '').strip()
    start_time = _parse_timestamp(request.args.get('start'))
    end_time = _parse_timestamp(request.args.get('end'))

    query = db_session.query(AuditLog).order_by(AuditLog.timestamp.desc())

    if action_filter in AUDIT_ACTIONS:
        query = query.filter(AuditLog.action == action_filter)
    else:
        action_filter = ''

    if table_filter:
        query = query.filter(AuditLog.table_name == table_filter)

    if user_filter:
        query = query.filter(AuditLog.user_id == user_filter)

    if start_time:
        query = query.filter(AuditLog.timestamp >= start_time)

    if end_time:
        query = query.filter(AuditLog.timestamp <= end_time)

    if search_terms:
        like_term = f"%{search_terms}%"
        query = query.filter(or_(
            AuditLog.field_name.ilike(like_term),
            AuditLog.old_value.ilike(like_term),
            AuditLog.new_value.ilike(like_term),
            AuditLog.notes.ilike(like_term),
            AuditLog.table_name.ilike(like_term),
        ))

    offset = (page - 1) * per_page
    rows = query.offset(offset).limit(per_page + 1).all()
    has_next = len(rows) > per_page
    entries = rows[:per_page]

    user_lookup = {}
    user_ids = {entry.user_id for entry in entries if entry.user_id}
    if user_ids:
        users = db_session.query(User).filter(User.user_id.in_(user_ids)).all()
        user_lookup = {user.user_id: user for user in users}

    table_options = [
        value[0]
        for value in db_session.query(AuditLog.table_name)
        .distinct()
        .order_by(AuditLog.table_name.asc())
        .all()
    ]

    user_options = db_session.query(User).order_by(User.username.asc()).all()

    filters = {
        'action': action_filter,
        'table': table_filter,
        'user': user_filter,
        'search': search_terms,
        'start': request.args.get('start', ''),
        'end': request.args.get('end', ''),
    }

    summary = {
        'count': len(entries),
        'page': page,
        'per_page': per_page,
    }

    # Provide a quick breakdown of actions within the current result set
    action_totals = {key: 0 for key in AUDIT_ACTIONS}
    for entry in entries:
        if entry.action in action_totals:
            action_totals[entry.action] += 1

    def build_page_args(page_number: int) -> dict:
        args = {}
        if action_filter:
            args['action'] = action_filter
        if table_filter:
            args['table'] = table_filter
        if user_filter:
            args['user'] = user_filter
        if search_terms:
            args['search'] = search_terms
        if filters['start']:
            args['start'] = filters['start']
        if filters['end']:
            args['end'] = filters['end']
        if per_page != 50:
            args['per_page'] = per_page
        args['page'] = page_number
        return args

    prev_args = build_page_args(page - 1) if page > 1 else None
    next_args = build_page_args(page + 1) if has_next else None

    return render_template(
        'admin/audit_log.html',
        entries=entries,
        user_lookup=user_lookup,
        filters=filters,
        actions=AUDIT_ACTIONS,
        action_totals=action_totals,
        user_options=user_options,
        table_options=table_options,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=page > 1,
        search_terms=search_terms,
        summary=summary,
        prev_args=prev_args,
        next_args=next_args,
    )


@bp.route('/permissions')
@login_required
@admin_required
def permission_scrubbing():
    view = request.args.get('view', 'confidential')

    flags = db_session.query(ConfidentialFieldFlag).order_by(ConfidentialFieldFlag.marked_date.desc()).all()
    confidential_field_count = sum(1 for flag in flags if flag.is_confidential)

    field_entries = []
    for flag in flags:
        if view == 'confidential' and not flag.is_confidential:
            continue
        entity_label, field_name = _resolve_field_display(flag)
        field_entries.append({
            'flag': flag,
            'entity_label': entity_label,
            'field_name': field_name,
        })

    relationship_entries_all = _collect_relationship_entries()
    relationship_confidential = sum(1 for entry in relationship_entries_all if entry['is_confidential'])
    if view == 'confidential':
        relationship_entries = [entry for entry in relationship_entries_all if entry['is_confidential']]
    else:
        relationship_entries = relationship_entries_all

    contact_logs = _collect_confidential_contacts()

    field_form = ConfirmActionForm()
    field_toggle_form = ConfirmActionForm()
    relationship_toggle_form = ConfirmActionForm()
    contact_toggle_form = ConfirmActionForm()

    return render_template(
        'admin/permissions.html',
        field_entries=field_entries,
        relationship_entries=relationship_entries,
        contact_logs=contact_logs,
        confidential_field_count=confidential_field_count,
        relationship_confidential=relationship_confidential,
        view=view,
        field_form=field_form,
        field_toggle_form=field_toggle_form,
        relationship_toggle_form=relationship_toggle_form,
        contact_toggle_form=contact_toggle_form
    )


@bp.route('/permissions/fields/mark', methods=['POST'])
@login_required
@admin_required
def mark_field_permission():
    view_param = request.form.get('view') or request.args.get('view', 'confidential')
    table_name = request.form.get('table_name', '').strip()
    field_name = request.form.get('field_name', '').strip()
    record_id = request.form.get('record_id', type=int)
    value = request.form.get('value', '1') == '1'

    if not table_name or not field_name or record_id is None:
        flash('Provide table name, record ID, and field name.', 'warning')
        return redirect(url_for('admin.permission_scrubbing', view=view_param))

    try:
        mark_field_confidential(table_name, record_id, field_name, value, user_id=current_user.user_id)
        db_session.commit()
        msg = 'Field marked confidential.' if value else 'Field marked public.'
        flash(msg, 'success')
    except Exception as exc:  # pragma: no cover
        db_session.rollback()
        flash(f'Error updating field confidentiality: {exc}', 'danger')

    return redirect(url_for('admin.permission_scrubbing', view=view_param))


@bp.route('/permissions/fields/<int:flag_id>/set', methods=['POST'])
@login_required
@admin_required
def set_field_confidential(flag_id):
    flag = db_session.get(ConfidentialFieldFlag, flag_id)
    if not flag:
        flash('Confidential field flag not found.', 'warning')
        return redirect(url_for('admin.permission_scrubbing'))

    new_state = request.form.get('value', '1') == '1'
    try:
        mark_field_confidential(flag.table_name, flag.record_id, flag.field_name, new_state, user_id=current_user.user_id)
        db_session.commit()
        msg = 'Field marked confidential.' if new_state else 'Field made public.'
        flash(msg, 'success')
    except Exception as exc:  # pragma: no cover
        db_session.rollback()
        flash(f'Error updating field confidentiality: {exc}', 'danger')

    return redirect(url_for('admin.permission_scrubbing', view=request.args.get('view', 'confidential')))


@bp.route('/permissions/relationships/<string:rel_type>/<int:relationship_id>/set', methods=['POST'])
@login_required
@admin_required
def set_relationship_confidential(rel_type, relationship_id):
    rel_type = rel_type.lower()
    config = RELATIONSHIP_CONFIG.get(rel_type)
    if not config:
        flash('Unknown relationship type.', 'warning')
        return redirect(url_for('admin.permission_scrubbing'))

    model, _ = config
    relationship = db_session.get(model, relationship_id)
    if not relationship:
        flash('Relationship not found.', 'warning')
        return redirect(url_for('admin.permission_scrubbing'))

    new_state = request.form.get('value', '1') == '1'
    relationship.is_confidential = new_state
    if hasattr(relationship, 'modified_by'):
        relationship.modified_by = current_user.user_id
    if hasattr(relationship, 'modified_date'):
        relationship.modified_date = datetime.utcnow()
    db_session.commit()

    msg = 'Relationship marked confidential.' if new_state else 'Relationship made public.'
    flash(msg, 'success')
    return redirect(url_for('admin.permission_scrubbing', view=request.args.get('view', 'confidential')))


@bp.route('/permissions/contact-log/<int:contact_id>/set', methods=['POST'])
@login_required
@admin_required
def set_contact_confidential(contact_id):
    log = db_session.get(ContactLog, contact_id)
    if not log:
        flash('Contact log entry not found.', 'warning')
        return redirect(url_for('admin.permission_scrubbing'))

    new_state = request.form.get('value', '1') == '1'
    log.is_confidential = new_state
    log.modified_by = current_user.user_id
    log.modified_date = datetime.utcnow()
    db_session.commit()

    msg = 'Contact log marked confidential.' if new_state else 'Contact log made public.'
    flash(msg, 'success')
    return redirect(url_for('admin.permission_scrubbing', view=request.args.get('view', 'confidential')))


@bp.route('/users')
@login_required
@admin_required
def manage_users():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'all')

    query = db_session.query(User)

    if search:
        like_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(like_term)) |
            (User.email.ilike(like_term)) |
            (User.full_name.ilike(like_term))
        )

    if status == 'active':
        query = query.filter(User.is_active.is_(True))
    elif status == 'inactive':
        query = query.filter(User.is_active.is_(False))

    users = query.order_by(User.username.asc()).all()

    total_users = db_session.query(User).count()
    active_users = db_session.query(User).filter_by(is_active=True).count()
    inactive_users = total_users - active_users

    return render_template(
        'admin/users.html',
        users=users,
        search=search,
        status=status,
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users
    )


@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = CreateUserForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            full_name=form.full_name.data,
            has_confidential_access=form.has_confidential_access.data,
            is_ned_team=form.is_ned_team.data,
            is_admin=form.is_admin.data,
            is_active=form.is_active.data
        )

        try:
            validate_password_strength(form.password.data, username=form.username.data)
        except ValidatorError as exc:
            form.password.errors.append(str(exc))
            return render_template('admin/user_form.html', form=form, title='Add New User')

        user.set_password(form.password.data)
        db_session.add(user)
        db_session.commit()

        flash(f"User '{user.username}' created successfully.", 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/user_form.html', form=form, title='Add New User')


@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = db_session.get(User, user_id)
    if not user:
        flash('User not found.', 'warning')
        return redirect(url_for('admin.manage_users'))

    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        user.email = form.email.data.lower()
        user.full_name = form.full_name.data
        user.has_confidential_access = form.has_confidential_access.data
        user.is_ned_team = form.is_ned_team.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        db_session.commit()

        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/user_form.html', form=form, title=f'Edit User: {user.username}', editing=True, user=user)


@bp.route('/users/<int:user_id>/password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_password(user_id):
    user = db_session.get(User, user_id)
    if not user:
        flash('User not found.', 'warning')
        return redirect(url_for('admin.manage_users'))

    form = AdminChangePasswordForm()

    if form.validate_on_submit():
        try:
            validate_password_strength(form.new_password.data, username=user.username)
        except ValidatorError as exc:
            form.new_password.errors.append(str(exc))
            return render_template('admin/user_password.html', form=form, user=user)

        user.set_password(form.new_password.data)
        db_session.commit()

        flash('Password updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/user_password.html', form=form, user=user)


@bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_user(user_id):
    if current_user.user_id == user_id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.manage_users'))

    user = db_session.get(User, user_id)
    if not user:
        flash('User not found.', 'warning')
        return redirect(url_for('admin.manage_users'))

    user.is_active = False
    db_session.commit()
    flash(f"User '{user.username}' deactivated.", 'success')
    return redirect(url_for('admin.manage_users'))


@bp.route('/users/<int:user_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_user(user_id):
    user = db_session.get(User, user_id)
    if not user:
        flash('User not found.', 'warning')
        return redirect(url_for('admin.manage_users'))

    user.is_active = True
    db_session.commit()
    flash(f"User '{user.username}' reactivated.", 'success')
    return redirect(url_for('admin.manage_users'))


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user_warning(user_id):
    user = db_session.get(User, user_id)
    if user:
        flash('Users cannot be deleted because their activity must be preserved. Deactivate the user instead.', 'warning')
    else:
        flash('User not found.', 'warning')
    return redirect(url_for('admin.manage_users'))


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    section = request.args.get('section', 'company')
    message = None

    if section == 'company':
        form = CompanySettingsForm()
        if request.method == 'GET':
            form.company_name.data = get_system_setting('company_name', 'MPR Associates')
            form.company_logo_path.data = get_system_setting('company_logo_path', '', typed=False)
        if form.validate_on_submit():
            set_system_setting('company_name', form.company_name.data, 'text', user_id=current_user.user_id)
            set_system_setting('company_logo_path', form.company_logo_path.data or '', 'text', user_id=current_user.user_id)
            message = 'Company settings saved.'
    elif section == 'backups':
        form = BackupSettingsForm()
        if request.method == 'GET':
            form.auto_snapshot_enabled.data = bool(get_system_setting('auto_snapshot_enabled', True))
            form.daily_snapshot_time.data = get_system_setting('daily_snapshot_time', '02:00')
            form.snapshot_retention_days.data = int(get_system_setting('snapshot_retention_days', 30))
            form.max_snapshots.data = int(get_system_setting('max_snapshots', 10))
            form.snapshot_dir.data = get_system_setting('snapshot_dir', '', typed=False)
        if form.validate_on_submit():
            set_system_setting('auto_snapshot_enabled', form.auto_snapshot_enabled.data, 'boolean', current_user.user_id)
            set_system_setting('daily_snapshot_time', form.daily_snapshot_time.data, 'text', current_user.user_id)
            set_system_setting('snapshot_retention_days', form.snapshot_retention_days.data, 'integer', current_user.user_id)
            set_system_setting('max_snapshots', form.max_snapshots.data, 'integer', current_user.user_id)
            if form.snapshot_dir.data is not None:
                set_system_setting('snapshot_dir', form.snapshot_dir.data, 'text', current_user.user_id)
            message = 'Backup settings saved.'
    elif section == 'crm':
        form = CrmSettingsForm()
        if request.method == 'GET':
            form.roundtable_history_limit.data = int(get_roundtable_history_limit())
        if form.validate_on_submit():
            set_system_setting('roundtable_history_limit', form.roundtable_history_limit.data, 'integer', current_user.user_id)
            message = 'CRM settings saved.'
    else:
        section = 'company'
        form = CompanySettingsForm()
        if request.method == 'GET':
            form.company_name.data = get_system_setting('company_name', 'MPR Associates')
            form.company_logo_path.data = get_system_setting('company_logo_path', '', typed=False)

    if request.method == 'POST' and form.validate_on_submit() and message:
        flash(message, 'success')
        return redirect(url_for('admin.system_settings', section=section))

    return render_template('admin/settings.html', section=section, form=form)
