# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run dev server
python app.py

# Initialize a fresh database
flask init-db-cmd

# Create an admin user
flask create-admin --username <name> --email <email> --password <password>

# Run all tests
pytest

# Run a single test file
pytest tests/test_validators.py

# Coverage report
pytest --cov=app --cov-report=html

# Lint / format
flake8 app/
black app/

# Migration commands (Flask CLI)
flask check-migrations
flask apply-migrations
flask migration-history

# Apply migrations directly against a database file
python scripts/run_migrations.py <path_to_database>
```

## Architecture

### Database selection before everything else

The app does **not** open a database connection at startup. Every request goes through a `before_request` middleware (`register_db_selector_middleware` in `app/__init__.py`) that checks `session['selected_db_path']`. If missing, the user is redirected to the database picker (`db_select` blueprint) before any other route runs. Exemptions: static files, auth routes, `/api` endpoints, and AJAX requests (which get `g.db_session` set without a redirect).

Per-request database sessions are stored in `g.db_session` via `get_or_create_engine_session()`, which caches SQLAlchemy engines by absolute path in a module-level `_engine_cache` dict. WAL mode, foreign keys, and a 30-second busy timeout are set on every new connection.

### Two-tier permission system

Permissions are field-level and relationship-level, not just route-level. Two independent tiers:

- **Tier 1 (Confidential)** — `user.has_confidential_access`. Gates business-sensitive fields (financials, confidential relationships).
- **Tier 2 (NED Team)** — `user.is_ned_team`. Gates internal strategy notes and roundtable history.
- **Admin** — `user.is_admin` bypasses all checks.

The key utility functions are in `app/utils/permissions.py`:
- `can_view_field(user, table_name, record_id, field_name)` — checks `ConfidentialFieldFlag` records
- `get_field_display_value(user, entity, field_name, ...)` — returns value or `[Confidential]`
- `can_view_ned_content(user)` / `get_ned_field_value(...)` — Tier 2 equivalent

Templates use registered Jinja filters rather than calling these functions directly:
```jinja2
{% if 'projects'|can_view_field(project.project_id, 'capex') %}
{{ project|field_value('capex') }}
{{ client|ned_field_value('relationship_notes') }}
```

### Per-field encryption

Encrypted fields use a custom SQLAlchemy `TypeDecorator` called `EncryptedString(key_type)`, where `key_type` is `'confidential'` or `'ned_team'`. Encryption/decryption is transparent at the ORM layer via Fernet (`cryptography` library). Currently applied to Project financial fields (CAPEX, OPEX, fuel\_cost, LCOE); more fields are planned in Phase 3b–3e. Key management lives in `app/utils/key_management.py`.

### Unified company model

Legacy role-specific tables (vendor, owner, operator, constructor, offtaker) were replaced by a single `Company` table with `CompanyRole` and `CompanyRoleAssignment` junction records. The deprecated `app/services/company_sync.py` is marked for removal after legacy tables are dropped. Do not add new code that references legacy role tables.

### Blueprints

| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| `db_select` | (none) | Database file picker — runs before auth |
| `auth` | `/auth` | Login, logout, password management |
| `dashboard` | `/` | Home |
| `companies` | `/companies` | Company CRUD and role management |
| `projects` | `/projects` | Project CRUD |
| `crm` | `/crm` | Client relationship management |
| `contact_log` | `/contact-log` | Interaction logs |
| `personnel` | `/personnel` | Personnel management |
| `reports` | `/reports` | PDF/Excel generation via ReportLab/openpyxl |
| `admin` | `/admin` | User management, snapshots, settings |
| `network` | (none) | JSON API for network diagram |

### Migration system

SQL migrations live in `migrations/` and are versioned via a `schema_version` table. `REQUIRED_SCHEMA_VERSION` in `config.py` is currently 9 (application) / 12 (migration util). `check_and_apply_migrations(db_path)` handles backup creation, sequential application, and rollback on failure. **Note:** migrations 010 and 013 each have two files with the same number prefix — this is a known issue; the migration runner handles them by filename sort order.

### Configuration

Three config classes in `config.py`: `DevelopmentConfig`, `ProductionConfig`, `TestingConfig`. Selected via `FLASK_ENV`. Key env vars:

- `SECRET_KEY` — required in production (auto-generated in dev)
- `NUKEWORKS_DB_PATH` — default database path
- `NUKEWORKS_DATA_DIR` — writable storage root (defaults to `~/.local/share/NukeWorks` on Linux, `%LOCALAPPDATA%\NukeWorks` on Windows)
- `DEV_DB_PATH` — override dev database location

`TestingConfig` sets `DATABASE_PATH = ':memory:'`, disables CSRF, and reduces bcrypt rounds to 4 for speed.

### Test fixtures

`conftest.py` provides session-scoped `app` and `db_session` fixtures, plus a function-scoped `permission_dataset` fixture that creates four test users (admin, ned\_user, conf\_user, standard\_user) and a project with public and confidential relationships. Most tests that need database access should use these rather than creating their own setup.
