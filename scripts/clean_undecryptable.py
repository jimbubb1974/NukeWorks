#!/usr/bin/env python3
"""
Remove encrypted values that cannot be decrypted with the keys currently
configured (environment / .env). Use this when data was written with a
different set of keys and the original key is unrecoverable.

Usage (from the project root):
    python scripts/clean_undecryptable.py <path_to_database>            # dry run, changes nothing
    python scripts/clean_undecryptable.py <path_to_database> --apply    # backs up, then cleans

What --apply does, in order:
  1. Copies the database to <name>.pre_cleanup_<timestamp> (SQLite online backup).
  2. roundtable_history: a row where EVERY non-empty encrypted field fails is deleted;
     a row where only SOME fields fail has just those fields set to NULL.
  3. Every other table: failing encrypted fields are set to NULL.
  4. Re-scans; if clean, records the current key fingerprint in system_settings so the
     app accepts this machine's keys for this database.

DELETION IS PERMANENT (apart from the backup). Make sure nobody else has the app open.
Plaintext is never printed.
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken

from check_decryption import TABLES, fingerprint

load_dotenv(override=False)

SETTING_NAME = 'encryption_key_fingerprint'


def combined_fingerprint(keys):
    return f"conf:{fingerprint(keys['confidential'])};ned:{fingerprint(keys['ned_team'])}"


def decrypts(ciphers, value):
    data = value if isinstance(value, bytes) else str(value).encode()
    for cipher in ciphers.values():
        try:
            cipher.decrypt(data)
            return True
        except InvalidToken:
            continue
    return False


def scan(conn, ciphers):
    """Return {table: [(row_id, [failing cols], [ok cols])]} for rows with any failure."""
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    problems = {}
    for table, (id_col, cols) in TABLES.items():
        if table not in existing:
            continue
        have = {r[1] for r in conn.execute(f'PRAGMA table_info({table})')}
        cols = [c for c in cols if c in have]
        if not cols:
            continue
        for row in conn.execute(f'SELECT {id_col}, {", ".join(cols)} FROM {table}'):
            rid, values = row[0], row[1:]
            failing, ok = [], []
            for col, value in zip(cols, values):
                if value is None or value == b'':
                    continue
                (ok if decrypts(ciphers, value) else failing).append(col)
            if failing:
                problems.setdefault(table, []).append((rid, failing, ok))
    return problems


def describe(conn, table, rid):
    if table != 'roundtable_history':
        return ''
    row = conn.execute(
        'SELECT entity_type, entity_id, created_timestamp FROM roundtable_history WHERE history_id=?',
        (rid,),
    ).fetchone()
    if not row:
        return ''
    name = ''
    if row[0] == 'Company':
        c = conn.execute('SELECT company_name FROM companies WHERE company_id=?', (row[1],)).fetchone()
        name = f' "{c[0]}"' if c else ''
    return f'  [{row[0]} {row[1]}{name}, created {row[2]}]'


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apply_changes = '--apply' in sys.argv
    if not args:
        print(__doc__)
        sys.exit(1)

    db_path = os.path.abspath(args[0])
    if os.path.isdir(db_path):
        print(f'That path is a folder, not a database file: {db_path}')
        sys.exit(1)
    if not os.path.isfile(db_path):
        print(f'Database file not found: {db_path}')
        sys.exit(1)

    keys = {
        'confidential': os.environ.get('CONFIDENTIAL_DATA_KEY'),
        'ned_team': os.environ.get('NED_TEAM_KEY'),
    }
    for name, key in keys.items():
        print(f'{name:13s} key: ' + (f'set (fingerprint {fingerprint(key)})' if key else 'MISSING'))
    if not all(keys.values()):
        print('\nSet both keys (environment or .env) and retry.')
        sys.exit(2)
    ciphers = {name: Fernet(key.encode()) for name, key in keys.items()}

    mode = 'APPLY' if apply_changes else 'DRY RUN (no changes will be made)'
    print(f'\nMode: {mode}\nDatabase: {db_path}\n')

    if apply_changes:
        conn = sqlite3.connect(db_path, timeout=30)
    else:
        conn = sqlite3.connect(f'{Path(db_path).as_uri()}?mode=ro', uri=True)

    problems = scan(conn, ciphers)
    if not problems:
        print('Nothing to clean: every encrypted value decrypts with the current keys.')
        if apply_changes:
            stamp(conn, keys)
            conn.close()
        sys.exit(0)

    plan = []  # (action, table, id_col, rid, cols)
    for table, rows in problems.items():
        id_col = TABLES[table][0]
        print(f'[{table}]')
        for rid, failing, ok in rows:
            if table == 'roundtable_history' and not ok:
                plan.append(('delete', table, id_col, rid, failing))
                print(f'  DELETE row {id_col}={rid} (all {len(failing)} encrypted fields unreadable){describe(conn, table, rid)}')
            else:
                plan.append(('null', table, id_col, rid, failing))
                print(f'  CLEAR  row {id_col}={rid}: {", ".join(failing)}{describe(conn, table, rid)}')
    print(f'\n{len(plan)} row(s) affected.')

    if not apply_changes:
        print('Dry run only. Re-run with --apply to back up and clean.')
        conn.close()
        sys.exit(0)

    backup_path = f'{db_path}.pre_cleanup_{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    dest = sqlite3.connect(backup_path)
    with dest:
        conn.backup(dest)
    dest.close()
    print(f'\nBackup written: {backup_path}')

    with conn:
        for action, table, id_col, rid, cols in plan:
            if action == 'delete':
                conn.execute(f'DELETE FROM {table} WHERE {id_col}=?', (rid,))
            else:
                sets = ', '.join(f'{c}=NULL' for c in cols)
                conn.execute(f'UPDATE {table} SET {sets} WHERE {id_col}=?', (rid,))

    remaining = scan(conn, ciphers)
    if remaining:
        print('\nWARNING: some values still fail after cleanup:')
        for table, rows in remaining.items():
            for rid, failing, _ in rows:
                print(f'  {table} {TABLES[table][0]}={rid}: {", ".join(failing)}')
        conn.close()
        sys.exit(3)

    print('Re-scan clean: every remaining encrypted value decrypts.')
    stamp(conn, keys)
    conn.close()


def stamp(conn, keys):
    """Record this machine's key fingerprint in system_settings (if that table exists)."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'system_settings' not in tables:
        print('system_settings table not found; skipped recording key fingerprint.')
        return
    value = combined_fingerprint(keys)
    with conn:
        row = conn.execute('SELECT setting_id FROM system_settings WHERE setting_name=?', (SETTING_NAME,)).fetchone()
        if row:
            conn.execute(
                'UPDATE system_settings SET setting_value=?, modified_date=? WHERE setting_name=?',
                (value, datetime.now().isoformat(sep=' '), SETTING_NAME),
            )
        else:
            conn.execute(
                'INSERT INTO system_settings (setting_name, setting_value, setting_type, description, modified_date) '
                'VALUES (?, ?, ?, ?, ?)',
                (SETTING_NAME, value, 'text',
                 'Fingerprint of the encryption keys this database was written with',
                 datetime.now().isoformat(sep=' ')),
            )
    print(f'Recorded key fingerprint: {value}')


if __name__ == '__main__':
    main()
