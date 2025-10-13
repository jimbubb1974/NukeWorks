#!/usr/bin/env python3
"""
Run database migrations on a specific database file
Usage: python run_migrations.py <path_to_database>
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.migrations import check_and_apply_migrations

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_migrations.py <path_to_database>")
        sys.exit(1)

    db_path = sys.argv[1]

    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        sys.exit(1)

    print(f"Running migrations on: {db_path}\n")

    success = check_and_apply_migrations(db_path, interactive=True)

    if success:
        print("\nMigrations completed successfully!")
        sys.exit(0)
    else:
        print("\nMigrations failed or were cancelled.")
        sys.exit(1)

if __name__ == '__main__':
    main()
