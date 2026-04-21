#!/usr/bin/env python3
"""
Run database migrations on a specific database file (non-interactive)
Usage: python run_migrations_auto.py <path_to_database>
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.migrations import (
    get_current_schema_version,
    get_required_schema_version,
    get_pending_migrations,
    apply_migrations,
    parse_migration_filename
)

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_migrations_auto.py <path_to_database>")
        sys.exit(1)

    db_path = sys.argv[1]

    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        sys.exit(1)

    print(f"Running migrations on: {db_path}\n")

    try:
        # Get current and required versions
        current_version = get_current_schema_version(db_path)
        required_version = get_required_schema_version()

        print(f"Current schema version: {current_version}")
        print(f"Required schema version: {required_version}\n")

        if current_version == required_version:
            print("Schema is already up to date!")
            sys.exit(0)

        elif current_version > required_version:
            print(f"ERROR: Database version ({current_version}) is newer than application version ({required_version})")
            print("Please update the application to the latest version.")
            sys.exit(1)

        # Get pending migrations
        pending_migrations = get_pending_migrations(current_version, required_version)

        print(f"Found {len(pending_migrations)} pending migration(s):\n")
        for migration_file in pending_migrations:
            version, description = parse_migration_filename(migration_file)
            print(f"  • Version {version}: {description}")

        print(f"\nA backup will be created before updating.\n")
        print("Applying migrations...")

        # Apply migrations
        backup_path = apply_migrations(db_path, pending_migrations)

        print(f"\n[SUCCESS] Database updated successfully!")
        print(f"  New version: {get_current_schema_version(db_path)}")
        print(f"  Backup location: {backup_path}")

        sys.exit(0)

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
