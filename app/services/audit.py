"""Audit logging integration for SQLAlchemy session events."""
from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict

from flask import g, has_request_context
from flask_login import current_user
from sqlalchemy import inspect, event
from sqlalchemy.orm import Mapper, Session

from app.models import AuditLog


_thread_local = threading.local()


def set_audit_user(user_id: int | None) -> None:
    """Override the audit user for the current thread."""
    if user_id is None:
        clear_audit_user()
    else:
        _thread_local.user_id = user_id


def clear_audit_user() -> None:
    """Remove any thread-local audit user override."""
    if hasattr(_thread_local, 'user_id'):
        delattr(_thread_local, 'user_id')


@contextmanager
def audit_user_context(user_id: int | None):
    """Temporarily set the audit user within a context manager."""
    previous = getattr(_thread_local, 'user_id', None)
    set_audit_user(user_id)
    try:
        yield
    finally:
        if previous is None:
            clear_audit_user()
        else:
            set_audit_user(previous)


def _current_audit_user_id() -> int | None:
    """Best-effort resolution of the acting user for audit entries."""
    if hasattr(_thread_local, 'user_id'):
        return getattr(_thread_local, 'user_id')

    if has_request_context():  # pragma: no branch - cheap check
        if getattr(g, 'audit_user_id', None) is not None:
            return g.audit_user_id
        try:
            if current_user.is_authenticated:
                return current_user.user_id
        except Exception:  # pragma: no cover - defensive
            pass

    return None


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    if isinstance(value, (int, float, bool, str)):
        return value
    if isinstance(value, dict):
        return value
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return str(value)


def _serialize_columns(obj) -> Dict[str, Any]:
    mapper: Mapper = inspect(obj).mapper
    data: Dict[str, Any] = {}
    for column in mapper.columns:
        key = column.key
        data[key] = _serialize_value(getattr(obj, key, None))
    return data


def _record_id_for(obj) -> int | None:
    identity = inspect(obj).identity
    if not identity:
        return None
    if len(identity) == 1:
        return identity[0]
    # Composite keys are uncommon; fall back to string join handled in caller
    return identity


def _should_skip(obj) -> bool:
    return isinstance(obj, AuditLog)


def _json_dump(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, default=str)


def init_audit_logging(session_factory: Session) -> None:
    """Attach audit event listeners to the provided SQLAlchemy session."""
    if getattr(session_factory, '_audit_logging_enabled', False):
        return

    session_factory._audit_logging_enabled = True  # type: ignore[attr-defined]

    @event.listens_for(session_factory, 'before_flush')
    def _capture_changes(session: Session, flush_context, instances):
        if session.info.get('_suspend_audit'):
            return

        entries = session.info.setdefault('_pending_audit', {
            'create': [],
            'update': [],
            'delete': [],
        })

        for obj in list(session.new):
            if _should_skip(obj):
                continue
            entries['create'].append({
                'obj': obj,
                'values': _serialize_columns(obj),
            })

        for obj in list(session.deleted):
            if _should_skip(obj):
                continue
            entries['delete'].append({
                'obj': obj,
                'values': _serialize_columns(obj),
            })

        for obj in list(session.dirty):
            if _should_skip(obj):
                continue
            if not session.is_modified(obj, include_collections=False):
                continue
            state = inspect(obj)
            mapper = state.mapper
            changes: list[dict[str, Any]] = []
            for attr in mapper.column_attrs:
                hist = state.attrs[attr.key].history
                if not hist.has_changes():
                    continue
                old_value = hist.deleted[0] if hist.deleted else None
                new_value = hist.added[0] if hist.added else getattr(obj, attr.key)
                if _serialize_value(old_value) == _serialize_value(new_value):
                    continue
                changes.append({
                    'field': attr.key,
                    'old': _serialize_value(old_value),
                    'new': _serialize_value(new_value),
                })
            if changes:
                entries['update'].append({
                    'obj': obj,
                    'changes': changes,
                })

    @event.listens_for(session_factory, 'after_flush')
    def _write_audit_entries(session: Session, flush_context):
        pending = session.info.pop('_pending_audit', None)
        if not pending:
            return

        user_id = _current_audit_user_id()
        audit_rows: list[AuditLog] = []

        def resolve_record(obj) -> tuple[int | None, str | None]:
            record_identifier = _record_id_for(obj)
            if isinstance(record_identifier, tuple):
                return None, f'Composite key: {json.dumps(record_identifier)}'
            return record_identifier, None

        for payload in pending.get('create', []):
            obj = payload['obj']
            record_id, notes = resolve_record(obj)
            audit_rows.append(AuditLog(
                user_id=user_id,
                action='CREATE',
                table_name=obj.__tablename__,
                record_id=record_id,
                field_name=None,
                old_value=None,
                new_value=_json_dump(payload['values']),
                notes=notes,
            ))

        for payload in pending.get('delete', []):
            obj = payload['obj']
            record_id, notes = resolve_record(obj)
            audit_rows.append(AuditLog(
                user_id=user_id,
                action='DELETE',
                table_name=obj.__tablename__,
                record_id=record_id,
                field_name=None,
                old_value=_json_dump(payload['values']),
                new_value=None,
                notes=notes,
            ))

        for payload in pending.get('update', []):
            obj = payload['obj']
            record_id, notes = resolve_record(obj)
            for change in payload['changes']:
                audit_rows.append(AuditLog(
                    user_id=user_id,
                    action='UPDATE',
                    table_name=obj.__tablename__,
                    record_id=record_id,
                    field_name=change['field'],
                    old_value=_json_dump(change['old']),
                    new_value=_json_dump(change['new']),
                    notes=notes,
                ))

        if not audit_rows:
            return

        session.info['_suspend_audit'] = True
        try:
            session.add_all(audit_rows)
        finally:
            session.info['_suspend_audit'] = False
