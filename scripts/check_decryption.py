#!/usr/bin/env python3
"""
Read-only check: can every encrypted value in a database be decrypted with the
keys currently configured in the environment / .env?

Usage (from the project root):
    python scripts/check_decryption.py <path_to_database> [--company-id N]

For each encrypted cell it reports one of:
    ok(confidential) / ok(ned_team)  - decrypts with that key
    FAIL                             - decrypts with neither key (wrong key, or not an encrypted value)
Plaintext is never printed. The database is opened read-only.
"""
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken

load_dotenv(override=False)

# table -> (id column, [encrypted columns])
TABLES = {
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


def fingerprint(key: str) -> str:
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()[:8]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        sys.exit(1)
    db_path = os.path.abspath(args[0])
    company_filter = None
    if '--company-id' in sys.argv:
        company_filter = int(sys.argv[sys.argv.index('--company-id') + 1])

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

    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    totals = {'ok': 0, 'fail': 0}
    for table, (id_col, cols) in TABLES.items():
        if table not in existing:
            continue
        have = {r[1] for r in conn.execute(f'PRAGMA table_info({table})')}
        cols = [c for c in cols if c in have]
        if not cols:
            continue
        where = ''
        params = ()
        if company_filter is not None and table == 'roundtable_history':
            where = " WHERE entity_type='Company' AND entity_id=?"
            params = (company_filter,)
        elif company_filter is not None and table == 'client_profiles':
            where = ' WHERE company_id=?'
            params = (company_filter,)
        elif company_filter is not None:
            continue

        print(f'\n[{table}]')
        for row in conn.execute(f'SELECT {id_col}, {", ".join(cols)} FROM {table}{where}', params):
            rid, values = row[0], row[1:]
            for col, value in zip(cols, values):
                if value is None or value == b'':
                    continue
                data = value if isinstance(value, bytes) else str(value).encode()
                result = None
                for name, cipher in ciphers.items():
                    try:
                        cipher.decrypt(data)
                        result = name
                        break
                    except InvalidToken:
                        pass
                if result:
                    totals['ok'] += 1
                else:
                    totals['fail'] += 1
                    kind = 'looks like plaintext' if not data.startswith(b'gAAAA') else 'Fernet token, wrong key'
                    print(f'  FAIL  {id_col}={rid}  {col}  ({kind})')

    print(f"\nSummary: {totals['ok']} decrypted OK, {totals['fail']} failed.")
    sys.exit(0 if totals['fail'] == 0 else 3)


if __name__ == '__main__':
    main()
