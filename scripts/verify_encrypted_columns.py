#!/usr/bin/env python3
"""
Verify that encrypted columns exist in database
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text


def verify_columns(db_path):
    """Verify encrypted columns exist"""

    print("=" * 70)
    print("VERIFYING ENCRYPTED COLUMNS")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()

    engine = create_engine(f'sqlite:///{db_path}')

    expected_columns = {
        'projects': ['capex_encrypted', 'opex_encrypted', 'fuel_cost_encrypted', 'lcoe_encrypted'],
        'client_profiles': ['relationship_strength_encrypted', 'relationship_notes_encrypted',
                           'client_priority_encrypted', 'client_status_encrypted'],
        'roundtable_history': ['discussion_encrypted', 'action_items_encrypted', 'next_steps_encrypted',
                              'client_near_term_focus_encrypted', 'mpr_work_targets_encrypted'],
        'company_role_assignments': ['notes_encrypted'],
        'internal_external_links': ['relationship_strength_encrypted', 'notes_encrypted'],
    }

    all_good = True

    with engine.connect() as conn:
        for table, columns in expected_columns.items():
            print(f"\n[TABLE] {table}")

            # Get table info
            result = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            existing_columns = [row[1] for row in result]

            for col in columns:
                if col in existing_columns:
                    print(f"  [OK] {col}")
                else:
                    print(f"  [MISSING] {col}")
                    all_good = False

    print("\n" + "=" * 70)
    if all_good:
        print("[SUCCESS] All encrypted columns exist!")
        print("\nYour database is ready for encrypted data.")
        print("\nYou can now:")
        print("1. Restart your Flask application (python app.py)")
        print("2. The application should work without errors")
        print("3. New data will be automatically encrypted")
        print("4. Existing plain-text data can be migrated later with:")
        print(f"   python scripts/migrate_data_to_encrypted.py {db_path}")
    else:
        print("[ERROR] Some columns are missing!")
    print("=" * 70)

    return all_good


if __name__ == '__main__':
    import sys
    import os

    db_path = sys.argv[1] if len(sys.argv) > 1 else 'databases/development/nukeworks.sqlite'

    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        sys.exit(1)

    success = verify_columns(db_path)
    sys.exit(0 if success else 1)
