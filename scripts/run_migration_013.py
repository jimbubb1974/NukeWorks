#!/usr/bin/env python3
"""
Run Migration 013: Add Encrypted Columns
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text


def run_migration(db_path):
    """Run migration 013 on a database"""

    # Read migration SQL
    migration_file = Path(__file__).parent.parent / 'migrations' / '013_add_encrypted_columns.sql'

    if not migration_file.exists():
        print(f"[ERROR] Migration file not found: {migration_file}")
        return False

    with open(migration_file, 'r') as f:
        sql = f.read()

    # Split into individual statements
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

    print("=" * 70)
    print("RUNNING MIGRATION 013: Add Encrypted Columns")
    print("=" * 70)
    print(f"Database: {db_path}")
    print(f"Statements to execute: {len(statements)}")
    print()

    # Create engine
    engine = create_engine(f'sqlite:///{db_path}')

    try:
        with engine.begin() as conn:
            for i, statement in enumerate(statements, 1):
                # Skip comments
                if statement.startswith('--'):
                    continue

                try:
                    print(f"[{i}/{len(statements)}] Executing: {statement[:60]}...")
                    conn.execute(text(statement))
                except Exception as e:
                    # Check if error is "duplicate column" (already exists)
                    if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                        print(f"  [SKIP] Column already exists (safe to ignore)")
                    else:
                        print(f"  [ERROR] {e}")
                        raise

            print("\n[COMMIT] All statements executed successfully")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        return False

    print("\n" + "=" * 70)
    print("[SUCCESS] Migration 013 completed successfully!")
    print("=" * 70)
    print()
    print("Encrypted columns added:")
    print("  - projects: capex_encrypted, opex_encrypted, fuel_cost_encrypted, lcoe_encrypted")
    print("  - client_profiles: relationship_strength_encrypted, relationship_notes_encrypted, ...")
    print("  - roundtable_history: discussion_encrypted, action_items_encrypted, ...")
    print("  - company_role_assignments: notes_encrypted")
    print("  - internal_external_links: relationship_strength_encrypted, notes_encrypted")
    print()
    print("Next steps:")
    print("1. Restart the Flask application")
    print("2. The app should now work without errors")
    print("3. Run data migration to encrypt existing data:")
    print(f"   python scripts/migrate_data_to_encrypted.py {db_path}")
    print()

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run migration 013')
    parser.add_argument('database', nargs='?',
                       default='databases/development/nukeworks.sqlite',
                       help='Path to database file')

    args = parser.parse_args()

    if not os.path.exists(args.database):
        print(f"[ERROR] Database not found: {args.database}")
        sys.exit(1)

    success = run_migration(args.database)
    sys.exit(0 if success else 1)
