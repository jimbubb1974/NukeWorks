"""
NukeWorks - Configuration Module
Handles application configuration for different environments
"""
import os
from pathlib import Path
from datetime import timedelta

# Base directory for the application
basedir = Path(__file__).parent.absolute()


class Config:
    """Base configuration class with common settings"""

    # Secret key for session management (MUST be changed in production)
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)

    # Database configuration
    DATABASE_PATH = os.environ.get('NUKEWORKS_DB_PATH') or \
                    str(basedir / 'nukeworks_db.sqlite')
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
    SESSION_FILE_DIR = str(basedir / 'flask_sessions')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    UPLOAD_FOLDER = str(basedir / 'uploads')
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'pdf', 'png', 'jpg', 'jpeg'}

    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit on CSRF tokens

    # Application settings
    ITEMS_PER_PAGE = 50  # Pagination
    ROUNDTABLE_HISTORY_LIMIT = 3  # Number of roundtable entries to keep per entity

    # Snapshot settings
    SNAPSHOT_DIR = os.environ.get('NUKEWORKS_SNAPSHOT_DIR') or \
                   str(basedir / 'snapshots')
    AUTO_SNAPSHOT_ENABLED = True
    DAILY_SNAPSHOT_TIME = '02:00'  # 2 AM
    SNAPSHOT_RETENTION_DAYS = 30
    MAX_SNAPSHOTS = 10

    # Migration settings
    MIGRATIONS_DIR = str(basedir / 'migrations')
    APPLICATION_VERSION = '1.0.0'
    REQUIRED_SCHEMA_VERSION = 6  # Updated for database selection feature

    # Report settings
    COMPANY_NAME = 'MPR Associates'
    CONFIDENTIAL_WATERMARK_ENABLED = True
    CONFIDENTIAL_WATERMARK_TEXT = 'CONFIDENTIAL'

    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = str(basedir / 'logs' / 'nukeworks.log')

    # Flask-specific
    JSON_SORT_KEYS = False
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Disable caching for development


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries

    # Override with local database for development
    DATABASE_PATH = os.environ.get('DEV_DB_PATH') or str(basedir / 'dev_nukeworks.sqlite')
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
