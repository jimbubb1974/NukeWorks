"""Helpers for working with system settings"""
from datetime import datetime
from functools import lru_cache

from flask import current_app

from app.models import SystemSetting, RoundtableHistory
from app import db_session as global_session


def _get_session():
    if global_session is not None:
        return global_session
    if current_app:
        return current_app.db_session
    raise RuntimeError('Database session unavailable')


@lru_cache(maxsize=128)
def get_system_setting(setting_name, default=None, typed=True):
    """Return system setting value or default"""
    session = _get_session()
    setting = session.query(SystemSetting).filter_by(setting_name=setting_name).first()
    if not setting:
        return default

    value = setting.get_typed_value() if typed else setting.setting_value
    return default if value is None else value


def clear_system_setting_cache():
    """Clear cached system setting lookups"""
    get_system_setting.cache_clear()


def get_roundtable_history_limit(default=3):
    value = get_system_setting('roundtable_history_limit', default=default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def enforce_roundtable_history_limit(entity_type: str, entity_id: int, limit: int | None = None):
    """Ensure only the most recent N roundtable entries are kept"""
    session = _get_session()
    limit = limit or get_roundtable_history_limit()
    if limit <= 0:
        return

    entries = session.query(RoundtableHistory).filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(RoundtableHistory.meeting_date.desc(), RoundtableHistory.history_id.desc()).all()

    if len(entries) <= limit:
        return

    for entry in entries[limit:]:
        session.delete(entry)
    session.commit()


def set_system_setting(setting_name: str, value, setting_type: str | None = None, user_id: int | None = None):
    """Create or update a system setting"""
    session = _get_session()

    # Determine type if not provided
    if setting_type is None:
        if isinstance(value, bool):
            setting_type = 'boolean'
        elif isinstance(value, int):
            setting_type = 'integer'
        else:
            setting_type = 'text'

    # Convert value to string for storage
    if setting_type == 'boolean':
        stored_value = 'true' if bool(value) else 'false'
    else:
        stored_value = '' if value is None else str(value)

    setting = session.query(SystemSetting).filter_by(setting_name=setting_name).first()
    if setting:
        setting.setting_value = stored_value
        setting.setting_type = setting_type
        setting.modified_by = user_id
        setting.modified_date = datetime.utcnow()
    else:
        setting = SystemSetting(
            setting_name=setting_name,
            setting_value=stored_value,
            setting_type=setting_type,
            modified_by=user_id,
            modified_date=datetime.utcnow()
        )
        session.add(setting)

    session.commit()
    clear_system_setting_cache()
