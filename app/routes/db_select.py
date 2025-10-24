"""
Database Selection Routes
Allows users to select which SQLite database file to use
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import current_user, login_required
from app.utils import db_selector_cache, db_helpers
from flask import current_app
from app.utils.migrations import get_current_schema_version, get_required_schema_version, check_and_apply_migrations
import logging
import json
import ctypes
import string

bp = Blueprint('db_select', __name__, url_prefix='')
logger = logging.getLogger(__name__)


@bp.route('/select-db', methods=['GET'])
@login_required
def select_database():
    """
    Show database selector page
    Displays scanned databases and allows browsing
    """
    # Get scanned databases from databases/ directory
    scanned_databases = db_helpers.scan_databases_directory()

    # Get recent paths from cache
    recent_paths = db_selector_cache.get_recent_paths()

    # Get last browsed directory
    last_browsed_dir = db_selector_cache.get_last_browsed_dir()

    # Get current selection if any (do not fall back to app default)
    current_selection = session.get('selected_db_path')
    if not current_selection:
        from flask import g
        if hasattr(g, 'selected_db_path') and g.selected_db_path:
            current_selection = g.selected_db_path
    
    # Database info gathering removed - only showing path and filename now

    # Get suggested default (user preference or global default)
    suggested_default = None
    if current_user.is_authenticated and current_user.last_db_path:
        if os.path.exists(current_user.last_db_path):
            suggested_default = current_user.last_db_path

    if not suggested_default:
        global_default = db_selector_cache.get_global_default_path()
        if global_default and os.path.exists(global_default):
            suggested_default = global_default

    # Build recent databases list with display names
    recent_databases = []
    for path in recent_paths:
        if os.path.exists(path):
            display_name = db_helpers.get_db_display_name(path)
            if not display_name:
                display_name = os.path.basename(os.path.dirname(path))
            recent_databases.append({
                'path': path,
                'display_name': display_name
            })

    return render_template(
        'db_select/select.html',
        scanned_databases=scanned_databases,
        recent_databases=recent_databases,
        last_browsed_dir=last_browsed_dir,
        current_selection=current_selection,
        suggested_default=suggested_default
    )


@bp.route('/select-db', methods=['POST'])
def select_database_post():
    """
    Process database selection
    Validates, checks schema, and optionally runs migrations
    """
    db_path = request.form.get('db_path', '').strip()
    custom_name = request.form.get('custom_name', '').strip()
    apply_migration = request.form.get('apply_migration') == 'yes'

    # DEBUG: Log database selection attempt
    logger.info(f"[DEBUG DB_SELECT] Database selection POST request")
    logger.info(f"[DEBUG DB_SELECT] Requested DB path: {db_path}")
    logger.info(f"[DEBUG DB_SELECT] Custom name: {custom_name}")

    if not db_path:
        logger.warning(f"[DEBUG DB_SELECT] No database path provided")
        flash('Please select or enter a database path', 'warning')
        return redirect(url_for('db_select.select_database'))

    # Normalize path
    db_path = os.path.abspath(db_path)
    logger.info(f"[DEBUG DB_SELECT] Normalized path: {db_path}")
    logger.info(f"[DEBUG DB_SELECT] Path exists: {os.path.exists(db_path)}")

    # Validate database file
    logger.info(f"[DEBUG DB_SELECT] Validating database file...")
    validation = db_helpers.validate_database_file(db_path)
    logger.info(f"[DEBUG DB_SELECT] Validation result: valid={validation.get('valid')}, error={validation.get('error')}")

    if not validation['valid']:
        flash(f"Invalid database: {validation['error']}", 'danger')
        return redirect(url_for('db_select.select_database'))

    # Check schema version
    current_version = validation['schema_version']
    required_version = get_required_schema_version()

    logger.info(f"Database {db_path} has schema version {current_version}, required is {required_version}")

    # Handle migration if needed
    if current_version < required_version:
        # Migration required
        if not current_user.is_authenticated or not current_user.is_admin:
            flash(
                f'This database requires migration (v{current_version} → v{required_version}). '
                'Only administrators can migrate databases. Please contact an administrator.',
                'danger'
            )
            return redirect(url_for('db_select.select_database'))

        # Admin user - check if they want to apply migration
        if not apply_migration:
            # Show migration prompt
            pending_count = required_version - current_version
            return render_template(
                'db_select/migration_prompt.html',
                db_path=db_path,
                current_version=current_version,
                required_version=required_version,
                pending_count=pending_count,
                custom_name=custom_name
            )

        # Apply migrations
        try:
            success = check_and_apply_migrations(db_path, interactive=False)
            if not success:
                flash('Migration failed. Please check logs for details.', 'danger')
                return redirect(url_for('db_select.select_database'))

            flash(f'Database migrated successfully from v{current_version} to v{required_version}', 'success')

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            flash(f'Migration failed: {str(e)}', 'danger')
            return redirect(url_for('db_select.select_database'))

    elif current_version > required_version:
        flash(
            f'This database (v{current_version}) is newer than this application version (v{required_version}). '
            'Please update the application.',
            'danger'
        )
        return redirect(url_for('db_select.select_database'))

    # Database is valid and ready to use
    # Set custom display name if provided
    if custom_name:
        db_helpers.set_db_display_name(db_path, custom_name)

    # Update session
    logger.info(f"[DEBUG DB_SELECT] Setting session['selected_db_path'] = {db_path}")
    session['selected_db_path'] = db_path
    session.permanent = True
    logger.info(f"[DEBUG DB_SELECT] Session updated. Confirmed session value: {session.get('selected_db_path')}")

    # Update cache
    db_selector_cache.add_recent_path(db_path)
    db_selector_cache.set_global_default_path(db_path)

    # Update browsed directory
    parent_dir = os.path.dirname(db_path)
    db_selector_cache.set_last_browsed_dir(parent_dir)

    # Update user preference if authenticated
    if current_user.is_authenticated:
        # Import here to avoid circular dependency
        from app import db_session

        display_name = custom_name or db_helpers.get_db_display_name(db_path)
        current_user.last_db_path = db_path
        current_user.last_db_display_name = display_name

        try:
            db_session.commit()
        except Exception as e:
            logger.error(f"Failed to update user preference: {e}")

    display_name = db_helpers.get_db_display_name(db_path) or os.path.basename(os.path.dirname(db_path))
    flash(f'Database "{display_name}" selected successfully', 'success')

    # Redirect appropriately
    if current_user.is_authenticated:
        # Go to dashboard
        return redirect(url_for('dashboard.index'))
    else:
        # Go to login
        return redirect(url_for('auth.login'))


@bp.route('/select-db/refresh', methods=['POST'])
def refresh_database_list():
    """
    Refresh the database list and return to selector
    """
    flash('Database list refreshed', 'info')
    return redirect(url_for('db_select.select_database'))


@bp.route('/select-db/mapped-drives', methods=['GET'])
def mapped_drives():
    """Return a JSON list of mapped drives and their UNC roots (Windows only).

    This is best-effort: returns drive letter and root path if available.
    """
    drives = []
    if os.name == 'nt':
        # Use GetLogicalDrives and GetDriveType / QueryDosDevice via ctypes
        kernel32 = ctypes.windll.kernel32
        bitmask = kernel32.GetLogicalDrives()
        for i in range(26):
            if bitmask & (1 << i):
                letter = f"{string.ascii_uppercase[i]}:"
                root = f"{letter}\\"
                # Try to resolve to a UNC path using QueryDosDevice
                target_buf = ctypes.create_string_buffer(1024)
                res = kernel32.QueryDosDeviceA(letter.encode('ascii'), target_buf, ctypes.sizeof(target_buf))
                unc = None
                if res:
                    target = target_buf.value.decode('utf-8', errors='ignore')
                    unc = target
                drives.append({'letter': letter, 'root': root, 'target': unc})
    else:
        # Non-windows: list mountpoints from /mnt, /media as a fallback
        mounts = []
        for base in ['/mnt', '/media']:
            if os.path.exists(base):
                for p in os.listdir(base):
                    mounts.append({'letter': '', 'root': os.path.join(base, p), 'target': ''})
        drives = mounts

    return current_app.response_class(json.dumps(drives), mimetype='application/json')


@bp.route('/api/mapped-drives', methods=['GET'])
def api_mapped_drives():
    """Compatibility API endpoint for mapped drives (JSON) placed under /api to avoid DB-selector middleware redirects."""
    # Reuse the same logic as mapped_drives
    drives = []
    if os.name == 'nt':
        kernel32 = ctypes.windll.kernel32
        bitmask = kernel32.GetLogicalDrives()
        for i in range(26):
            if bitmask & (1 << i):
                letter = f"{string.ascii_uppercase[i]}:"
                root = f"{letter}\\"
                target_buf = ctypes.create_string_buffer(1024)
                res = kernel32.QueryDosDeviceA(letter.encode('ascii'), target_buf, ctypes.sizeof(target_buf))
                unc = None
                if res:
                    target = target_buf.value.decode('utf-8', errors='ignore')
                    unc = target
                drives.append({'letter': letter, 'root': root, 'target': unc})
    else:
        mounts = []
        for base in ['/mnt', '/media']:
            if os.path.exists(base):
                for p in os.listdir(base):
                    mounts.append({'letter': '', 'root': os.path.join(base, p), 'target': ''})
        drives = mounts

    return current_app.response_class(json.dumps(drives), mimetype='application/json')


@bp.route('/api/list-files', methods=['GET'])
def api_list_files():
    """List directories and files for a given root path.

    Query params:
      root - required, a drive root like 'Q:\\'
      path - optional, relative path under the root

    Returns JSON: {cwd: <absolute>, entries: [{name, is_dir, size, path}]}
    """
    root = request.args.get('root')
    rel = request.args.get('path', '')

    if not root:
        return current_app.response_class(json.dumps({'error': 'root is required'}), status=400, mimetype='application/json')

    # Normalize and ensure root ends with backslash on Windows
    if os.name == 'nt':
        if not root.endswith('\\'):
            root = root + '\\'
    else:
        # for non-windows treat root as absolute path
        pass

    # Build absolute path and ensure it is under the root
    requested = os.path.normpath(os.path.join(root, rel))

    try:
        # Prevent escaping root
        if not os.path.commonpath([os.path.abspath(requested), os.path.abspath(root)]) == os.path.abspath(root):
            return current_app.response_class(json.dumps({'error': 'path outside root'}), status=400, mimetype='application/json')

        entries = []
        if os.path.isdir(requested):
            for name in sorted(os.listdir(requested)):
                full = os.path.join(requested, name)
                try:
                    is_dir = os.path.isdir(full)
                    size = os.path.getsize(full) if not is_dir else None
                except Exception:
                    is_dir = False
                    size = None
                entries.append({'name': name, 'is_dir': is_dir, 'size': size, 'path': os.path.relpath(full, root)})
        else:
            return current_app.response_class(json.dumps({'error': 'not a directory'}), status=400, mimetype='application/json')

        return current_app.response_class(json.dumps({'cwd': os.path.relpath(requested, root), 'entries': entries}), mimetype='application/json')

    except Exception as e:
        return current_app.response_class(json.dumps({'error': str(e)}), status=500, mimetype='application/json')


@bp.route('/select-db/db-info', methods=['GET'])
def select_db_info():
    """Temporary debug endpoint: return info about the currently-selected DB path.

    Returns JSON with keys: selected_db_path, exists, size, integrity, tables, counts
    """
    sel = session.get('selected_db_path')
    info = {'selected_db_path': sel}

    if not sel:
        return current_app.response_class(json.dumps({'error': 'no selected_db_path in session', 'info': info}), status=400, mimetype='application/json')

    try:
        exists = os.path.exists(sel)
        info['exists'] = exists
        if exists:
            try:
                info['size'] = os.path.getsize(sel)
            except Exception:
                info['size'] = None

            # Try opening SQLite and gathering basic metadata
            import sqlite3
            try:
                conn = sqlite3.connect(sel, timeout=5.0)
                cur = conn.cursor()
                try:
                    cur.execute('PRAGMA integrity_check')
                    info['integrity'] = cur.fetchone()
                except Exception as e:
                    info['integrity_error'] = str(e)

                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cur.fetchall()]
                info['tables'] = tables

                for t in ['projects', 'companies', 'users', 'system_settings']:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {t}")
                        info[f'{t}_count'] = cur.fetchone()[0]
                    except Exception as e:
                        info[f'{t}_count_error'] = str(e)

                conn.close()
            except Exception as e:
                info['sqlite_open_error'] = str(e)
        else:
            info['size'] = None

        return current_app.response_class(json.dumps(info), mimetype='application/json')

    except Exception as e:
        return current_app.response_class(json.dumps({'error': str(e)}), status=500, mimetype='application/json')


@bp.route('/api/db-info', methods=['GET'])
def api_db_info():
    """API: return metadata for an arbitrary database path provided as `path` query param.

    Example: /api/db-info?path=Q:\\some\\dir\\nukeworks.sqlite
    This does not depend on session and is intended for debugging.
    """
    p = request.args.get('path')
    if not p:
        return current_app.response_class(json.dumps({'error': 'path param is required'}), status=400, mimetype='application/json')

    info = {'queried_path': p}
    try:
        exists = os.path.exists(p)
        info['exists'] = exists
        if exists:
            try:
                info['size'] = os.path.getsize(p)
            except Exception:
                info['size'] = None

            # SQLite metadata
            import sqlite3
            try:
                conn = sqlite3.connect(p, timeout=5.0)
                cur = conn.cursor()
                try:
                    cur.execute('PRAGMA integrity_check')
                    info['integrity'] = cur.fetchone()
                except Exception as e:
                    info['integrity_error'] = str(e)

                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cur.fetchall()]
                info['tables'] = tables

                for t in ['projects', 'companies', 'users', 'system_settings']:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {t}")
                        info[f'{t}_count'] = cur.fetchone()[0]
                    except Exception as e:
                        info[f'{t}_count_error'] = str(e)

                conn.close()
            except Exception as e:
                info['sqlite_open_error'] = str(e)
        else:
            info['size'] = None

        return current_app.response_class(json.dumps(info), mimetype='application/json')

    except Exception as e:
        return current_app.response_class(json.dumps({'error': str(e)}), status=500, mimetype='application/json')


@bp.route('/alive', methods=['GET'])
def alive():
    """Return server process info and mtime of db_select.py to help verify which code the running server loaded."""
    try:
        import time

        pid = os.getpid()
        file_path = os.path.join(os.path.dirname(__file__), 'db_select.py')
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            mtime_iso = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        else:
            mtime_iso = None

        return current_app.response_class(json.dumps({'pid': pid, 'file': file_path, 'file_mtime': mtime_iso}), mimetype='application/json')
    except Exception as e:
        return current_app.response_class(json.dumps({'error': str(e)}), status=500, mimetype='application/json')
