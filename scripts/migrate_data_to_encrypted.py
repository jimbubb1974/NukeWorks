#!/usr/bin/env python3
"""
Migrate Existing Data to Encrypted Columns

This script:
1. Reads plain text values from original columns
2. Encrypts them with appropriate keys
3. Stores encrypted data in new *_encrypted columns
4. Validates encryption worked correctly
5. Provides rollback option

IMPORTANT: Run migration 013 first to add encrypted columns!
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from app.utils.encryption import encrypt_confidential, encrypt_value
from app.utils.key_management import validate_encryption_keys


# Field mappings: (table, old_column, new_column, key_type)
FIELD_MIGRATIONS = [
    # Projects - Confidential Financial Data
    ('projects', 'capex', 'capex_encrypted', 'confidential'),
    ('projects', 'opex', 'opex_encrypted', 'confidential'),
    ('projects', 'fuel_cost', 'fuel_cost_encrypted', 'confidential'),
    ('projects', 'lcoe', 'lcoe_encrypted', 'confidential'),

    # ClientProfile - NED Team CRM Data
    ('client_profiles', 'relationship_strength', 'relationship_strength_encrypted', 'ned_team'),
    ('client_profiles', 'relationship_notes', 'relationship_notes_encrypted', 'ned_team'),
    ('client_profiles', 'client_priority', 'client_priority_encrypted', 'ned_team'),
    ('client_profiles', 'client_status', 'client_status_encrypted', 'ned_team'),

    # RoundtableHistory - NED Team Meeting Notes
    ('roundtable_history', 'discussion', 'discussion_encrypted', 'ned_team'),
    ('roundtable_history', 'action_items', 'action_items_encrypted', 'ned_team'),
    ('roundtable_history', 'next_steps', 'next_steps_encrypted', 'ned_team'),
    ('roundtable_history', 'client_near_term_focus', 'client_near_term_focus_encrypted', 'ned_team'),
    ('roundtable_history', 'mpr_work_targets', 'mpr_work_targets_encrypted', 'ned_team'),

    # CompanyRoleAssignment - Confidential Notes
    ('company_role_assignments', 'notes', 'notes_encrypted', 'confidential'),

    # InternalExternalLink - NED Team Relationship Data
    ('internal_external_links', 'relationship_strength', 'relationship_strength_encrypted', 'ned_team'),
    ('internal_external_links', 'notes', 'notes_encrypted', 'ned_team'),
]


def check_encrypted_columns_exist(engine):
    """
    Check that all encrypted columns exist in database

    Returns:
        bool: True if all columns exist
    """
    print("\n" + "=" * 70)
    print("CHECKING ENCRYPTED COLUMNS EXIST")
    print("=" * 70)

    with engine.connect() as conn:
        missing_columns = []

        for table, old_col, new_col, key_type in FIELD_MIGRATIONS:
            # Check if encrypted column exists
            result = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            columns = [row[1] for row in result]

            if new_col not in columns:
                missing_columns.append(f"{table}.{new_col}")
                print(f"[MISSING] {table}.{new_col}")
            else:
                print(f"[OK] {table}.{new_col} exists")

    if missing_columns:
        print(f"\n[ERROR] Missing {len(missing_columns)} encrypted columns!")
        print("Please run migration 013_add_encrypted_columns.sql first")
        return False

    print("\n[SUCCESS] All encrypted columns exist")
    return True


def migrate_field(conn, table, old_column, new_column, key_type):
    """
    Migrate data from old column to encrypted column

    Args:
        conn: Database connection
        table: Table name
        old_column: Source column name
        new_column: Destination encrypted column name
        key_type: 'confidential' or 'ned_team'

    Returns:
        dict: Migration statistics
    """
    # Get primary key column name
    pk_result = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    pk_column = None
    for row in pk_result:
        if row[5] == 1:  # pk column is at index 5
            pk_column = row[1]
            break

    if not pk_column:
        raise ValueError(f"Could not find primary key for table {table}")

    # Get all records with non-null values in old column
    query = f"SELECT {pk_column}, {old_column} FROM {table} WHERE {old_column} IS NOT NULL"
    records = conn.execute(text(query)).fetchall()

    encrypted_count = 0
    skipped_count = 0
    error_count = 0

    for record in records:
        pk_value = record[0]
        plain_value = record[1]

        if plain_value is None or str(plain_value).strip() == '':
            skipped_count += 1
            continue

        try:
            # Encrypt the value
            encrypted_bytes = encrypt_value(str(plain_value), key_type)

            # Store in encrypted column
            update_query = f"""
                UPDATE {table}
                SET {new_column} = :encrypted_value
                WHERE {pk_column} = :pk_value
            """
            conn.execute(
                text(update_query),
                {'encrypted_value': encrypted_bytes, 'pk_value': pk_value}
            )

            encrypted_count += 1

        except Exception as e:
            print(f"  [ERROR] Failed to encrypt {table}.{pk_column}={pk_value}: {e}")
            error_count += 1

    return {
        'total': len(records),
        'encrypted': encrypted_count,
        'skipped': skipped_count,
        'errors': error_count
    }


def migrate_all_fields(engine, dry_run=False):
    """
    Migrate all fields to encrypted columns

    Args:
        engine: SQLAlchemy engine
        dry_run: If True, don't commit changes

    Returns:
        bool: True if successful
    """
    print("\n" + "=" * 70)
    print("MIGRATING DATA TO ENCRYPTED COLUMNS")
    if dry_run:
        print("DRY RUN MODE - No changes will be committed")
    print("=" * 70)

    total_stats = {
        'total': 0,
        'encrypted': 0,
        'skipped': 0,
        'errors': 0
    }

    with engine.begin() as conn:
        for table, old_col, new_col, key_type in FIELD_MIGRATIONS:
            print(f"\n[MIGRATING] {table}.{old_col} -> {new_col} (key={key_type})")

            stats = migrate_field(conn, table, old_col, new_col, key_type)

            print(f"  Total records: {stats['total']}")
            print(f"  Encrypted: {stats['encrypted']}")
            print(f"  Skipped (empty): {stats['skipped']}")
            print(f"  Errors: {stats['errors']}")

            # Update totals
            for key in total_stats:
                total_stats[key] += stats[key]

        if dry_run:
            print("\n[DRY RUN] Rolling back transaction (no changes committed)")
            conn.rollback()
        else:
            print("\n[COMMIT] Committing transaction")
            # Transaction auto-commits when using engine.begin()

    print("\n" + "=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    print(f"Total records processed: {total_stats['total']}")
    print(f"Successfully encrypted: {total_stats['encrypted']}")
    print(f"Skipped (empty values): {total_stats['skipped']}")
    print(f"Errors: {total_stats['errors']}")

    if total_stats['errors'] > 0:
        print("\n[WARNING] Some records failed to encrypt")
        return False

    if not dry_run:
        print("\n[SUCCESS] All data migrated successfully!")
    else:
        print("\n[DRY RUN COMPLETE] No changes were committed")

    return True


def validate_encryption(engine):
    """
    Validate that encrypted data can be decrypted

    Args:
        engine: SQLAlchemy engine

    Returns:
        bool: True if validation passes
    """
    print("\n" + "=" * 70)
    print("VALIDATING ENCRYPTED DATA")
    print("=" * 70)

    from app.utils.encryption import decrypt_value

    with engine.connect() as conn:
        validation_errors = []

        # Sample validate: check first 5 encrypted records from each table
        for table, old_col, new_col, key_type in FIELD_MIGRATIONS[:5]:  # Just validate first 5 for speed
            query = f"SELECT {new_col} FROM {table} WHERE {new_col} IS NOT NULL LIMIT 5"
            records = conn.execute(text(query)).fetchall()

            for record in records:
                encrypted_bytes = record[0]

                try:
                    decrypted_value = decrypt_value(encrypted_bytes, key_type)
                    print(f"[OK] {table}.{new_col}: Decrypted successfully")
                except Exception as e:
                    error_msg = f"{table}.{new_col}: Decryption failed - {e}"
                    validation_errors.append(error_msg)
                    print(f"[ERROR] {error_msg}")

    if validation_errors:
        print(f"\n[FAILURE] {len(validation_errors)} validation errors")
        return False

    print("\n[SUCCESS] All sampled encrypted data can be decrypted")
    return True


def main():
    """Run the migration"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate data to encrypted columns')
    parser.add_argument('database', help='Path to database file')
    parser.add_argument('--dry-run', action='store_true', help='Run without committing changes')
    parser.add_argument('--skip-validation', action='store_true', help='Skip encrypted data validation')

    args = parser.parse_args()

    if not os.path.exists(args.database):
        print(f"[ERROR] Database file not found: {args.database}")
        return 1

    print("=" * 70)
    print("NUKEWORKS DATA ENCRYPTION MIGRATION")
    print("=" * 70)
    print(f"Database: {args.database}")
    print(f"Dry run: {args.dry_run}")
    print(f"Skip validation: {args.skip_validation}")

    # Validate encryption keys are loaded
    try:
        print("\n[STEP 1] Validating encryption keys...")
        validate_encryption_keys()
        print("[OK] Encryption keys valid")
    except Exception as e:
        print(f"[ERROR] Encryption keys invalid: {e}")
        print("Make sure CONFIDENTIAL_DATA_KEY and NED_TEAM_KEY are in .env file")
        return 1

    # Create engine
    engine = create_engine(f'sqlite:///{args.database}')

    # Check encrypted columns exist
    print("\n[STEP 2] Checking encrypted columns exist...")
    if not check_encrypted_columns_exist(engine):
        return 1

    # Migrate data
    print("\n[STEP 3] Migrating data to encrypted columns...")
    if not migrate_all_fields(engine, dry_run=args.dry_run):
        return 1

    # Validate encryption
    if not args.skip_validation and not args.dry_run:
        print("\n[STEP 4] Validating encrypted data...")
        if not validate_encryption(engine):
            return 1

    print("\n" + "=" * 70)
    if args.dry_run:
        print("[DRY RUN COMPLETE] Review results above")
        print("Run without --dry-run to apply changes")
    else:
        print("[MIGRATION COMPLETE]")
        print("Encrypted columns have been populated with encrypted data")
        print("\nNEXT STEPS:")
        print("1. Test application with encrypted models")
        print("2. Verify Joe sees [Confidential] for financial data")
        print("3. Verify Sally sees actual values")
        print("4. After validation, optionally drop old columns")
    print("=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
