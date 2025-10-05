"""Pytest configuration and fixtures for NukeWorks."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool

import app as app_module
from app.models import Base
import test_permissions  # type: ignore
import test_validators  # type: ignore


@pytest.fixture(scope='session')
def _database_path(tmp_path_factory) -> Path:
    """Return a temporary on-disk SQLite database path for tests."""
    db_dir = tmp_path_factory.mktemp('db')
    return db_dir / 'test_nukeworks.sqlite'


@pytest.fixture(scope='session')
def app(_database_path: Path):
    """Create a Flask application configured for testing."""
    # Ensure deterministic database configuration
    from config import TestingConfig

    TestingConfig.DATABASE_PATH = str(_database_path)
    TestingConfig.SQLALCHEMY_DATABASE_URI = f'sqlite:///{_database_path}'
    TestingConfig.SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool,
    }

    os.environ['FLASK_ENV'] = 'testing'

    flask_app = app_module.create_app('testing')

    # Recreate the schema explicitly to ensure a clean slate
    engine = app_module.db_session.get_bind()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    flask_app.testing = True
    return flask_app


@pytest.fixture(scope='session')
def db_session(app):
    """Provide the SQLAlchemy session for tests."""
    return app.db_session


@pytest.fixture(autouse=True, scope='session')
def _wire_test_modules(app):
    """Point test helper modules at the active database session."""
    test_permissions.db_session = app.db_session
    test_validators.db_session = app.db_session
    yield


@pytest.fixture(scope='function')
def permission_dataset(app, db_session):
    """Set up users, project, and relationships used across permission tests."""
    from test_permissions import (
        setup_test_users,
        setup_test_data,
        cleanup_test_data,
    )

    with app.app_context():
        admin, ned_user, conf_user, standard_user = setup_test_users()
        project, vendor, public_rel, conf_rel = setup_test_data(admin)

        yield {
            'admin': admin,
            'ned_user': ned_user,
            'conf_user': conf_user,
            'standard_user': standard_user,
            'project': project,
            'vendor': vendor,
            'public_rel': public_rel,
            'conf_rel': conf_rel,
        }

        cleanup_test_data()


@pytest.fixture
def admin(permission_dataset):
    return permission_dataset['admin']


@pytest.fixture
def ned_user(permission_dataset):
    return permission_dataset['ned_user']


@pytest.fixture
def conf_user(permission_dataset):
    return permission_dataset['conf_user']


@pytest.fixture
def standard_user(permission_dataset):
    return permission_dataset['standard_user']


@pytest.fixture
def project(permission_dataset):
    return permission_dataset['project']


@pytest.fixture
def public_rel(permission_dataset):
    return permission_dataset['public_rel']


@pytest.fixture
def conf_rel(permission_dataset):
    return permission_dataset['conf_rel']
