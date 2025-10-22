"""
NukeWorks - Configuration Module
Handles application configuration for different environments
"""
import os
import sys
from pathlib import Path
from datetime import timedelta

# Base directory for the application
basedir = Path(__file__).parent.absolute()


def _runtime_root() -> Path:
    """Return the directory where bundled resources are located.

    In PyInstaller onedir mode, resources are placed under the distribution
    directory; in some versions they may reside in a nested "_internal" dir.
    """
    if getattr(sys, 'frozen', False):
        meipass = Path(getattr(sys, '_MEIPASS', basedir))
        # Prefer _MEIPASS if present
        if meipass.exists():
            return meipass
        # Fallbacks: current executable directory and potential _internal
        exec_dir = Path(sys.executable).resolve().parent
        internal = exec_dir / "_internal"
        if internal.exists():
            return internal
        return exec_dir
    return basedir


def _resource_path(relative_path: str) -> Path:
    """
    Resolve a resource path that may live inside a PyInstaller bundle.

    Handles the onedir layout where files may be extracted into a directory
    of the same name (e.g., "<name>/<name>").
    """
    relative = Path(relative_path)
    runtime_root = _runtime_root()
    runtime_candidate = runtime_root / relative

    if runtime_candidate.is_file():
        return runtime_candidate
    if runtime_candidate.is_dir():
        nested = runtime_candidate / relative.name
        if nested.exists():
            return nested

    # Also check PyInstaller's _internal directory (newer layouts)
    internal_candidate = runtime_root / "_internal" / relative
    if internal_candidate.exists():
        return internal_candidate

    # Also check one level up for onedir where app/ is beside exe
    parent_candidate = runtime_root.parent / relative
    if parent_candidate.exists():
        return parent_candidate

    fallback = basedir / relative
    if fallback.is_file():
        return fallback
    if fallback.is_dir():
        nested = fallback / relative.name
        if nested.exists():
            return nested

    return runtime_candidate


def _storage_root() -> Path:
    """Determine the writable storage root for runtime data."""
    override = os.environ.get('NUKEWORKS_DATA_DIR')
    if override:
        return Path(override).expanduser()

    if sys.platform.startswith('win'):
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    else:
        base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))

    return base / 'NukeWorks'


STORAGE_ROOT = _storage_root()
DEV_DB_TEMPLATE = _resource_path('dev_nukeworks.sqlite')
MIGRATIONS_ROOT = _resource_path('migrations')


class Config:
    """Base configuration class with common settings"""

    # Secret key for session management (MUST be changed in production)
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)

    # Database configuration
    STORAGE_ROOT = STORAGE_ROOT
    DATABASE_FILENAME = 'nukeworks_db.sqlite'
    DEFAULT_DB_TEMPLATE = None
    DATABASE_PATH = os.environ.get('NUKEWORKS_DB_PATH') or \
                    str(STORAGE_ROOT / DATABASE_FILENAME)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True to log SQL queries

    # SQLite-specific configuration for network drive optimization
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'timeout': 30.0,  # 30 second timeout for database locks
            'check_same_thread': False,  # Allow multi-threading
        },
        'pool_pre_ping': True,  # Verify connections before using
    }

    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = str(STORAGE_ROOT / 'flask_sessions')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    UPLOAD_FOLDER = str(STORAGE_ROOT / 'uploads')
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'pdf', 'png', 'jpg', 'jpeg'}

    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit on CSRF tokens

    # Application settings
    ITEMS_PER_PAGE = 50  # Pagination
    ROUNDTABLE_HISTORY_LIMIT = 3  # Number of roundtable entries to keep per entity

    # Snapshot settings
    SNAPSHOT_DIR = os.environ.get('NUKEWORKS_SNAPSHOT_DIR') or \
                   str(STORAGE_ROOT / 'snapshots')
    AUTO_SNAPSHOT_ENABLED = True
    DAILY_SNAPSHOT_TIME = '02:00'  # 2 AM
    SNAPSHOT_RETENTION_DAYS = 30
    MAX_SNAPSHOTS = 10

    # Migration settings
    MIGRATIONS_DIR = str(MIGRATIONS_ROOT)
    APPLICATION_VERSION = '1.0.0'
    REQUIRED_SCHEMA_VERSION = 9  # Updated for company field cleanup

    # Report settings
    COMPANY_NAME = 'MPR Associates'
    CONFIDENTIAL_WATERMARK_ENABLED = True
    CONFIDENTIAL_WATERMARK_TEXT = 'CONFIDENTIAL'

    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = str(STORAGE_ROOT / 'logs' / 'nukeworks.log')

    # Flask-specific
    JSON_SORT_KEYS = False
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Disable caching for development


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries

    # Override with local database for development
    DATABASE_FILENAME = 'dev_nukeworks.sqlite'
    DEFAULT_DB_TEMPLATE = str(DEV_DB_TEMPLATE)
    DATABASE_PATH = os.environ.get('DEV_DB_PATH') or str(STORAGE_ROOT / DATABASE_FILENAME)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False

    # Production should ALWAYS use environment variables for sensitive data
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Production database path (typically on network drive)
    DATABASE_PATH = os.environ.get('NUKEWORKS_DB_PATH')

    def __init__(self):
        """Validate required production settings"""
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set for production!")
        if not self.DATABASE_PATH:
            raise ValueError("NUKEWORKS_DB_PATH environment variable must be set for production!")

    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

    # Stricter session settings for production
    SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True

    # Use in-memory database for testing
    DATABASE_PATH = ':memory:'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env_name=None):
    """
    Get configuration object based on environment name

    Args:
        env_name: Name of environment ('development', 'production', 'testing')
                  If None, reads from FLASK_ENV or defaults to 'development'

    Returns:
        Configuration class object
    """
    if env_name is None:
        env_name = os.environ.get('FLASK_ENV', 'development')

    return config.get(env_name, config['default'])
