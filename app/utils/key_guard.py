"""
Encryption key fingerprint guard.

Every database records a fingerprint of the encryption keys it was written with
(system_settings.encryption_key_fingerprint). When a machine whose keys do not
match opens the database, writes are blocked and a banner explains why, so data
is never encrypted with a second, unreadable set of keys.

First use of a database with no stored fingerprint: every encrypted value is
checked against this machine's keys. Only if all of them decrypt (or there are
none) is the fingerprint recorded; otherwise the database stays "unverified" and
writes stay blocked until it is cleaned (scripts/clean_undecryptable.py).
"""
import hashlib
import logging
import time
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken
from flask import flash, g, jsonify, redirect, request, url_for

from app.exceptions import EncryptionKeyError

logger = logging.getLogger(__name__)

SETTING_NAME = 'encryption_key_fingerprint'
CACHE_TTL_SECONDS = 60
WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
EXEMPT_ENDPOINT_PREFIXES = ('static', 'auth.', 'db_select.')

# table -> (id column, [encrypted columns]). Keep in sync with scripts/check_decryption.py.
ENCRYPTED_COLUMNS = {
    'roundtable_history': ('history_id', [
        'discussion_encrypted', 'action_items_encrypted', 'next_steps_encrypted',
        'client_near_term_focus_encrypted', 'mpr_work_targets_encrypted',
        'client_strategic_objectives_encrypted',
    ]),
    'client_profiles': ('company_id', [
        'relationship_notes_encrypted', 'client_priority_encrypted', 'client_tier_encrypted',
    ]),
    'company_role_assignments': ('assignment_id', ['notes_encrypted']),
    'internal_external_links': ('link_id', ['relationship_strength_encrypted', 'notes_encrypted']),
    'projects': ('project_id', [
        'capex_encrypted', 'opex_encrypted', 'fuel_cost_encrypted', 'lcoe_encrypted',
    ]),
}

# db_path -> (expires_at, result dict)
_cache = {}


def _short(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()[:8]


def _local_keys():
    """Return {'confidential': bytes, 'ned_team': bytes} or None if keys are not configured."""
    from app.utils.key_management import KeyManager
    try:
        return {
            'confidential': KeyManager.get_key(KeyManager.CONFIDENTIAL),
            'ned_team': KeyManager.get_key(KeyManager.NED_TEAM),
        }
    except EncryptionKeyError:
        return None


def local_fingerprint(keys=None):
    keys = keys or _local_keys()
    if not keys:
        return None
    return f"conf:{_short(keys['confidential'])};ned:{_short(keys['ned_team'])}"


def _read_stored(session):
    from sqlalchemy import text
    row = session.execute(
        text('SELECT setting_value FROM system_settings WHERE setting_name = :n'),
        {'n': SETTING_NAME},
    ).first()
    return row[0] if row and row[0] else None


def _all_values_decrypt(session, keys) -> bool:
    """True if every non-empty encrypted value decrypts with one of this machine's keys."""
    from sqlalchemy import text
    ciphers = {name: Fernet(k) for name, k in keys.items()}
    existing = {r[0] for r in session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
    for table, (_, cols) in ENCRYPTED_COLUMNS.items():
        if table not in existing:
            continue
        have = {r[1] for r in session.execute(text(f'PRAGMA table_info({table})'))}
        cols = [c for c in cols if c in have]
        if not cols:
            continue
        # The app uses one specific key per table: a value readable only with the other key still fails
        cipher = ciphers['confidential' if table == 'projects' else 'ned_team']
        for row in session.execute(text(f'SELECT {", ".join(cols)} FROM {table}')):
            for value in row:
                if value is None or value == b'':
                    continue
                data = value if isinstance(value, bytes) else str(value).encode()
                try:
                    cipher.decrypt(data)
                except InvalidToken:
                    return False
    return True


def _stamp(session, fingerprint):
    from sqlalchemy import text
    now = datetime.now().isoformat(sep=' ')
    params = {'n': SETTING_NAME, 'v': fingerprint, 'd': now}
    updated = session.execute(
        text('UPDATE system_settings SET setting_value=:v, modified_date=:d WHERE setting_name=:n'), params
    ).rowcount
    if not updated:
        session.execute(
            text(
                'INSERT INTO system_settings (setting_name, setting_value, setting_type, description, modified_date) '
                "VALUES (:n, :v, 'text', 'Fingerprint of the encryption keys this database was written with', :d)"
            ),
            params,
        )
    session.commit()


def compute_status(session):
    """
    Return {'state': 'ok'|'mismatch'|'unverified'|'no_keys', 'local': str|None, 'stored': str|None}.
    """
    keys = _local_keys()
    if not keys:
        return {'state': 'no_keys', 'local': None, 'stored': None}
    local = local_fingerprint(keys)
    stored = _read_stored(session)

    if stored:
        return {'state': 'ok' if stored == local else 'mismatch', 'local': local, 'stored': stored}

    # No fingerprint recorded yet: verify against the real data before trusting these keys.
    if _all_values_decrypt(session, keys):
        try:
            _stamp(session, local)
        except Exception as exc:
            session.rollback()
            logger.warning('Could not record key fingerprint: %s', exc)
        return {'state': 'ok', 'local': local, 'stored': local}
    return {'state': 'unverified', 'local': local, 'stored': None}


def get_status():
    """Cached status for the currently selected database (None if none selected)."""
    db_path = getattr(g, 'selected_db_path', None)
    session = getattr(g, 'db_session', None)
    if not db_path or session is None:
        return None
    cached = _cache.get(db_path)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    try:
        result = compute_status(session)
    except Exception as exc:
        # Never lock users out because the check itself failed (e.g. table missing mid-migration)
        session.rollback()
        logger.warning('Key fingerprint check failed: %s', exc)
        return None
    _cache[db_path] = (time.monotonic() + CACHE_TTL_SECONDS, result)
    return result


def blocking_message(status):
    if status['state'] == 'mismatch':
        return (
            'Your encryption keys do not match the keys this database was written with '
            f"(database: {status['stored']}, this computer: {status['local']}). "
            'Saving is disabled so data is not encrypted with the wrong keys. '
            'Install the shared team keys and restart the app.'
        )
    return (
        'Some encrypted data in this database cannot be read with this computer\'s keys, '
        'so saving is disabled. An administrator should install the correct team keys or '
        'run scripts/clean_undecryptable.py.'
    )


def register_key_guard(app):
    """Block writes and expose a banner flag when the key fingerprint check fails."""
    from flask_login import current_user

    @app.before_request
    def key_fingerprint_guard():
        endpoint = request.endpoint or ''
        if endpoint.startswith(EXEMPT_ENDPOINT_PREFIXES) or request.path.startswith('/api'):
            return None
        if not current_user.is_authenticated:
            return None
        status = get_status()
        g.key_guard_status = status
        if not status or status['state'] not in ('mismatch', 'unverified'):
            return None
        if request.method not in WRITE_METHODS:
            return None

        message = blocking_message(status)
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({'error': message}), 403
        flash(message, 'danger')
        return redirect(request.referrer or url_for('dashboard.index'))

    @app.context_processor
    def inject_key_guard():
        status = getattr(g, 'key_guard_status', None)
        if status and status['state'] in ('mismatch', 'unverified'):
            return {'key_guard_banner': blocking_message(status)}
        return {'key_guard_banner': None}
