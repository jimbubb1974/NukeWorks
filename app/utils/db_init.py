"""
Database initialization utilities
"""
from datetime import datetime
from app.models import SystemSetting, SchemaVersion, User


def init_database(db_session):
    """
    Initialize database with default settings and admin user

    Args:
        db_session: SQLAlchemy database session
    """
    # Check if already initialized
    schema_version = db_session.query(SchemaVersion).first()
    if schema_version:
        print("Database already initialized")
        return

    # Initialize system settings
    init_system_settings(db_session)

    # Initialize schema version
    init_schema_version(db_session)

    # Create default admin user
    init_admin_user(db_session)

    db_session.commit()
    print("Database initialized successfully!")


def init_system_settings(db_session):
    """Initialize default system settings"""
    settings = [
        {
            'setting_name': 'company_name',
            'setting_value': 'MPR Associates',
            'setting_type': 'text',
            'description': 'Company name for reports'
        },
        {
            'setting_name': 'company_logo_path',
            'setting_value': '',
            'setting_type': 'text',
            'description': 'Path to company logo file'
        },
        {
            'setting_name': 'roundtable_history_limit',
            'setting_value': '3',
            'setting_type': 'integer',
            'description': 'Number of roundtable entries to keep per entity'
        },
        {
            'setting_name': 'auto_snapshot_enabled',
            'setting_value': 'true',
            'setting_type': 'boolean',
            'description': 'Enable automated database snapshots'
        },
        {
            'setting_name': 'daily_snapshot_time',
            'setting_value': '02:00',
            'setting_type': 'text',
            'description': 'Time for daily snapshots (HH:MM 24-hour)'
        },
        {
            'setting_name': 'snapshot_retention_days',
            'setting_value': '30',
            'setting_type': 'integer',
            'description': 'Days to keep automated snapshots'
        },
        {
            'setting_name': 'max_snapshots',
            'setting_value': '10',
            'setting_type': 'integer',
            'description': 'Maximum number of snapshots to keep'
        },
        {
            'setting_name': 'confidential_watermark_enabled',
            'setting_value': 'true',
            'setting_type': 'boolean',
            'description': 'Add CONFIDENTIAL watermark to reports'
        },
        {
            'setting_name': 'confidential_watermark_text',
            'setting_value': 'CONFIDENTIAL',
            'setting_type': 'text',
            'description': 'Watermark text for reports'
        },
    ]

    for setting_data in settings:
        setting = SystemSetting(**setting_data)
        db_session.add(setting)


def init_schema_version(db_session):
    """Initialize schema version"""
    schema_version = SchemaVersion(
        version=1,
        applied_date=datetime.now(),
        applied_by='system',
        description='Initial schema creation'
    )
    db_session.add(schema_version)


def init_admin_user(db_session):
    """Create default admin user (CHANGE PASSWORD AFTER FIRST LOGIN!)"""
    # Check if any users exist
    user_count = db_session.query(User).count()
    if user_count > 0:
        print("Users already exist, skipping admin creation")
        return

    admin = User(
        username='admin',
        email='admin@nukeworks.local',
        full_name='System Administrator',
        has_confidential_access=True,
        is_ned_team=True,
        is_admin=True,
        is_active=True
    )
    admin.set_password('admin123')  # CHANGE THIS IMMEDIATELY!

    db_session.add(admin)

    print("WARNING: Default admin user created with username 'admin' and password 'admin123'")
    print("PLEASE CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!")
