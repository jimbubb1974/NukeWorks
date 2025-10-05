"""
NukeWorks Flask Application Factory
"""
import os
from flask import Flask
from flask_login import LoginManager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import scoped_session, sessionmaker
from config import get_config


# Global objects
login_manager = LoginManager()
db_session = None


def create_app(config_name=None):
    """
    Create and configure Flask application

    Args:
        config_name: Configuration environment name (development, production, testing)

    Returns:
        Configured Flask application
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Ensure required directories exist
    for directory in ['flask_sessions', 'logs', 'uploads']:
        path = os.path.join(app.root_path, '..', directory)
        os.makedirs(path, exist_ok=True)

    # Initialize database
    init_db(app)

    # Initialize Flask-Login
    init_login_manager(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_commands(app)

    # Register template filters
    register_template_filters(app)

    # Start background scheduler for automated snapshots (disabled during tests)
    from app.services.snapshots import start_snapshot_scheduler

    start_snapshot_scheduler(app)

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


def init_db(app):
    """
    Initialize database connection with SQLite optimizations

    Args:
        app: Flask application
    """
    global db_session

    # Create SQLAlchemy engine
    engine = create_engine(
        app.config['SQLALCHEMY_DATABASE_URI'],
        **app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}),
        echo=app.config.get('SQLALCHEMY_ECHO', False)
    )

    # Enable WAL mode for better concurrency
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite PRAGMAs for optimization"""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute(f"PRAGMA busy_timeout={int(app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('connect_args', {}).get('timeout', 30) * 1000)}")
        cursor.close()

    # Create scoped session
    session_factory = sessionmaker(bind=engine)
    db_session = scoped_session(session_factory)

    # Attach audit logging listeners before the session is used
    from app.services.audit import init_audit_logging

    init_audit_logging(db_session)

    # Import models to register them
    from app import models

    # Create all tables if they don't exist
    models.Base.metadata.create_all(engine)
    _ensure_product_columns(engine)
    _ensure_product_columns(engine)

    # Store db_session in app for easy access
    app.db_session = db_session

    # Teardown context
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Remove database session at the end of request"""
        db_session.remove()


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
        existing = {row[1] for row in connection.execute(text('PRAGMA table_info(products)'))}
        for column, ddl in product_columns.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE products ADD COLUMN {column} {ddl}"))

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
    from app.routes import auth, dashboard, vendors, projects, owners, operators, technologies, offtakers, clients, crm, reports, admin, contact_log, network

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(vendors.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(owners.bp)
    app.register_blueprint(operators.bp)
    app.register_blueprint(technologies.bp)
    app.register_blueprint(offtakers.bp)
    app.register_blueprint(clients.bp)
    app.register_blueprint(crm.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(contact_log.bp)
    app.register_blueprint(network.bp)


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
            click.echo('✓ Database is up to date')
        elif current > required:
            click.echo('⚠ Database is newer than application')
        else:
            click.echo(f'⚠ Database needs update ({required - current} migration(s) pending)')

    @app.cli.command()
    def apply_migrations():
        """Apply pending database migrations"""
        from app.utils.migrations import check_and_apply_migrations

        db_path = app.config['DATABASE_PATH']
        success = check_and_apply_migrations(db_path, interactive=True)

        if success:
            click.echo('✓ Migrations completed successfully')
        else:
            click.echo('✗ Migration failed or cancelled')

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
