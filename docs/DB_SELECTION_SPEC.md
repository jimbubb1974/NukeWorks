DB Selection (Per-User/Session) - Design and Implementation Spec

Purpose

- Allow each user/session to choose which SQLite database file the app uses, before login, with a friendly name and a persistent last-used default. Support browsing for .sqlite files (including UNC paths), validate and migrate as needed, and ensure snapshots follow the selected database.

Key Requirements (confirmed)

- Per user/session scope: the selected DB applies to the current browser session (and is also saved for the authenticated user).
- Pre-login selector: show a "Select Database" screen before the login page with a default of the last-used DB; user can change it anytime.
- **Required on first access**: Database selector MUST be shown before any application access. No fallback to config file DATABASE_PATH.
- Input methods: show a defaults list (auto-scanned) and allow browsing/typing a path.
- Persistence
  - Bootstrap (pre-login, machine-level): remember last browsed folders and recent paths in instance-local JSON cache: instance/db_selector.json.
  - Authenticated user: persist last-used DB path (and display name) in the users table.
  - Friendly DB name: stored inside the selected DB via system_settings.db_display_name so the label travels with the database file.
- Defaults list: scan a project directory structure databases/<label>/nukeworks.sqlite; each DB has its own snapshots/ subfolder.
  - **Directory structure created during implementation**: The databases/ directory and initial structure will be created as part of this feature implementation.
- Validation and migrations: after selection, verify file exists and is a valid DB, check schema version, and offer/apply migrations if needed. On failure, fall back to the previous working DB and clearly notify the user.
  - **Schema compatibility**: If database schema_version matches REQUIRED_SCHEMA_VERSION, no migration needed - users can seamlessly switch between databases with identical schemas.
  - **Migration permissions**: Only admin users can execute migrations. Non-admin users can select databases that don't need migration, but are blocked from selecting databases requiring migration.
- Hot switch: allow switching the DB at runtime without server restart; acceptable to momentarily reinitialize engine/session for the current user.
- Snapshots: snapshot directory is derived from the selected DB (per-DB snapshots); user-triggered snapshots follow the current DB.
- Access: DB selection is available to all users (not admin-only), including anonymous users pre-login.

Non-Goals and Design Decisions

- **Automated snapshots DISABLED**: The automated daily snapshot scheduler is disabled entirely. Only manual snapshots (admin-triggered) are supported, targeting the currently selected database's snapshots/ directory.
- **Engine cache management**: No automatic limit on cached engines; admin interface provided to manually dispose/close unused engines to manage file locks and memory.

Data Model and Storage

1. users table (current DB)

   - Add columns:
     - last_db_path TEXT NULL
     - last_db_display_name TEXT NULL
   - These store a user’s last-used selection post-login. They are hints, not enforcement.

2. system_settings (inside each selected DB)

   - Add or reuse key db_display_name (TEXT). If absent, the selector will let the user provide a temporary display name (stored on save/migrate).

3. instance/db_selector.json (machine-local bootstrap)
   - JSON structure:
     - last_browsed_dir: string
     - recent_paths: string[] (absolute paths)
     - global_default_path: string (optional, used for pre-login default when no authenticated user context is available)

Directory Layout (defaults list)

- Project-managed DBs (auto-scanned):
  - databases/
    - <label_1>/
      - nukeworks.sqlite
      - snapshots/
    - <label_2>/
      - nukeworks.sqlite
      - snapshots/
- The selector lists all databases/\*\*/nukeworks.sqlite, showing <label> as the friendly name if db_display_name is missing.

Runtime Architecture Changes (per-session DB)

1. Session-scoped DB selection

   - Store selected DB path in Flask session under key selected_db_path.
   - Derive a session-level SQLAlchemy engine and session from this path.

2. DB session accessor (LocalProxy)

   - Replace global db_session usage with a LocalProxy that resolves per-request (from flask.g) if a session-specific DB is active; otherwise fallback to app-level default.
   - Implementation sketch:
     - In app/**init**.py create get_db_session() which returns g.db_session if set, else app.db_session.
     - Expose db_session = LocalProxy(get_db_session) for import compatibility.
   - Before each request, if session['selected_db_path'] differs from app’s default, ensure an engine+scoped_session exists in a cache keyed by absolute DB path, assign g.db_session accordingly.

3. Engine/session cache

   - Maintain a dict path->(engine, scoped_session_factory) to avoid recreating engines on every request.
   - Dispose engines on application shutdown or when explicitly requested (admin tool) to release file locks.

4. Snapshot directory derivation
   - For a selected DB path …/databases/<label>/nukeworks.sqlite, use …/databases/<label>/snapshots as SNAPSHOT_DIR for that request/user by setting g.snapshot_dir or computing on demand.

Pre-Login Selector (UX/Routes)

- Route: GET /select-db

  - Shows:
    - Last used (from instance cache global_default_path if anonymous; from users.last_db_path if known and DB reachable)
    - Auto-scanned list from databases/\*\*/nukeworks.sqlite with friendly names (db_display_name if present; else directory name)
    - “Browse…” input (free text path and a small JS-powered file picker where available); remember last_browsed_dir in instance JSON
  - Buttons: Continue, Refresh List

- Route: POST /select-db
  - Validates chosen path (exists, is SQLite); attempts to open and read minimal metadata (schema_version, system_settings.db_display_name)
  - Migration flow:
    - If schema_version < REQUIRED_SCHEMA_VERSION: show prompt to apply migrations; if accepted, run migrations (non-interactive)
    - On failure: show error and fall back to previous working DB (if any), with unambiguous flash message
  - On success:
    - session['selected_db_path'] = path
    - Update instance cache (recent_paths, last_browsed_dir)
    - If authenticated: persist users.last_db_path and last_db_display_name
    - Redirect to login (if anonymous) or back to the previous page

Login and Redirect Logic

- **Pre-login flow**: Any unauthenticated user hitting any route (without session['selected_db_path']) → redirect to /select-db → user selects DB → redirect to /login → user authenticates → application access.
- **Post-login flow**: Authenticated users can access "Database" link in navigation header to switch databases anytime.
- **User preference suggestion**: On login, if users.last_db_path exists and is valid, it's suggested as default in the selector but can be overridden. Session selection always takes precedence over saved preference.

Migrations and Validation

- On selection, check:
  - File exists and is readable.
  - SQLite PRAGMAs work, tables present.
  - schema_version vs REQUIRED_SCHEMA_VERSION.
  - **If schema_version == REQUIRED_SCHEMA_VERSION**: No migration needed, proceed immediately (seamless switching).
  - **If schema_version < REQUIRED_SCHEMA_VERSION**: Show migration prompt. Only admin users can proceed with migration; non-admin users are blocked with clear error message.
  - Optional: company table presence to pre-warn user if DB seems empty.
- Apply migrations via existing utils/migrations helpers with admin permission check.
- On any failure, fall back to previous working DB (if any) and flash a warning banner with specific error details.

Snapshots Behavior

- **Manual snapshots only**: Admin users can trigger manual snapshots, which target the currently selected DB's sibling snapshots/ directory (e.g., databases/<label>/snapshots/).
- **Automated scheduler DISABLED**: The automated daily snapshot scheduler is completely disabled. No background snapshot automation across any databases.

Persistence Details

- Per-user (users table): last_db_path, last_db_display_name updated upon successful selection while authenticated.
- Machine bootstrap (instance/db_selector.json): store recent_paths (for quick selection), last_browsed_dir, and a global_default_path used pre-login.
- Friendly name within the DB (system_settings.db_display_name): set if missing when the user assigns a name.

Security and Paths

- No restrictions on path location; UNC paths allowed. Validate existence and readability. Sanitize user-provided strings for display.
- **Session-based isolation**: Each Flask session maintains its own database selection via filesystem-based sessions (SESSION_TYPE = 'filesystem').

Multi-User and Audit Considerations

- **Per-session database contexts**: LocalProxy pattern ensures db_session resolves to the correct per-session database on each request via flask.g.
- **Audit logging compatibility**: Audit trails in app/services/audit.py automatically write to the user's selected database since they use the db_session LocalProxy.
- **Engine cache**: Maintains dict of absolute_db_path → (engine, scoped_session_factory) with no automatic limits. Admin interface provided to manually dispose unused engines to manage file locks and memory.

UI Notes

- Selector is accessible from a header link “Database” once logged in to change DB at any time. Pre-login, it’s the first screen.
- Banner messaging on fallback: “Your selected database could not be opened. Reverted to <name>. Reason: <detail>.”

Testing Plan

- Unit tests: engine cache, LocalProxy db_session resolution, migration prompts.
- Integration tests: select valid DB, invalid DB (fallback), migration-needed DB, empty DB warning.
- Manual QA: UNC paths, switching while logged-in, snapshot creation landing in per-DB snapshots/.

Implementation Checklist (for CLI agent)

1. **Directory Structure**
   - Create databases/ directory structure at project root
   - Create initial databases/default/nukeworks.sqlite and databases/default/snapshots/ as example

2. **Models**
   - Add columns to users: last_db_path TEXT, last_db_display_name TEXT.
   - Create migration to add these columns (SQLite ALTER TABLE add column).

3. **Instance cache**
   - New module app/utils/db_selector_cache.py handling instance/db_selector.json read/write with schema:
     {"recent_paths": [], "last_browsed_dir": "", "global_default_path": ""}

4. **DB session indirection (LocalProxy)**
   - In app/__init__.py:
     - Introduce get_db_session() and db_session = LocalProxy(get_db_session).
     - Add before_request to resolve session['selected_db_path'] → engine cache → g.db_session.
     - Maintain an engine/session cache dict keyed by absolute DB path.
     - Add engine disposal function for admin interface.

5. **Config helpers**
   - Utility to compute per-DB SNAPSHOT_DIR from selected path (…/snapshots).
   - Expose a getter to use in snapshot services instead of a fixed app.config value when g.context exists.

6. **Routes and templates**
   - New blueprint routes/db_select.py with /select-db GET/POST.
   - Template templates/db_select/select.html with:
     - Defaults list (scanned databases/**/nukeworks.sqlite)
     - Recent paths, browse input (text + directory remember)
     - Display of friendly name; ability to set if missing
     - Migration prompt UI for admin users
   - Register blueprint in app/__init__.py

7. **Middleware and redirects**
   - Add before_request handler: if no session['selected_db_path'], redirect to /select-db (except for /select-db itself and static assets).
   - Add "Database" link to navigation header for authenticated users.

8. **Migration and validation**
   - On POST selection: validate file, check schema_version.
   - If schema_version == REQUIRED_SCHEMA_VERSION: proceed immediately (seamless switch).
   - If schema_version < REQUIRED_SCHEMA_VERSION:
     - Check if current_user.is_admin
     - If admin: show migration prompt, allow proceeding
     - If not admin: block with error message
   - On failure: fallback to previous working DB (if any); flash banner with specific error.

9. **Snapshots**
   - Update snapshot services to derive snapshot target from current request's selected DB (g or session).
   - **DISABLE automated scheduler**: Comment out or remove start_snapshot_scheduler() call in app/__init__.py.
   - Update admin snapshot UI to show per-DB snapshot directory.

10. **Defaults scanner**
    - Walk databases/*/nukeworks.sqlite and build a list with display labels (db_display_name or folder name).
    - Helper function to read db_display_name from system_settings table without full session.

11. **Friendly name persistence**
    - If user provides a name and system_settings.db_display_name is missing/different, write it to the DB on selection confirmation.

12. **Admin interface for engine management**
    - Add route in admin.py to list cached engines (path, last used, etc.)
    - Add button to dispose/close specific engines to release file locks.

13. **Docs and help**
    - Update README Setup to include databases/ structure and the new selector.
    - Troubleshooting section for invalid DB fallback messages.

Rollout Notes

- **Breaking change**: Database selector is now REQUIRED on first access; no automatic fallback to config DATABASE_PATH.
- **Migration compatibility**: Users can seamlessly switch between databases with matching schema versions.
- **Session persistence**: Uses existing filesystem-based sessions (SESSION_TYPE = 'filesystem').
- **Backwards compatibility**: Existing routes continue to work due to LocalProxy indirection for db_session.









