"""
Database Selector Cache Module
Manages instance-local JSON cache for database selection bootstrap data
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def get_cache_file_path() -> Path:
    """Get path to db_selector.json in instance directory"""
    base_dir = Path(__file__).parent.parent.parent
    instance_dir = base_dir / 'instance'
    instance_dir.mkdir(exist_ok=True)
    return instance_dir / 'db_selector.json'


def _get_default_cache() -> Dict:
    """Return default cache structure"""
    return {
        'recent_paths': [],
        'last_browsed_dir': '',
        'global_default_path': ''
    }


def load_cache() -> Dict:
    """
    Load cache from instance/db_selector.json

    Returns:
        Dict with keys: recent_paths, last_browsed_dir, global_default_path
    """
    cache_file = get_cache_file_path()

    if not cache_file.exists():
        logger.info(f"Cache file does not exist, creating default: {cache_file}")
        return _get_default_cache()

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        # Ensure all required keys exist
        default = _get_default_cache()
        for key in default:
            if key not in cache:
                cache[key] = default[key]

        return cache

    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load cache file: {e}")
        return _get_default_cache()


def save_cache(cache: Dict) -> bool:
    """
    Save cache to instance/db_selector.json

    Args:
        cache: Dict with keys: recent_paths, last_browsed_dir, global_default_path

    Returns:
        bool: True if successful, False otherwise
    """
    cache_file = get_cache_file_path()

    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
        return True

    except IOError as e:
        logger.error(f"Failed to save cache file: {e}")
        return False


def add_recent_path(db_path: str, max_recent: int = 10) -> None:
    """
    Add a database path to recent paths list

    Args:
        db_path: Absolute path to database file
        max_recent: Maximum number of recent paths to keep
    """
    cache = load_cache()

    # Normalize path
    db_path = os.path.abspath(db_path)

    # Remove if already exists (will be added to front)
    if db_path in cache['recent_paths']:
        cache['recent_paths'].remove(db_path)

    # Add to front
    cache['recent_paths'].insert(0, db_path)

    # Limit to max_recent
    cache['recent_paths'] = cache['recent_paths'][:max_recent]

    save_cache(cache)


def set_last_browsed_dir(directory: str) -> None:
    """
    Update last browsed directory

    Args:
        directory: Directory path
    """
    cache = load_cache()
    cache['last_browsed_dir'] = os.path.abspath(directory)
    save_cache(cache)


def set_global_default_path(db_path: str) -> None:
    """
    Set global default database path (used pre-login)

    Args:
        db_path: Absolute path to database file
    """
    cache = load_cache()
    cache['global_default_path'] = os.path.abspath(db_path)
    save_cache(cache)


def get_global_default_path() -> Optional[str]:
    """
    Get global default database path

    Returns:
        str or None: Path if set, None otherwise
    """
    cache = load_cache()
    path = cache.get('global_default_path', '')
    return path if path else None


def get_recent_paths() -> List[str]:
    """
    Get list of recent database paths

    Returns:
        List of absolute paths
    """
    cache = load_cache()
    # Filter out paths that no longer exist
    valid_paths = [p for p in cache.get('recent_paths', []) if os.path.exists(p)]

    # Update cache if any paths were removed
    if len(valid_paths) != len(cache.get('recent_paths', [])):
        cache['recent_paths'] = valid_paths
        save_cache(cache)

    return valid_paths


def get_last_browsed_dir() -> str:
    """
    Get last browsed directory

    Returns:
        str: Directory path, or empty string if not set
    """
    cache = load_cache()
    return cache.get('last_browsed_dir', '')
