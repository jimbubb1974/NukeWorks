#!/usr/bin/env python3
"""
Add missing encrypted columns
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text


def add_missing_columns(db_path):
    """Add any missing encrypted columns"""

    print("=" * 70)
    print("ADDING MISSING ENCRYPTED COLUMNS")
    print("=" * 70)

    engine = create_engine(f'sqlite:///{db_path}')

    columns_to_add = [
        ('projects', 'capex_encrypted', 'BLOB'),
        ('client_profiles', 'relationship_strength_encrypted', 'BLOB'),
        ('roundtable_history', 'discussion_encrypted', 'BLOB'),
        ('company_role_assignments', 'notes_encrypted', 'BLOB'),
        ('internal_external_links', 'relationship_strength_encrypted', 'BLOB'),
    ]

    with engine.begin() as conn:
        for table, column, col_type in columns_to_add:
            try:
                print(f"[ADD] {table}.{column}")
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                print(f"  [OK] Added successfully")
            except Exception as e:
                if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                    print(f"  [SKIP] Already exists")
                else:
                    print(f"  [ERROR] {e}")
                    raise

    print("\n[SUCCESS] All missing columns added!")
    return True


if __name__ == '__main__':
    import os

    db_path = sys.argv[1] if len(sys.argv) > 1 else 'databases/development/nukeworks.sqlite'

    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        sys.exit(1)

    add_missing_columns(db_path)
