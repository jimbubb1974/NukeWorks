"""
Authentication routes (login, logout, password management)
"""
import os
import sys
from pathlib import Path
from typing import Optional
from flask import Blueprint, render_template, redirect, url_for, flash, request, session as flask_session, g
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.forms.auth import LoginForm, ChangePasswordForm
from app import db_session
import logging


def _app_root() -> Path:
    """Return the application root directory.

    In a PyInstaller bundle the root is the folder containing the executable
    (i.e. the unzipped portable directory or the install location).
    In development it is the repository root (two levels above this file).
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]

bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)


def _is_lock_error(exc) -> bool:
    """True if an exception looks like a SQLite 'database is locked' error."""
    return 'database is locked' in str(exc).lower()


def _describe_other_holder(db_path: str) -> Optional[str]:
    """Best-effort human description of who else may hold this database open."""
    try:
        from app.utils.instance_lock import check_lock
        status = check_lock(db_path)
    except Exception:
        return None

    info = status.get('info')
    if not status.get('locked') or not info:
        return None

    host = info.get('hostname', 'another machine')
    if status.get('same_host'):
        return f"NukeWorks also appears to be running on this computer (PID {info.get('pid')})."
    return f"NukeWorks also appears to be open on another computer ({host})."


def _build_db_choices():
    """Return (choices, default_path) for the login database dropdown.

    Only surfaces top-level databases — skips backups/ and snapshots/ subdirs.
    Falls back to the filename stem when display names are missing or duplicated
    across multiple files.
    """
    from pathlib import Path
    from app.utils.db_helpers import get_db_display_name
    from app.utils.db_selector_cache import get_recent_paths, get_global_default_path

    SKIP_DIRS = {'backups', 'backup', 'snapshots', 'snapshot'}

    def _excluded(path):
        return any(p.lower() in SKIP_DIRS for p in Path(path).parts)

    seen = set()
    raw = []  # [(abs_path, raw_display_name)]

    # Scan databases/ directory — top-level files + one level of named subdirs,
    # skipping backup/snapshot folders entirely.
    databases_dir = _app_root() / 'databases'
    if databases_dir.exists():
        for entry in sorted(databases_dir.iterdir()):
            if entry.is_file() and entry.suffix.lower() == '.sqlite':
                p = str(entry.resolve())
                if p not in seen:
                    seen.add(p)
                    raw.append((p, get_db_display_name(p) or ''))
            elif entry.is_dir() and entry.name.lower() not in SKIP_DIRS:
                for f in sorted(entry.iterdir()):
                    if f.is_file() and f.suffix.lower() == '.sqlite':
                        p = str(f.resolve())
                        if p not in seen:
                            seen.add(p)
                            raw.append((p, get_db_display_name(p) or ''))

    # Include recently-used paths not already listed
    for path in get_recent_paths():
        p = os.path.abspath(path)
        if p not in seen and os.path.exists(p) and not _excluded(p):
            seen.add(p)
            raw.append((p, get_db_display_name(p) or ''))

    # Deduplicate display names — when a name appears more than once, append
    # the filename stem so the user can tell entries apart.
    name_freq: dict = {}
    for _, name in raw:
        key = name.strip().lower()
        name_freq[key] = name_freq.get(key, 0) + 1

    choices = []
    for path, name in raw:
        label = name.strip()
        if not label or name_freq.get(label.lower(), 0) > 1:
            stem = Path(path).stem
            parent = Path(path).parent
            if parent.resolve() != databases_dir.resolve():
                label = f"{stem} ({parent.name})"
            else:
                label = stem
        choices.append((path, label))

    default = get_global_default_path()
    if default:
        default = os.path.abspath(default)
    if not default and choices:
        default = choices[0][0]
    return choices, default


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login with integrated database selection."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    db_choices, default_db = _build_db_choices()

    # Compute the app's databases directory to expose as a browser shortcut
    databases_dir = str((_app_root() / 'databases').resolve())

    def _render(**kwargs):
        return render_template(
            'auth/login.html',
            form=form,
            single_db=len(db_choices) == 1,
            databases_dir=databases_dir,
            **kwargs
        )

    form = LoginForm()

    # A manual path submitted from the file browser overrides the dropdown.
    # Add it to choices before validation so WTForms accepts it.
    manual_path = request.form.get('manual_db_path', '').strip()
    if manual_path:
        manual_abs = os.path.abspath(manual_path)
        if not any(p == manual_abs for p, _ in db_choices):
            db_choices = db_choices + [(manual_abs, os.path.basename(manual_abs))]
        form.db_path.data = manual_abs

    form.db_path.choices = db_choices

    # Pre-select the default on GET
    if request.method == 'GET' and default_db:
        form.db_path.data = default_db

    # "Force Unlock & Retry" button posts here with this flag set, asking us
    # to clear this process's own cached engine/connection for the chosen
    # database before retrying — see _render(locked_db_path=...) below.
    force_unlock = request.form.get('force_unlock') == '1'

    if form.validate_on_submit():
        db_path = os.path.abspath(form.db_path.data)

        if force_unlock:
            from app import dispose_engine
            from app.utils.instance_lock import force_clear_lock
            dispose_engine(db_path)
            force_clear_lock(db_path)
            logger.warning(f'User requested force-unlock for database: {db_path}')
            flash('Cleared this app\'s connection to the database. Retrying…', 'info')

        from app.utils.db_helpers import validate_database_file
        from app.utils.migrations import get_required_schema_version
        validation = validate_database_file(db_path)
        if not validation['valid']:
            locked = 'database is locked' in str(validation.get('error') or '').lower()
            flash(f'Database error: {validation["error"]}', 'danger')
            if locked:
                return _render(locked_db_path=db_path, lock_owner=_describe_other_holder(db_path))
            return _render()

        if validation['schema_version'] < get_required_schema_version():
            flash('This database needs to be updated before it can be used. An administrator can update it from "Database settings" below.', 'danger')
            return _render()

        # Single-instance guard: if another live process on *this* machine
        # already has this database open, don't even attempt to open a
        # second connection — that's the scenario most likely to leave
        # SQLite's WAL/journal in a locked state. Cross-machine locks (e.g.
        # a colleague using a shared network database) are only noted as
        # informational, since the app is designed to support that.
        if not force_unlock:
            try:
                from app.utils.instance_lock import check_lock
                lock_status = check_lock(db_path)
            except Exception:
                lock_status = {'locked': False}

            if lock_status.get('locked') and lock_status.get('same_host'):
                flash('This database is already open in another NukeWorks window on this computer.', 'danger')
                return _render(locked_db_path=db_path, lock_owner=_describe_other_holder(db_path))

        from app import get_or_create_engine_session
        try:
            _, db_sess = get_or_create_engine_session(db_path)
            g.db_session = db_sess
        except Exception as e:
            logger.error(f'Failed to open database {db_path}: {e}')
            if _is_lock_error(e):
                flash('Could not open the selected database because it is locked.', 'danger')
                return _render(locked_db_path=db_path, lock_owner=_describe_other_holder(db_path))
            flash('Could not open the selected database. Please try again.', 'danger')
            return _render()

        username = form.username.data
        try:
            user = db_session.query(User).filter_by(username=username).first()
        except Exception as e:
            logger.error(f'User query failed: {e}')
            if _is_lock_error(e):
                flash('Database error while authenticating: the database is locked.', 'danger')
                return _render(locked_db_path=db_path, lock_owner=_describe_other_holder(db_path))
            flash('Database error while authenticating. Please try again.', 'danger')
            return _render()

        if user is None or not user.check_password(form.password.data):
            logger.warning(f'Failed login for {username!r} from {request.remote_addr}')
            flash('Invalid username or password', 'danger')
            return _render()

        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return _render()

        flask_session['selected_db_path'] = db_path
        flask_session.permanent = True

        from app.utils.db_selector_cache import add_recent_path, set_global_default_path
        add_recent_path(db_path)
        set_global_default_path(db_path)

        user.last_db_path = db_path
        user.update_last_login()
        db_session.commit()

        login_user(user, remember=form.remember_me.data)
        logger.info(f'User {username} logged in from {request.remote_addr}')
        flash(f'Welcome back, {user.full_name or user.username}!', 'success')
        return redirect(url_for('dashboard.index'))

    return _render()


@bp.route('/logout')
@login_required
def logout():
    """User logout with security logging"""
    username = current_user.username
    logger.info(f'User {username} logged out from IP: {request.remote_addr}')
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change current user's password"""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('auth.change_password'))

        # Update password
        current_user.set_password(form.new_password.data)
        db_session.commit()

        logger.info(f'User {current_user.username} changed their password')
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/change_password.html', form=form)


@bp.route('/profile')
@login_required
def profile():
    """View user profile"""
    return render_template('auth/profile.html', user=current_user)
