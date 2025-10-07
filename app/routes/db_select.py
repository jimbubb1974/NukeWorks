"""
Database Selection Routes
Allows users to select which SQLite database file to use
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import current_user
from app.utils import db_selector_cache, db_helpers
from app.utils.migrations import get_current_schema_version, get_required_schema_version, check_and_apply_migrations
import logging

bp = Blueprint('db_select', __name__, url_prefix='')
logger = logging.getLogger(__name__)


@bp.route('/select-db', methods=['GET'])
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

    # Get current selection if any
    current_selection = session.get('selected_db_path')

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

    if not db_path:
        flash('Please select or enter a database path', 'warning')
        return redirect(url_for('db_select.select_database'))

    # Normalize path
    db_path = os.path.abspath(db_path)

    # Validate database file
    validation = db_helpers.validate_database_file(db_path)

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
    session['selected_db_path'] = db_path
    session.permanent = True

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
