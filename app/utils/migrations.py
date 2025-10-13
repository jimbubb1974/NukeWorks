"""
Database Migration System
Implements versioned schema migrations following docs/07_MIGRATION_SYSTEM.md
"""
import os
import re
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Raised when migration fails"""
    pass


class ValidationError(Exception):
    """Raised when migration validation fails"""
    pass


# Application version and required schema version
APPLICATION_VERSION = "1.0.0"
APPLICATION_REQUIRED_SCHEMA_VERSION = 12  # Updated for complete legacy table cleanup


def get_migrations_directory():
    """Get path to migrations directory"""
    base_dir = Path(__file__).parent.parent.parent
    return base_dir / 'migrations'


def get_current_schema_version(db_path):
    """
    Get the current schema version from the database
    Returns 0 if Schema_Version table doesn't exist (new database)
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("""
            SELECT MAX(version) as current_version
            FROM schema_version
        """)
        result = cursor.fetchone()
        conn.close()

        return result[0] if result and result[0] else 0

    except sqlite3.OperationalError:
        # Schema_Version table doesn't exist - this is a new database
        return 0


def get_required_schema_version():
    """
    Get the required schema version for this application version
    """
    return APPLICATION_REQUIRED_SCHEMA_VERSION


def parse_migration_filename(filename):
    """
    Parse migration filename to extract version and description

    Args:
        filename: e.g., "001_initial_schema.sql"

    Returns:
        tuple: (version, description) e.g., (1, "initial schema")
    """
    match = re.match(r'(\d+)_(.+)\.sql', filename)
    if not match:
        raise ValueError(f"Invalid migration filename format: {filename}")

    version = int(match.group(1))
    description = match.group(2).replace('_', ' ')

    return version, description


def find_migration_file(version):
    """
    Find migration file for specific version

    Args:
        version: Schema version number

    Returns:
        str: Migration filename or None if not found
    """
    migrations_dir = get_migrations_directory()

    # Look for file matching pattern: {version:03d}_*.sql
    pattern = f"{version:03d}_*.sql"

    for filename in os.listdir(migrations_dir):
        if re.match(f"{version:03d}_.*\\.sql", filename):
            return filename

    return None


def get_pending_migrations(current_version, required_version):
    """
    Get list of migrations that need to be applied

    Returns:
        List of migration files in order: ['002_add_feature.sql', '003_add_field.sql']
    """
    if current_version >= required_version:
        return []

    pending = []

    for version in range(current_version + 1, required_version + 1):
        migration_file = find_migration_file(version)

        if not migration_file:
            raise MigrationError(f"Missing migration file for version {version}")

        pending.append(migration_file)

    return pending


def validate_migration_sql(migration_sql):
    """
    Validate migration SQL before executing
    Checks for common issues
    """
    # Check for transaction wrapper
    if 'BEGIN TRANSACTION' not in migration_sql.upper():
        raise ValidationError("Migration must contain BEGIN TRANSACTION")

    if 'COMMIT' not in migration_sql.upper():
        raise ValidationError("Migration must contain COMMIT")

    # Check for Schema_Version update
    if 'schema_version' not in migration_sql.lower():
        raise ValidationError("Migration must update schema_version table")

    # Check for dangerous operations (optional warning)
    if 'DROP TABLE' in migration_sql.upper():
        logger.warning("Migration contains DROP TABLE - ensure data is backed up")

    if 'DELETE FROM' in migration_sql.upper():
        logger.warning("Migration contains DELETE - ensure this is intentional")


def apply_single_migration(db_path, migration_file):
    """
    Apply a single migration file
    Migration file must contain BEGIN TRANSACTION and COMMIT
    """
    # Read migration SQL
    migrations_dir = get_migrations_directory()
    migration_path = migrations_dir / migration_file

    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    # Validate migration SQL
    validate_migration_sql(migration_sql)

    # Check if migration explicitly disables foreign keys
    disable_fk = 'PRAGMA foreign_keys = OFF' in migration_sql.upper()

    # Execute migration
    conn = sqlite3.connect(db_path)

    try:
        # Enable foreign keys unless migration explicitly disables them
        if not disable_fk:
            conn.execute("PRAGMA foreign_keys = ON")

        # Execute the migration
        # Note: Migration file contains BEGIN TRANSACTION and COMMIT
        conn.executescript(migration_sql)

        conn.close()

    except Exception as e:
        conn.close()
        raise e


def create_migration_backup(db_path):
    """
    Create backup before applying migrations
    Separate from regular automated backups
    """
    from config import get_config

    config = get_config()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"migration_backup_{timestamp}.sqlite"

    # Get snapshot directory from config
    snapshot_dir = Path(config.SNAPSHOT_DIR)
    snapshot_dir.mkdir(exist_ok=True)

    backup_path = snapshot_dir / backup_filename

    # Copy database file
    shutil.copy2(db_path, backup_path)

    logger.info(f"Created migration backup: {backup_path}")

    return str(backup_path)


def restore_from_backup(db_path, backup_path):
    """
    Restore database from backup
    """
    if not os.path.exists(backup_path):
        raise MigrationError(f"Backup file not found: {backup_path}")

    # Copy backup over current database
    shutil.copy2(backup_path, db_path)

    logger.info(f"Restored database from backup: {backup_path}")


def apply_migrations(db_path, migration_files):
    """
    Apply a list of migrations in sequence
    Creates backup before starting
    Rolls back if any migration fails
    """
    backup_path = None

    try:
        # Step 1: Create backup
        logger.info("Creating backup before migration...")
        backup_path = create_migration_backup(db_path)
        logger.info(f"Backup created: {backup_path}")

        # Step 2: Apply each migration
        for migration_file in migration_files:
            logger.info(f"Applying migration: {migration_file}")

            try:
                apply_single_migration(db_path, migration_file)
                logger.info(f"Successfully applied: {migration_file}")

            except Exception as e:
                logger.error(f"Migration failed: {migration_file}")
                logger.error(f"Error: {str(e)}")

                # Rollback: restore from backup
                logger.info("Rolling back changes...")
                restore_from_backup(db_path, backup_path)

                raise MigrationError(f"Migration {migration_file} failed: {str(e)}")

        # Step 3: Verify final version
        final_version = get_current_schema_version(db_path)
        required_version = get_required_schema_version()

        if final_version != required_version:
            raise MigrationError(
                f"Version mismatch after migration. Expected {required_version}, got {final_version}"
            )

        logger.info("All migrations applied successfully")
        return backup_path

    except MigrationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during migration: {str(e)}")
        raise MigrationError(f"Migration failed: {str(e)}")


def check_and_apply_migrations(db_path, interactive=True):
    """
    Called on application startup
    Checks for pending migrations and applies them if needed

    Args:
        db_path: Path to database file
        interactive: If True, prompt user for confirmation (GUI mode)
                    If False, apply automatically (CLI mode)

    Returns:
        bool: True if successful, False if failed or user cancelled
    """
    try:
        # Get current and required versions
        current_version = get_current_schema_version(db_path)
        required_version = get_required_schema_version()

        logger.info(f"Current schema version: {current_version}")
        logger.info(f"Required schema version: {required_version}")

        # Check version compatibility
        if current_version == required_version:
            logger.info("Schema is up to date")
            return True

        elif current_version > required_version:
            # Database is newer than application
            error_msg = (
                f"This database (version {current_version}) is newer than this application version "
                f"(requires version {required_version}).\n\n"
                f"Please update the application to the latest version."
            )
            logger.error(error_msg)

            if interactive:
                # In GUI mode, would show error dialog
                print(f"ERROR: {error_msg}")

            return False

        else:
            # Pending migrations exist
            pending_migrations = get_pending_migrations(current_version, required_version)

            logger.info(f"Found {len(pending_migrations)} pending migration(s)")

            if interactive:
                # In GUI mode, would show confirmation dialog
                print(f"\nDatabase update required:")
                print(f"  Current version: {current_version}")
                print(f"  Required version: {required_version}")
                print(f"\nPending migrations:")

                for migration_file in pending_migrations:
                    version, description = parse_migration_filename(migration_file)
                    print(f"  • Version {version}: {description}")

                print(f"\nA backup will be created before updating.")

                response = input("\nApply migrations? (yes/no): ").strip().lower()

                if response != 'yes':
                    logger.info("User cancelled migration")
                    return False

            # Apply migrations
            backup_path = apply_migrations(db_path, pending_migrations)

            print(f"\n[SUCCESS] Database updated successfully!")
            print(f"  Backup location: {backup_path}")

            return True

    except Exception as e:
        logger.error(f"Migration check failed: {str(e)}")
        print(f"\n[ERROR] Migration error: {str(e)}")
        return False


def get_schema_version_info(db_path):
    """
    Get detailed schema version information

    Returns:
        dict with current_version and migration_history
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT version, applied_date, applied_by, description
            FROM schema_version
            ORDER BY version
        """)

        history = [dict(row) for row in cursor.fetchall()]

        current_version = history[-1]['version'] if history else 0

        conn.close()

        return {
            'current_version': current_version,
            'migration_history': history
        }

    except sqlite3.OperationalError:
        # Schema_Version table doesn't exist
        return {
            'current_version': 0,
            'migration_history': []
        }


def verify_database_integrity(db_path):
    """
    Run SQLite integrity checks on database
    """
    conn = sqlite3.connect(db_path)

    # Run integrity check
    cursor = conn.execute("PRAGMA integrity_check")
    result = cursor.fetchone()[0]

    if result != "ok":
        conn.close()
        raise MigrationError(f"Database integrity check failed: {result}")

    # Check foreign key constraints
    cursor = conn.execute("PRAGMA foreign_key_check")
    violations = cursor.fetchall()

    conn.close()

    if violations:
        raise MigrationError(f"Foreign key violations found: {violations}")

    logger.info("Database integrity check passed")
    return True
