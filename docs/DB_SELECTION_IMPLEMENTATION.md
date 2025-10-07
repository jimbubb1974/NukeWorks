# Database Selection Feature - Implementation Summary

## Overview

The database selection feature allows users to choose which SQLite database file the application uses on a per-session basis. This enables seamless switching between multiple database environments without restarting the server.

## What Was Implemented

### 1. Directory Structure
- Created `databases/default/` directory with `snapshots/` subdirectory
- This structure allows organizing multiple databases with their own snapshot directories

### 2. Data Model Changes
- **users table**: Added `last_db_path` and `last_db_display_name` columns to persist user preferences
- **system_settings**: Uses existing table to store `db_display_name` within each database file
- **Migration 006**: Created migration script to add new columns to users table
- **Required Schema Version**: Updated from 4 to 6

### 3. Core Infrastructure

#### LocalProxy Pattern (`app/__init__.py`)
- Replaced global `db_session` with `LocalProxy` that resolves per-request
- Created `get_db_session()` function that returns `g.db_session` if set, else default
- Implemented engine cache: `_engine_cache` dict mapping `absolute_db_path → (engine, scoped_session)`
- Added `get_or_create_engine_session()` for creating/caching engines
- Added `dispose_engine()` for releasing file locks and memory
- Added `get_engine_cache_info()` for admin interface

#### Middleware (`register_db_selector_middleware()`)
- Before every request:
  - Check if `session['selected_db_path']` exists
  - If not, redirect to `/select-db` (except for static files and db_select routes)
  - If yes, get or create engine/session for that path
  - Set `g.db_session` and `g.selected_db_path`
  - Set `g.snapshot_dir` for per-DB snapshots

### 4. Instance Cache Module (`app/utils/db_selector_cache.py`)
Manages `instance/db_selector.json` with:
- `recent_paths`: List of recently used database paths
- `last_browsed_dir`: Last directory user browsed for databases
- `global_default_path`: Default database for pre-login sessions

Functions:
- `load_cache()`, `save_cache()`
- `add_recent_path()`, `set_last_browsed_dir()`, `set_global_default_path()`
- `get_recent_paths()`, `get_last_browsed_dir()`, `get_global_default_path()`

### 5. Database Helper Module (`app/utils/db_helpers.py`)
Utilities for per-database operations:
- `get_snapshot_dir_for_db(db_path)`: Derives snapshot directory from database path
- `get_db_display_name(db_path)`: Reads display name from database's system_settings
- `set_db_display_name(db_path, display_name)`: Writes display name to database
- `scan_databases_directory()`: Scans `databases/*/nukeworks.sqlite` for available databases
- `validate_database_file(db_path)`: Validates SQLite file, checks schema version, integrity

### 6. Database Selection Routes (`app/routes/db_select.py`)

#### GET `/select-db`
Displays database selector page with:
- Auto-scanned databases from `databases/` directory
- Recent paths from cache
- Suggested default (user preference or global default)
- Manual path entry field
- Custom display name field

#### POST `/select-db`
Processes database selection:
- Validates database file
- Checks schema version against REQUIRED_SCHEMA_VERSION
- **If schema matches**: Proceeds immediately (seamless switching)
- **If schema older**:
  - Non-admin: Blocked with error message
  - Admin: Shows migration prompt
- **If migration accepted**: Applies migrations via `check_and_apply_migrations()`
- Updates session, cache, and user preferences
- Redirects to login (if not authenticated) or dashboard

#### POST `/select-db` (with migration)
Shows migration prompt template with:
- Current and required schema versions
- Number of pending migrations
- Warning about backup and irreversibility
- Admin-only migration execution

### 7. Templates

#### `templates/db_select/select.html`
- Lists scanned databases with friendly names
- Shows recent databases
- Manual path entry with UNC support
- Custom display name input
- Refresh list button
- JavaScript for radio button UX

#### `templates/db_select/migration_prompt.html`
- Migration warning screen
- Schema version comparison
- Backup notification
- Admin confirmation button

#### `templates/base.html`
- Added "Database" link in navigation header (for authenticated users)
- Allows switching databases at any time

### 8. Snapshot Services Updates (`app/services/snapshots.py`)

#### `_get_database_path()`
- Checks `g.selected_db_path` first (per-session database)
- Falls back to config default

#### `_snapshot_dir()`
- Checks `g.snapshot_dir` first (per-DB snapshots)
- Falls back to configured or default directory

#### Automated Scheduler
- **DISABLED**: Removed `start_snapshot_scheduler()` call from `app/__init__.py`
- Only manual snapshots are supported
- Comment added explaining the change

### 9. Admin Interface for Engine Management

#### Route: GET `/admin/engines`
Displays cached engines with:
- Database path
- File size and modification time
- Connection pool size
- Active/inactive status

#### Route: POST `/admin/engines/dispose`
Disposes specific engine from cache:
- Closes all connections
- Releases file locks
- Frees memory
- Engine automatically recreated when needed

#### Template: `templates/admin/engine_cache.html`
- Table showing all cached engines
- Dispose button for each engine
- Information about engine cache behavior

#### Admin Index Update
- Added "Engine Cache" card linking to engine management

## Configuration Changes

### `config.py`
- `REQUIRED_SCHEMA_VERSION = 6` (was 4)
- Added comment about database selection feature

### `app/utils/migrations.py`
- `APPLICATION_REQUIRED_SCHEMA_VERSION = 6` (was 4)

## Key Design Decisions

### 1. Required on First Access
- Database selector MUST be shown before application access
- No automatic fallback to config DATABASE_PATH
- Pre-login flow: `/select-db` → `/login` → app

### 2. Schema Compatibility
- If `schema_version == REQUIRED_SCHEMA_VERSION`: Seamless switching, no migration
- Users can switch between databases with identical schemas freely
- Only admin users can execute migrations

### 3. Migration Permissions
- **Admin users**: Can select and migrate any database
- **Non-admin users**: Can only select databases that don't need migration
- Clear error message for non-admins attempting to use older databases

### 4. Session Isolation
- Each Flask session maintains its own database selection
- Uses filesystem-based sessions (`SESSION_TYPE = 'filesystem'`)
- Session selection persists across requests
- User preference saved but session takes precedence

### 5. Automated Snapshots
- **Completely disabled** to avoid complexity with per-session databases
- Only manual snapshots supported
- Manual snapshots always target currently selected database's snapshot directory

### 6. Engine Cache Management
- No automatic limits on cached engines
- Admin interface for manual disposal
- Helps manage file locks and memory usage

### 7. Audit Logging Compatibility
- Audit trails automatically write to user's selected database
- Uses `db_session` LocalProxy which resolves per-request
- No changes needed to `app/services/audit.py`

## File Structure

```
databases/
├── default/
│   ├── nukeworks.sqlite
│   └── snapshots/
├── production/
│   ├── nukeworks.sqlite
│   └── snapshots/
└── test/
    ├── nukeworks.sqlite
    └── snapshots/

instance/
└── db_selector.json  (bootstrap cache)

migrations/
└── 006_add_user_db_preferences.sql

app/
├── __init__.py  (LocalProxy, engine cache, middleware)
├── utils/
│   ├── db_selector_cache.py  (instance cache management)
│   └── db_helpers.py  (database utilities)
├── routes/
│   ├── db_select.py  (database selection routes)
│   └── admin.py  (added engine management routes)
├── services/
│   └── snapshots.py  (updated for per-DB snapshots)
├── models/
│   └── user.py  (added last_db_path, last_db_display_name)
└── templates/
    ├── base.html  (added Database link)
    ├── db_select/
    │   ├── select.html
    │   └── migration_prompt.html
    └── admin/
        ├── index.html  (added Engine Cache card)
        └── engine_cache.html
```

## Testing Recommendations

### Unit Tests
- Engine cache creation and disposal
- LocalProxy `db_session` resolution
- Migration permission checks
- Database validation
- Cache file read/write

### Integration Tests
- Select valid database (seamless switch)
- Select database requiring migration (admin vs non-admin)
- Invalid database file (fallback behavior)
- Session persistence across requests
- Manual snapshot creation to correct directory

### Manual QA
- UNC path support
- Switching databases while logged in
- Pre-login database selection
- Migration UI for admin users
- Engine cache disposal
- Snapshot creation landing in per-DB `snapshots/` directory

## Backwards Compatibility

### Breaking Changes
- Database selector is now REQUIRED on first access
- No automatic fallback to config `DATABASE_PATH` after initial setup
- Automated snapshot scheduler disabled

### Compatible Changes
- Existing routes continue to work due to LocalProxy indirection
- Old databases can be migrated by admin users
- User table migration is backwards compatible (nullable columns)

## Future Enhancements

Potential improvements not included in initial implementation:

1. **Multi-DB Automated Snapshots**: Per-user scheduled snapshots across selected databases
2. **Database Templates**: Create new databases from templates
3. **Database Health Monitoring**: Dashboard showing status of all databases
4. **Connection Pooling Tuning**: Per-database pool configuration
5. **Database Metrics**: Track usage, queries, performance per database
6. **Export/Import**: Transfer data between databases
7. **Database Roles/Teams**: Assign databases to specific teams or roles

## Rollout Notes

### Before Deployment
1. Apply migration 006 to existing databases
2. Create `databases/` directory structure
3. Copy existing database into `databases/default/` if needed
4. Verify `instance/` directory is writable

### First Launch
1. User visits application
2. Redirected to `/select-db`
3. Selects database (or enters path)
4. If migration needed and user is admin, prompt to migrate
5. Redirected to login
6. After login, can switch databases via "Database" link in header

### Admin Tasks
- Monitor engine cache via `/admin/engines`
- Dispose unused engines to free resources
- Manually create snapshots as needed
- Manage user database preferences

## Documentation Updates Needed

- README: Setup instructions for `databases/` directory
- User Guide: How to select and switch databases
- Admin Guide: Engine cache management, manual snapshots
- Troubleshooting: Common issues with database selection, migration failures
