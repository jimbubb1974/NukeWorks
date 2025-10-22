"""
NukeWorks Flask Application Factory
"""
import os
import shutil
from pathlib import Path
from flask import Flask, g, session
from flask_login import LoginManager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.local import LocalProxy
from config import get_config, _resource_path
from pathlib import Path
from jinja2 import ChoiceLoader, FileSystemLoader, TemplateNotFound
from jinja2.loaders import BaseLoader
import logging

logger = logging.getLogger(__name__)


class PersistentFileSystemLoader(BaseLoader):
    """
    A Jinja2 loader that wraps FileSystemLoader and persists across requests.
    Ensures templates bundled in PyInstaller are always found.
    """
    def __init__(self, searchpath):
        self.fs_loader = FileSystemLoader(searchpath)

    def get_source(self, environment, template):
        try:
            return self.fs_loader.get_source(environment, template)
        except TemplateNotFound:
            raise TemplateNotFound(template)

    def list_templates(self):
        return self.fs_loader.list_templates()

# Global objects
login_manager = LoginManager()
db_session = None  # Will be replaced with LocalProxy after create_app
_engine_cache = {}  # Cache of {absolute_db_path: (engine, scoped_session)}
_default_db_session = None  # Fallback for initial setup


def create_app(config_name=None):
    """
    Create and configure Flask application

    Args:
        config_name: Configuration environment name (development, production, testing)

    Returns:
        Configured Flask application
    """
    # Resolve template/static folders so they work when bundled with PyInstaller
    template_dir = _resource_path('app/templates')
    static_dir = _resource_path('app/static')

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )

    # Visible startup diagnostics for template resolution (stdout)
    try:
        login_rel_path = Path('auth') / 'login.html'
        print(f"[Templates] template_dir={template_dir} exists={Path(template_dir).exists()} login_exists={(Path(template_dir)/login_rel_path).exists()}")
        print(f"[Templates] static_dir={static_dir} exists={Path(static_dir).exists()}")
    except Exception:
        pass

    # Prepare template search paths; we'll attach them after blueprints register
    def _compute_template_paths():
        base = str(template_dir)
        return [base, str(Path(base) / 'auth')]

    # Debug: Log template search paths and presence of key templates
    try:
        login_rel = Path('auth') / 'login.html'
        paths_to_check = unique_paths
        logger.info("Planned Jinja template search paths:")
        for p in paths_to_check:
            exists = Path(p).joinpath(login_rel).exists()
            logger.info(" - %s (login.html=%s)", p, 'yes' if exists else 'no')
    except Exception:
        pass

    # After registering blueprints (which sets DispatchingJinjaLoader), extend
    # the environment loader to also look in our explicit filesystem paths.
    def _attach_template_paths():
        try:
            paths = _compute_template_paths()
            app.jinja_env.loader = ChoiceLoader([app.jinja_env.loader, FileSystemLoader(paths)])
            # Diagnostics
            try:
                loader = app.jinja_env.loader
                searchpath = getattr(loader, 'searchpath', None)
                print(f"[JinjaLoader] type={type(loader).__name__} searchpath={searchpath}")
                with app.app_context():
                    try:
                        _ = app.jinja_env.get_template('auth/login.html')
                        print("[JinjaCheck] auth/login.html resolved OK")
                    except Exception as exc:
                        print(f"[JinjaCheck] Failed to resolve auth/login.html: {exc}")
            except Exception:
                pass
        except Exception:
            pass

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Ensure required directories exist in writable storage
    storage_paths = [
        Path(app.config['SESSION_FILE_DIR']),
        Path(app.config['UPLOAD_FOLDER']),
        Path(app.config['SNAPSHOT_DIR']),
        Path(app.config['LOG_FILE']).parent,
    ]
    for storage_path in storage_paths:
        storage_path.mkdir(parents=True, exist_ok=True)

    # Initialize database
    init_db(app)

    # Initialize Flask-Login
    init_login_manager(app)

    # Register blueprints
    register_blueprints(app)
    # Attach template paths now that loaders are initialized by blueprints
    # Force a custom PersistentFileSystemLoader that stays set across requests
    # This must be done AFTER blueprints are registered but BEFORE request handlers
    try:
        persistent_loader = PersistentFileSystemLoader([str(template_dir)])
        app.jinja_env.loader = persistent_loader
        print(f"[JinjaLoader] Using PersistentFileSystemLoader -> {template_dir}")

        # Test template resolution in app context
        with app.app_context():
            try:
                tmpl = app.jinja_env.get_template('auth/login.html')
                print("[JinjaCheck] auth/login.html resolved OK")
            except Exception as exc:
                print(f"[JinjaCheck] Failed to resolve auth/login.html: {exc}")
                raise  # Don't suppress - this is critical
    except Exception as exc:
        print(f"[JinjaLoader] ERROR: Failed to set template loader: {exc}")
        import traceback
        traceback.print_exc()
        raise SystemExit("Template loader initialization failed - cannot continue")

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_commands(app)

    # Register template filters
    register_template_filters(app)

    # Register before_request handler for database selection
    register_db_selector_middleware(app)

    # Note: Automated snapshot scheduler is DISABLED for per-DB selection feature
    # Only manual snapshots are supported

    # Context processors
    @app.context_processor
    def inject_template_helpers():
        """Expose commonly used helpers and user context to templates."""
        from flask import current_app
        from flask_login import current_user

        def has_endpoint(endpoint_name: str) -> bool:
            """Return True if the application has a registered endpoint."""
            if not current_app:
                return False
            return any(rule.endpoint == endpoint_name for rule in current_app.url_map.iter_rules())

        return dict(current_user=current_user, has_endpoint=has_endpoint)

    return app


def get_or_create_engine_session(db_path, app=None):
    """
    Get or create engine and scoped_session for a database path
    Uses cache to avoid recreating engines

    Args:
        db_path: Absolute path to database file
        app: Flask application (for config)

    Returns:
        tuple: (engine, scoped_session)
    """
    global _engine_cache

    abs_path = os.path.abspath(db_path)

    # Return cached if exists
    if abs_path in _engine_cache:
        return _engine_cache[abs_path]

    # Get config from app or use defaults
    if app:
        engine_options = app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})
        echo = app.config.get('SQLALCHEMY_ECHO', False)
        timeout = int(engine_options.get('connect_args', {}).get('timeout', 30) * 1000)
    else:
        engine_options = {
            'connect_args': {'timeout': 30.0, 'check_same_thread': False},
            'pool_pre_ping': True
        }
        echo = False
        timeout = 30000

    # Create engine
    engine = create_engine(
        f'sqlite:///{abs_path}',
        **engine_options,
        echo=echo
    )

    # Set SQLite pragmas
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite PRAGMAs for optimization"""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute(f"PRAGMA busy_timeout={timeout}")
        cursor.close()

    # Create scoped session
    session_factory = sessionmaker(bind=engine)
    scoped_sess = scoped_session(session_factory)

    # Cache it
    _engine_cache[abs_path] = (engine, scoped_sess)

    logger.info(f"Created new engine for database: {abs_path}")

    return engine, scoped_sess


def dispose_engine(db_path):
    """
    Dispose engine for a specific database path
    Releases file locks and frees memory

    Args:
        db_path: Absolute path to database file

    Returns:
        bool: True if disposed, False if not found
    """
    global _engine_cache

    abs_path = os.path.abspath(db_path)

    if abs_path in _engine_cache:
        engine, scoped_sess = _engine_cache[abs_path]
        scoped_sess.remove()
        engine.dispose()
        del _engine_cache[abs_path]
        logger.info(f"Disposed engine for database: {abs_path}")
        return True

    return False


def get_engine_cache_info():
    """
    Get information about cached engines

    Returns:
        dict: {db_path: {'engine': engine, 'session': scoped_session}}
    """
    return {path: {'engine': eng, 'session': sess} for path, (eng, sess) in _engine_cache.items()}


def get_db_session():
    """
    Get database session for current request
    Returns per-session DB if selected, otherwise default

    Returns:
        scoped_session: Database session
    """
    # Check if request context has a specific DB session
    if hasattr(g, 'db_session') and g.db_session is not None:
        return g.db_session

    # Fall back to default
    global _default_db_session
    return _default_db_session


def init_db(app):
    """
    Initialize database connection with SQLite optimizations

    Args:
        app: Flask application
    """
    global db_session, _default_db_session

    # Create default engine and session (for initial setup)
    db_path = app.config['DATABASE_PATH']
    template_path = app.config.get('DEFAULT_DB_TEMPLATE')

    if (
        template_path
        and isinstance(template_path, str)
        and template_path
        and db_path
        and db_path != ':memory:'
    ):
        target_path = Path(db_path).expanduser()
        template_file = Path(template_path)

        if not target_path.exists() and template_file.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template_file, target_path)

        app.config['DATABASE_PATH'] = str(target_path)
        db_path = app.config['DATABASE_PATH']

    engine, default_session = get_or_create_engine_session(db_path, app)

    _default_db_session = default_session

    # Attach audit logging listeners before the session is used
    from app.services.audit import init_audit_logging
    init_audit_logging(default_session)

    # Import models to register them
    from app import models

    # Create all tables if they don't exist
    models.Base.metadata.create_all(engine)
    _ensure_product_columns(engine)

    # Store default db_session in app for easy access
    app.db_session = default_session

    # Replace global db_session with LocalProxy
    db_session = LocalProxy(get_db_session)

    # Teardown context
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Remove database session at the end of request"""
        # Remove per-request session if it exists
        if hasattr(g, 'db_session') and g.db_session is not None:
            g.db_session.remove()
        # Also remove default session
        _default_db_session.remove()


def _ensure_product_columns(engine):
    """Ensure extended product columns exist (safe for repeated runs)."""
    product_columns = {
        'generation': 'TEXT',
        'gross_capacity_mwt': 'REAL',
        'fuel_type': 'TEXT',
        'fuel_enrichment': 'TEXT',
        'mpr_project_ids': 'TEXT',
    }

    with engine.begin() as connection:
        # Check if products table exists
        table_check = connection.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
        )).fetchone()
        
        if table_check:
            existing = {row[1] for row in connection.execute(text('PRAGMA table_info(products)'))}
            for column, ddl in product_columns.items():
                if column not in existing:
                    connection.execute(text(f"ALTER TABLE products ADD COLUMN {column} {ddl}"))

        # Check if projects table exists
        table_check = connection.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
        )).fetchone()
        
        if table_check:
            project_columns = {
                'target_cod': 'DATE',
            }

            existing_project = {row[1] for row in connection.execute(text('PRAGMA table_info(projects)'))}
            for column, ddl in project_columns.items():
                if column not in existing_project:
                    connection.execute(text(f"ALTER TABLE projects ADD COLUMN {column} {ddl}"))


def init_login_manager(app):
    """
    Initialize Flask-Login

    Args:
        app: Flask application
    """
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login"""
        from app.models import User
        return db_session.query(User).get(int(user_id))


def register_blueprints(app):
    """
    Register Flask blueprints

    Args:
        app: Flask application
    """
    from app.routes import auth, dashboard, projects, companies, crm, reports, admin, contact_log, network, personnel, db_select

    app.register_blueprint(db_select.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(companies.bp)
    app.register_blueprint(crm.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(contact_log.bp)
    app.register_blueprint(network.bp)
    app.register_blueprint(personnel.bp)

    # Legacy blueprints removed in Phase 4 cleanup (2025-10-10):
    # - operators, constructors, offtakers, technologies (use /companies?role=X instead)
    # - clients (use /companies with is_mpr_client filter instead)


def register_error_handlers(app):
    """
    Register error handlers

    Args:
        app: Flask application
    """
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        db_session.rollback()
        return render_template('errors/500.html'), 500


def register_commands(app):
    """
    Register CLI commands

    Args:
        app: Flask application
    """
    import click

    @app.cli.command()
    def init_db_cmd():
        """Initialize the database with sample data"""
        click.echo('Initializing database...')
        from app.utils.db_init import init_database
        init_database(app.db_session)
        click.echo('Database initialized successfully!')

    @app.cli.command()
    @click.option('--username', prompt=True)
    @click.option('--email', prompt=True)
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, email, password):
        """Create an admin user"""
        from app.models import User

        user = User(
            username=username,
            email=email,
            full_name='Administrator',
            is_admin=True,
            has_confidential_access=True,
            is_ned_team=True,
            is_active=True
        )
        user.set_password(password)

        db_session.add(user)
        db_session.commit()

        click.echo(f'Admin user {username} created successfully!')

    @app.cli.command()
    def check_migrations():
        """Check database migration status"""
        from app.utils.migrations import get_current_schema_version, get_required_schema_version, get_schema_version_info

        db_path = app.config['DATABASE_PATH']
        current = get_current_schema_version(db_path)
        required = get_required_schema_version()

        click.echo(f'Current schema version: {current}')
        click.echo(f'Required schema version: {required}')

        if current == required:
            click.echo('[OK] Database is up to date')
        elif current > required:
            click.echo('[WARNING] Database is newer than application')
        else:
            click.echo(f'[WARNING] Database needs update ({required - current} migration(s) pending)')

    @app.cli.command()
    def apply_migrations():
        """Apply pending database migrations"""
        from app.utils.migrations import check_and_apply_migrations

        db_path = app.config['DATABASE_PATH']
        success = check_and_apply_migrations(db_path, interactive=True)

        if success:
            click.echo('[SUCCESS] Migrations completed successfully')
        else:
            click.echo('[ERROR] Migration failed or cancelled')

    @app.cli.command()
    def migration_history():
        """Show database migration history"""
        from app.utils.migrations import get_schema_version_info

        db_path = app.config['DATABASE_PATH']
        info = get_schema_version_info(db_path)

        click.echo(f"\nCurrent Version: {info['current_version']}")
        click.echo("\nMigration History:")
        click.echo("-" * 70)

        for migration in info['migration_history']:
            click.echo(f"Version {migration['version']:3d}: {migration['description']}")
            click.echo(f"             Applied: {migration['applied_date']} by {migration['applied_by']}")
            click.echo()


def register_db_selector_middleware(app):
    """
    Register before_request handler for database selection

    Args:
        app: Flask application
    """
    from flask import request, redirect, url_for

    @app.before_request
    def handle_db_selection():
        """
        Ensure database is selected before any request
        Resolve session-specific database to g.db_session
        """
        # Skip for static files
        if request.endpoint and request.endpoint.startswith('static'):
            return

        # Debug logging to help trace why certain requests are redirected
        try:
            logger.debug(
                "handle_db_selection called: endpoint=%s path=%s args=%s headers_accept=%s",
                str(request.endpoint),
                str(request.path),
                dict(request.args),
                str(request.headers.get('Accept')),
            )
        except Exception:
            pass

        # Also write a short trace to a logfile for post-mortem analysis
        try:
            log_dir = os.path.join(app.root_path, '..', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            trace_file = os.path.join(log_dir, 'db_selector_debug.log')
            with open(trace_file, 'a', encoding='utf-8') as fh:
                fh.write(f"endpoint={request.endpoint} path={request.path} args={dict(request.args)} Accept={request.headers.get('Accept')}\n")
        except Exception:
            pass

        # Allow explicit bypass via query param or header for AJAX helpers
        # e.g. /select-db/mapped-drives?_skip_db_selector=1 or header X-Skip-DB-Selector: 1
        try:
            if request.args.get('_skip_db_selector') == '1' or request.headers.get('X-Skip-DB-Selector') == '1':
                print(f"[DBG] handle_db_selection: bypass via param/header for path={request.path}")
                return
        except Exception:
            pass

        # If the client explicitly accepts JSON (AJAX), don't redirect to the
        # selector page — allow the endpoint to return JSON (useful for mapped
        # drives and other AJAX helpers)
        accept_json = False
        try:
            accept_json = request.accept_mimetypes.accept_json
        except Exception:
            accept_json = False

        if accept_json:
            # For AJAX/API requests we do not want to redirect to the selector page
            # (that would return HTML to an AJAX caller). However, we still want
            # any existing session-selected database to be wired into the
            # request context so `db_session` LocalProxy resolves correctly.

            # If a database was already selected in the session, set up the
            # per-request session so handlers (including AJAX helpers) will
            # use the correct database connection.
            try:
                selected_db_path = session.get('selected_db_path')
                if selected_db_path:
                    abs_path = os.path.abspath(selected_db_path)
                    engine, db_sess = get_or_create_engine_session(abs_path, app)
                    g.db_session = db_sess
                    g.selected_db_path = abs_path
                    from app.utils.db_helpers import get_snapshot_dir_for_db
                    g.snapshot_dir = get_snapshot_dir_for_db(abs_path)
            except Exception:
                # If anything goes wrong here, do not block the request; the
                # caller will receive whatever the endpoint returns. We avoid
                # raising here to keep AJAX helpers robust during debugging.
                pass

            return

        # Require authentication before selecting a database
        # Allow auth routes (login/logout) so authentication works even when no DB selected
        if request.endpoint and request.endpoint.startswith('auth.'):
            return

        # If the user is not authenticated, redirect to login first
        try:
            from flask_login import current_user as _cu
            if not _cu.is_authenticated:
                return redirect(url_for('auth.login'))
        except Exception:
            pass

        # Skip for db_select routes
        if request.endpoint and request.endpoint.startswith('db_select.'):
            return

        # Skip API endpoints so AJAX helpers can function without redirect
        if request.path and request.path.startswith('/api'):
            return
        # Also skip any direct path under /select-db (covers AJAX/OPTIONS where
        # request.endpoint may not be set yet)
        if request.path and request.path.startswith('/select-db'):
            return

        # Check if database is selected in session (no default fallback)
        selected_db_path = session.get('selected_db_path')

        if not selected_db_path:
            # No database selected - redirect to selector
            return redirect(url_for('db_select.select_database'))

        # Database is selected - set up per-request session
        abs_path = os.path.abspath(selected_db_path)

        # Get or create engine/session for this database
        try:
            engine, db_sess = get_or_create_engine_session(abs_path, app)
            g.db_session = db_sess
            g.selected_db_path = abs_path

            # Also set snapshot directory for this database
            from app.utils.db_helpers import get_snapshot_dir_for_db
            g.snapshot_dir = get_snapshot_dir_for_db(abs_path)

        except Exception as e:
            logger.error(f"Failed to initialize database session: {e}")
            # Clear invalid selection and redirect to selector
            session.pop('selected_db_path', None)
            from flask import flash
            flash(f'Failed to open selected database: {str(e)}', 'danger')
            return redirect(url_for('db_select.select_database'))


def register_template_filters(app):
    """
    Register Jinja2 template filters for permissions

    Args:
        app: Flask application
    """
    from app.utils.permissions import (
        can_view_field,
        get_field_display_value,
        can_view_relationship,
        can_view_ned_content,
        get_ned_field_value,
        get_permission_level_name
    )
    from flask_login import current_user

    @app.template_filter('can_view_field')
    def can_view_field_filter(table_name, record_id, field_name, user=None):
        """
        Template filter to check if user can view a field

        Usage in template:
            {% if 'projects'|can_view_field(project.project_id, 'capex') %}
                {{ project.capex }}
            {% else %}
                [Confidential]
            {% endif %}
        """
        if user is None:
            user = current_user
        return can_view_field(user, table_name, record_id, field_name)

    @app.template_filter('field_value')
    def field_value_filter(entity, field_name, table_name=None, redaction_message="[Confidential]"):
        """
        Template filter to get field value with automatic redaction

        Usage in template:
            {{ project|field_value('capex') }}
            {{ project|field_value('opex', redaction_message='[Hidden]') }}
        """
        return get_field_display_value(current_user, entity, field_name, table_name, redaction_message)

    @app.template_filter('can_view_relationship')
    def can_view_relationship_filter(relationship, user=None):
        """
        Template filter to check if user can view a relationship

        Usage in template:
            {% if rel|can_view_relationship %}
                {{ rel.vendor.vendor_name }}
            {% endif %}
        """
        if user is None:
            user = current_user
        return can_view_relationship(user, relationship)

    @app.template_filter('can_view_ned')
    def can_view_ned_filter(user=None):
        """
        Template filter to check if user can view NED content

        Usage in template:
            {% if ''|can_view_ned %}
                <div class="ned-notes">{{ relationship_notes }}</div>
            {% endif %}
        """
        if user is None:
            user = current_user
        return can_view_ned_content(user)

    @app.template_filter('ned_field_value')
    def ned_field_value_filter(entity, field_name, redaction_message="[NED Team Only]"):
        """
        Template filter to get NED field value with automatic redaction

        Usage in template:
            {{ client|ned_field_value('relationship_notes') }}
        """
        return get_ned_field_value(current_user, entity, field_name, redaction_message)

    @app.template_filter('permission_level')
    def permission_level_filter(user=None):
        """
        Template filter to get user's permission level name

        Usage in template:
            <span class="badge">{{ current_user|permission_level }}</span>
        """
        if user is None:
            user = current_user
        return get_permission_level_name(user)
