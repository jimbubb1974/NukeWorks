"""Snapshot management utilities"""
from __future__ import annotations

import os
import shutil
import threading
from datetime import datetime, time, timedelta

from flask import current_app

from app import db_session
from app.models import DatabaseSnapshot
from app.utils.system_settings import get_system_setting


_scheduler_lock = threading.Lock()
_scheduler_thread: threading.Thread | None = None
_scheduler_stop = threading.Event()


def _get_database_path():
    config = current_app.config
    return config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')


def _snapshot_dir():
    configured = get_system_setting('snapshot_dir', '', typed=False)
    if configured:
        path = configured if os.path.isabs(configured) else os.path.join(current_app.root_path, configured)
    else:
        path = os.path.join(current_app.root_path, 'snapshots')
    os.makedirs(path, exist_ok=True)
    return path


def _snapshot_filename(snapshot_type: str) -> str:
    timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    return f"{timestamp}_{snapshot_type.lower()}.sqlite"


def create_snapshot(
    snapshot_type: str = 'MANUAL',
    user_id: int | None = None,
    description: str | None = None,
    retain: bool = False
) -> DatabaseSnapshot:
    db_path = _get_database_path()
    if not os.path.exists(db_path):
        raise FileNotFoundError('Database file not found for snapshot creation.')

    dest_dir = _snapshot_dir()
    file_name = _snapshot_filename(snapshot_type)
    dest_path = os.path.join(dest_dir, file_name)

    shutil.copy2(db_path, dest_path)
    size_bytes = os.path.getsize(dest_path)

    snapshot = DatabaseSnapshot(
        snapshot_timestamp=datetime.utcnow(),
        created_by_user_id=user_id,
        snapshot_type=snapshot_type,
        file_path=dest_path,
        description=description,
        snapshot_size_bytes=size_bytes,
        is_retained=retain
    )
    db_session.add(snapshot)
    db_session.commit()
    return snapshot


def restore_snapshot(snapshot: DatabaseSnapshot) -> str:
    db_path = _get_database_path()
    if not os.path.exists(snapshot.file_path):
        raise FileNotFoundError('Snapshot file not found for restore.')

    backup_path = f"{db_path}.pre_restore_{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    shutil.copy2(snapshot.file_path, db_path)
    return backup_path


def _parse_snapshot_time() -> time:
    time_str = get_system_setting('daily_snapshot_time', '02:00')
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour=hour, minute=minute)
    except ValueError:
        return time(hour=2, minute=0)


def _last_automated_snapshot() -> DatabaseSnapshot | None:
    return (
        db_session.query(DatabaseSnapshot)
        .filter(DatabaseSnapshot.snapshot_type.isnot(None))
        .filter(DatabaseSnapshot.snapshot_type.like('AUTOMATED%'))
        .order_by(DatabaseSnapshot.snapshot_timestamp.desc())
        .first()
    )


def should_run_automated_snapshot(now: datetime | None = None) -> bool:
    now = now or datetime.utcnow()

    if not bool(get_system_setting('auto_snapshot_enabled', True)):
        return False

    scheduled_time = _parse_snapshot_time()
    scheduled_today = datetime.combine(now.date(), scheduled_time)
    if now < scheduled_today:
        return False

    last_auto = _last_automated_snapshot()
    if last_auto and last_auto.snapshot_timestamp.date() == now.date():
        return False

    return True


def get_next_snapshot_run():
    now = datetime.utcnow()
    enabled = bool(get_system_setting('auto_snapshot_enabled', True))
    scheduled_time = _parse_snapshot_time()
    today_run = datetime.combine(now.date(), scheduled_time)

    last_auto = _last_automated_snapshot()
    if last_auto and last_auto.snapshot_timestamp.date() == now.date():
        next_run = datetime.combine(now.date() + timedelta(days=1), scheduled_time)
    else:
        next_run = today_run

    return enabled, next_run


def enforce_snapshot_retention():
    retention_days = int(get_system_setting('snapshot_retention_days', 30))
    max_snapshots = int(get_system_setting('max_snapshots', 10))

    cutoff = datetime.utcnow() - timedelta(days=retention_days)

    snapshots = db_session.query(DatabaseSnapshot).order_by(DatabaseSnapshot.snapshot_timestamp.asc()).all()
    deletions = 0
    for snapshot in snapshots:
        if snapshot.is_retained:
            continue
        if not snapshot.snapshot_type or not snapshot.snapshot_type.startswith('AUTOMATED'):
            continue
        if snapshot.snapshot_timestamp < cutoff:
            _delete_snapshot(snapshot)
            deletions += 1

    auto_snapshots = [
        s for s in snapshots
        if not s.is_retained and s.snapshot_type and s.snapshot_type.startswith('AUTOMATED')
    ]
    if len(auto_snapshots) > max_snapshots:
        to_remove = len(auto_snapshots) - max_snapshots
        for snapshot in auto_snapshots[:to_remove]:
            _delete_snapshot(snapshot)
            deletions += 1
    return deletions


def _delete_snapshot(snapshot: DatabaseSnapshot):
    try:
        if os.path.exists(snapshot.file_path):
            os.remove(snapshot.file_path)
    except OSError:
        pass
    db_session.delete(snapshot)
    db_session.commit()


def last_snapshot_info():
    last = db_session.query(DatabaseSnapshot).order_by(DatabaseSnapshot.snapshot_timestamp.desc()).first()
    return last


def _scheduler_iteration(app) -> float:
    try:
        if should_run_automated_snapshot():
            snapshot = create_snapshot('AUTOMATED_DAILY', description='Automated daily snapshot')
            app.logger.info('Automated snapshot created: %s', snapshot.file_path)
            enforce_snapshot_retention()
    except Exception as exc:  # pragma: no cover - defensive logging
        app.logger.exception('Automated snapshot failed: %s', exc)
        return 300.0

    enabled, next_run = get_next_snapshot_run()
    if not enabled:
        return 300.0

    now = datetime.utcnow()
    delta = (next_run - now).total_seconds()
    if delta < 60:
        delta = 60
    return min(delta, 3600.0)


def _snapshot_scheduler_loop(app):
    while not _scheduler_stop.is_set():
        with app.app_context():
            sleep_for = _scheduler_iteration(app)
        _scheduler_stop.wait(timeout=sleep_for)


def start_snapshot_scheduler(app=None):
    app = app or current_app
    if app is None:
        raise RuntimeError('Application context required to start snapshot scheduler')

    if hasattr(app, '_get_current_object'):
        app = app._get_current_object()

    if getattr(app, 'testing', False):
        return

    with _scheduler_lock:
        global _scheduler_thread
        if _scheduler_thread and _scheduler_thread.is_alive():
            return

        _scheduler_stop.clear()
        thread = threading.Thread(
            target=_snapshot_scheduler_loop,
            args=(app,),
            daemon=True,
            name='snapshot-scheduler'
        )
        thread.start()
        _scheduler_thread = thread
        app.logger.debug('Snapshot scheduler started')


def stop_snapshot_scheduler():  # pragma: no cover - used for teardown/manual control
    with _scheduler_lock:
        global _scheduler_thread
        if not _scheduler_thread:
            return
        _scheduler_stop.set()
        _scheduler_thread.join(timeout=5)
        _scheduler_thread = None
