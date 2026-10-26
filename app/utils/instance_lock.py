"""
Advisory instance lock for database files.

SQLite itself is the final word on real write conflicts (via its own file
locking and PRAGMA busy_timeout). This module is purely advisory: it lets the
app warn a user *before* they hit a confusing "database is locked" error by
remembering which process (and, best-effort, which machine) last opened a
given database file.

Design notes:
- Lock state lives in small JSON files under STORAGE_ROOT/db_locks, keyed by
  a hash of the absolute database path, so it works for local files and for
  databases on shared network drives alike.
- A lock is considered live if it was written by a PID that is still running
  on the same hostname, or (for a different hostname, which we can't verify
  directly) if its heartbeat is recent. Anything else is treated as stale and
  silently overwritten, so a crashed process never permanently "locks" a
  database for everyone else.
- This module never attempts to force-close another process's real file
  handle. Clearing a lock only ever affects *this* process's own cached
  SQLAlchemy engine/connection and the advisory marker file.
"""
import ctypes
import hashlib
import json
import logging
import os
import socket
import sys
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# A lock with no heartbeat update in this long is treated as stale when we
# can't directly verify the owning process is still alive (different host).
REMOTE_STALE_SECONDS = 120

# Avoid writing the heartbeat file on every single request (especially bad
# on network drives) — only refresh it at most this often per db path.
_HEARTBEAT_MIN_INTERVAL = 30
_last_heartbeat_write: dict = {}


def _lock_dir() -> Path:
    from config import STORAGE_ROOT
    d = Path(STORAGE_ROOT) / 'db_locks'
    d.mkdir(parents=True, exist_ok=True)
    return d


def _lock_file_for(db_path: str) -> Path:
    abs_path = os.path.abspath(db_path)
    digest = hashlib.sha256(abs_path.encode('utf-8')).hexdigest()[:16]
    return _lock_dir() / f'{digest}.json'


def _pid_is_running(pid: Optional[int]) -> bool:
    """Best-effort liveness check for a PID on this machine."""
    if not pid:
        return False
    if sys.platform == 'win32':
        try:
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid)
            )
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return True  # Assume alive if we can't tell; safer to warn than not.
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
        except Exception:
            return True


def check_lock(db_path: str) -> dict:
    """
    Inspect any existing advisory lock for db_path.

    Returns:
        {
          'locked': bool,        # another live process appears to hold it
          'stale': bool,         # a lock file exists but looks abandoned
          'info': dict or None,  # raw lock contents, if any
        }
    """
    result = {'locked': False, 'stale': False, 'info': None, 'same_host': False}
    lock_file = _lock_file_for(db_path)

    if not lock_file.exists():
        return result

    try:
        info = json.loads(lock_file.read_text())
    except Exception:
        result['stale'] = True
        return result

    result['info'] = info

    same_host = info.get('hostname') == socket.gethostname()
    result['same_host'] = same_host
    pid = info.get('pid')

    if same_host:
        if pid and pid != os.getpid() and _pid_is_running(pid):
            result['locked'] = True
        else:
            result['stale'] = True
    else:
        last_seen = info.get('last_heartbeat') or info.get('opened_at') or 0
        if time.time() - last_seen < REMOTE_STALE_SECONDS:
            result['locked'] = True
        else:
            result['stale'] = True

    return result


def acquire_lock(db_path: str) -> None:
    """Write/refresh the advisory lock for db_path to point at this process."""
    lock_file = _lock_file_for(db_path)
    info = {
        'db_path': os.path.abspath(db_path),
        'pid': os.getpid(),
        'hostname': socket.gethostname(),
        'opened_at': time.time(),
        'last_heartbeat': time.time(),
    }
    try:
        lock_file.write_text(json.dumps(info))
    except Exception as exc:
        logger.warning(f'Failed to write instance lock for {db_path}: {exc}')


def refresh_lock(db_path: str) -> None:
    """Update the heartbeat timestamp for a lock already held by this process.

    Throttled to avoid hammering the lock file (particularly over network
    drives) when called from a hot path like per-request middleware.
    """
    abs_path = os.path.abspath(db_path)
    now = time.time()
    last = _last_heartbeat_write.get(abs_path, 0)
    if now - last < _HEARTBEAT_MIN_INTERVAL:
        return
    _last_heartbeat_write[abs_path] = now

    lock_file = _lock_file_for(db_path)
    if not lock_file.exists():
        acquire_lock(db_path)
        return
    try:
        info = json.loads(lock_file.read_text())
        if info.get('pid') == os.getpid() and info.get('hostname') == socket.gethostname():
            info['last_heartbeat'] = now
            lock_file.write_text(json.dumps(info))
        else:
            # Someone else owns the lock file now; don't stomp on it.
            pass
    except Exception:
        acquire_lock(db_path)


def release_lock(db_path: str) -> None:
    """Remove the advisory lock if it belongs to this process."""
    lock_file = _lock_file_for(db_path)
    if not lock_file.exists():
        return
    try:
        info = json.loads(lock_file.read_text())
        if info.get('pid') == os.getpid() and info.get('hostname') == socket.gethostname():
            lock_file.unlink()
    except Exception:
        pass


def force_clear_lock(db_path: str) -> None:
    """Unconditionally remove the lock file (explicit user override)."""
    lock_file = _lock_file_for(db_path)
    try:
        if lock_file.exists():
            lock_file.unlink()
    except Exception:
        pass


def release_all_locks_for_this_process() -> None:
    """Release every advisory lock owned by the current PID/host.

    Intended to be called on clean process shutdown (e.g. via atexit) so
    locks don't linger needlessly, even though stale locks are also
    self-healing via the PID-liveness check in check_lock().
    """
    try:
        lock_dir = _lock_dir()
    except Exception:
        return

    hostname = socket.gethostname()
    pid = os.getpid()

    for lock_file in lock_dir.glob('*.json'):
        try:
            info = json.loads(lock_file.read_text())
            if info.get('pid') == pid and info.get('hostname') == hostname:
                lock_file.unlink()
        except Exception:
            continue
