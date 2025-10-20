"""
Database Helper Functions
Utilities for per-database operations and path derivation
"""
import os
from pathlib import Path
from typing import Optional
import sqlite3
import logging

logger = logging.getLogger(__name__)


def get_snapshot_dir_for_db(db_path: str) -> str:
    """
    Derive snapshot directory for a given database path

    For databases in structure: databases/<label>/nukeworks.sqlite
    Returns: databases/<label>/snapshots/

    For other paths, creates a snapshots/ directory next to the database file

    Args:
        db_path: Absolute path to database file

    Returns:
        str: Absolute path to snapshot directory
    """
    db_path = Path(db_path).resolve()
    parent_dir = db_path.parent

    # Check if in databases/<label>/ structure
    if parent_dir.parent.name == 'databases':
        snapshot_dir = parent_dir / 'snapshots'
    else:
        # Put snapshots next to database
        snapshot_dir = parent_dir / 'snapshots'

    # Ensure directory exists
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    return str(snapshot_dir)


def get_db_display_name(db_path: str) -> Optional[str]:
    """
    Get display name from database's system_settings table

    Args:
        db_path: Absolute path to database file

    Returns:
        str or None: Display name if set, None otherwise
    """
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.execute("""
            SELECT setting_value
            FROM system_settings
            WHERE setting_name = 'db_display_name'
        """)
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return result[0]

    except sqlite3.OperationalError as e:
        logger.warning(f"Could not read display name from {db_path}: {e}")

    return None


def set_db_display_name(db_path: str, display_name: str) -> bool:
    """
    Set display name in database's system_settings table

    Args:
        db_path: Absolute path to database file
        display_name: Friendly name for the database

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)

        # Check if setting exists
        cursor = conn.execute("""
            SELECT setting_id
            FROM system_settings
            WHERE setting_name = 'db_display_name'
        """)
        exists = cursor.fetchone()

        if exists:
            # Update existing
            conn.execute("""
                UPDATE system_settings
                SET setting_value = ?, modified_date = datetime('now')
                WHERE setting_name = 'db_display_name'
            """, (display_name,))
        else:
            # Insert new
            conn.execute("""
                INSERT INTO system_settings (setting_name, setting_value, setting_type, description, modified_date)
                VALUES ('db_display_name', ?, 'text', 'Friendly display name for this database', datetime('now'))
            """, (display_name,))

        conn.commit()
        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"Failed to set display name for {db_path}: {e}")
        return False


def scan_databases_directory() -> list:
    """
    Recursively scan databases/ directory for any *.sqlite files.

    Returns:
        list: List of dicts with keys: path, label, display_name
    """
    from config import get_config

    base_dir = Path(__file__).parent.parent.parent
    databases_dir = base_dir / 'databases'

    results = []

    if not databases_dir.exists():
        logger.warning(f"Databases directory does not exist: {databases_dir}")
        return results

    # Recursively walk and include any *.sqlite file
    for root, dirs, files in os.walk(databases_dir):
        # Exclude any snapshots directories from recursion
        dirs[:] = [d for d in dirs if d.lower() != 'snapshots']
        for fname in files:
            if fname.lower().endswith('.sqlite'):
                db_file = Path(root) / fname
                # Try to get display name from the DB
                display_name = get_db_display_name(str(db_file))
                if not display_name:
                    # Fall back to the directory name containing the DB, or filename if not under a label dir
                    display_name = Path(root).name or db_file.stem

                # Label is the immediate parent directory under databases/
                try:
                    rel = Path(root).resolve().relative_to(databases_dir.resolve())
                    label = rel.parts[0] if len(rel.parts) > 0 else databases_dir.name
                except Exception:
                    label = databases_dir.name

                results.append({
                    'path': str(db_file.resolve()),
                    'label': label,
                    'display_name': display_name
                })

    return sorted(results, key=lambda x: x['display_name'])


def validate_database_file(db_path: str) -> dict:
    """
    Validate that a file is a valid SQLite database

    Args:
        db_path: Path to database file

    Returns:
        dict with keys:
            - valid (bool): True if valid
            - error (str): Error message if not valid
            - schema_version (int): Schema version if valid
            - has_tables (bool): True if has expected tables
    """
    result = {
        'valid': False,
        'error': None,
        'schema_version': 0,
        'has_tables': False
    }

    # Check file exists
    if not os.path.exists(db_path):
        result['error'] = 'File does not exist'
        return result

    # Check file is readable
    if not os.access(db_path, os.R_OK):
        result['error'] = 'File is not readable'
        return result

    try:
        # Try to open as SQLite database
        conn = sqlite3.connect(db_path, timeout=5.0)

        # Check SQLite integrity
        cursor = conn.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()
        if integrity[0] != 'ok':
            result['error'] = f'Database integrity check failed: {integrity[0]}'
            conn.close()
            return result

        # Get schema version
        try:
            cursor = conn.execute("SELECT MAX(version) FROM schema_version")
            version = cursor.fetchone()
            result['schema_version'] = version[0] if version and version[0] else 0
        except sqlite3.OperationalError:
            result['schema_version'] = 0

        # Check for expected tables
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('users', 'companies', 'projects')
        """)
        tables = cursor.fetchall()
        result['has_tables'] = len(tables) >= 2  # At least users and one other table

        conn.close()

        result['valid'] = True

    except sqlite3.Error as e:
        result['error'] = f'Invalid SQLite database: {str(e)}'

    return result
