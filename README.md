# NukeWorks - Nuclear Project Management Database

A multi-user web-based database application for managing nuclear project data, technology vendors, stakeholders, and client relationships — with granular confidentiality controls, per-field encryption, and an AI-assisted research workflow.

## Features

- **Multi-Database Support** — select from multiple SQLite database files at runtime; no restart required
- **Two-Tier Permission System** — Confidential Access (Tier 1) and NED Team Access (Tier 2), independent of each other
- **Per-Field Encryption** — financial and strategy fields encrypted at rest using Fernet symmetric encryption with separate key sets per tier
- **Unified Company Management** — single company table covering vendors, owners, operators, constructors, offtakers, and MPR clients
- **Client Relationship Management (CRM)** — roundtable meeting history, client tiering/prioritization, and stakeholder strength tracking
- **Personnel Directory** — internal MPR staff and external contacts, with MPR-to-client contact linking
- **AI Research Workflow** — export company profiles for external AI processing, then stage and review results before committing to the database
- **Network Diagram Visualization** — interactive diagram and tabular view of project relationships
- **PDF Report Generation** — project summaries with confidentiality filtering
- **Database Migration System** — sequential SQL migrations with automatic backup and rollback on failure
- **Automated Backup/Snapshot System** — point-in-time backups with configurable retention

## Technology Stack

- **Backend**: Python 3.9+, Flask 3.0, SQLAlchemy 2.0
- **Database**: SQLite 3 (WAL mode, 30-second busy timeout)
- **Encryption**: `cryptography` library (Fernet); separate keys for Confidential and NED Team tiers
- **Frontend**: Bootstrap 5, Bootstrap Icons, Vanilla JS
- **Reports**: ReportLab (PDF), openpyxl (Excel export)
- **Authentication**: Flask-Login, bcrypt

## Project Structure

```
NukeWorks/
├── app.py                        # Entry point
├── config.py                     # DevelopmentConfig / ProductionConfig / TestingConfig
├── requirements.txt
├── .env.example                  # Environment variable template
│
├── app/
│   ├── __init__.py               # App factory, blueprint registration, Jinja filters
│   ├── models/
│   │   ├── base.py               # Base + TimestampMixin
│   │   ├── user.py               # User authentication and permission flags
│   │   ├── company.py            # Company, CompanyRole, CompanyRoleAssignment,
│   │   │                         #   ClientProfile, PersonCompanyAffiliation,
│   │   │                         #   InternalExternalLink
│   │   ├── project.py            # Project (with coordinates)
│   │   ├── personnel.py          # Personnel (base), InternalPersonnel
│   │   ├── external_personnel.py # ExternalPersonnel (incl. relationship_strength)
│   │   ├── relationships.py      # PersonnelRelationship
│   │   ├── contact_log.py        # ContactLog (CRM interaction records)
│   │   ├── roundtable.py         # RoundtableHistory (encrypted NED Team notes)
│   │   ├── research.py           # ResearchImportRun, ResearchQueueItem
│   │   └── system.py             # ConfidentialFieldFlag, AuditLog,
│   │                             #   DatabaseSnapshot, SystemSetting, SchemaVersion
│   │
│   ├── routes/
│   │   ├── auth.py               # /auth — login, logout, password, profile
│   │   ├── dashboard.py          # / — home
│   │   ├── db_select.py          # (no prefix) — database file picker
│   │   ├── companies.py          # /companies — CRUD, role management, employees
│   │   ├── projects.py           # /projects — project CRUD, map view
│   │   ├── personnel.py          # /personnel — internal/external directory
│   │   ├── crm.py                # /crm — roundtable, client dashboard, strength tracking
│   │   ├── contact_log.py        # /contact-log — interaction logging
│   │   ├── network.py            # network diagram JSON API
│   │   ├── reports.py            # /reports — PDF generation
│   │   ├── research.py           # /research — AI workflow export/import/review
│   │   └── admin.py              # /admin — users, snapshots, settings, audit log
│   │
│   ├── forms/                    # Flask-WTF form classes
│   ├── templates/                # Jinja2 templates (mirroring routes/ structure)
│   ├── static/                   # CSS, JS, images
│   └── utils/
│       ├── permissions.py        # can_view_field(), get_field_display_value(), decorators
│       ├── migrations.py         # Migration runner
│       └── key_management.py     # Fernet key loading
│
├── migrations/                   # SQL migration files (001–019)
├── scripts/                      # Standalone utility scripts
├── tests/                        # pytest test suite
└── docs/                         # Specification documents
```

## Installation & Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your settings
```

Key variables:

| Variable | Purpose |
|---|---|
| `FLASK_ENV` | `development` or `production` |
| `SECRET_KEY` | Session encryption key (required in production) |
| `NUKEWORKS_DB_PATH` | Default SQLite database path |
| `NUKEWORKS_DATA_DIR` | Writable storage root for snapshots etc. |
| `CONFIDENTIAL_DATA_KEY` | Fernet key for Tier 1 encrypted fields |
| `NED_TEAM_KEY` | Fernet key for Tier 2 (NED Team) encrypted fields |

### 4. Initialize a Database

```bash
flask init-db-cmd
```

Creates all tables, default settings, and a default admin user (`admin` / `admin123`).

> **⚠️ Change the default admin password immediately after first login.**

### 5. Run the Application

```bash
python app.py
```

Open `http://127.0.0.1:5000/` — you will be prompted to select a database file before accessing any other page.

## Common CLI Commands

```bash
# Create an admin user
flask create-admin --username <name> --email <email> --password <password>

# Check which migrations are pending
flask check-migrations

# Apply pending migrations to the selected database
flask apply-migrations

# Show migration history
flask migration-history

# Apply migrations directly against a database file (bypasses the session)
python scripts/run_migrations.py <path_to_database>
```

## Permission Levels

| Role | Access |
|---|---|
| **Read-Only User** | View public data only; no edits |
| **Standard User** | View public data; can edit non-confidential records |
| **Confidential Access (Tier 1)** | + financial fields (CAPEX, OPEX, LCOE, fuel cost) and confidential relationships |
| **NED Team (Tier 2)** | + internal client assessments, roundtable history, CRM strategy notes |
| **Administrator** | Full access, user management, snapshots, system settings |

Tiers are independent — a user can have Confidential Access without being NED Team, or vice versa.

## Database Migration System

Migrations are SQL files in `migrations/` named `NNN_description.sql`. They must follow this pattern:

```sql
BEGIN TRANSACTION;

-- DDL changes here

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (N, datetime('now'), 'system', 'Description');

COMMIT;
```

The current required schema version is **19**. The migration runner creates a backup before applying changes and rolls back on failure.

Note: migrations 010 and 013 each have two files with the same number prefix — this is a known issue; the runner handles them by filename sort order.

## CRM & Roundtable Features

The CRM module is restricted to NED Team members and administrators.

- **Client Dashboard** — filterable list of MPR clients with tier and priority
- **Roundtable Matrix** — Tier × Priority grid for visualizing client portfolio at a glance
- **Roundtable Entry Pages** — per-client pages with encrypted meeting notes (next steps, client focus, MPR targets, discussion), client category management (tier/priority), and company personnel with relationship strength tracking
- **Relationship Strength** — per-contact field on external personnel: `Strong` (green), `Medium` (orange), `Skeptical` (red), `Unaware` (black); editable inline on the roundtable client page
- **Contact Log** — timestamped interaction records linked to companies and contacts

## AI Research Workflow

The research module (NED Team only) supports a human-in-the-loop workflow for enriching company data with AI assistance:

1. **Export** — select companies and generate a chunked JSON package for an external AI tool
2. **Import** — upload AI-generated results into a staged review queue
3. **Review** — accept, skip, or delete each item before it touches the live database
4. Accepted items write directly to the appropriate company or personnel records

## Running Tests

```bash
# All tests
pytest

# Single file
pytest tests/test_validators.py

# Coverage report
pytest --cov=app --cov-report=html
```

`conftest.py` provides session-scoped `app` and `db_session` fixtures plus a `permission_dataset` fixture that creates four test users (admin, ned_user, conf_user, standard_user) with a fully-configured project for permission testing.

## Code Quality

```bash
flake8 app/
black app/
```

## Windows Installer Builds

Packaging scripts in `installer/` produce a PyInstaller bundle wrapped with an Inno Setup installer for distribution without requiring users to install Python. See `docs/installer_guide.md`.

## Deployment Notes

- **Production secret key**: `python -c "import secrets; print(secrets.token_hex(32))"`
- **Network drive databases**: set `NUKEWORKS_DB_PATH` to the UNC path; WAL mode and a 30-second busy timeout are applied automatically
- **Encryption keys**: generate with `scripts/generate_encryption_keys.py`; store in `.env` or environment — never commit to source control

## Troubleshooting

| Problem | Likely cause / fix |
|---|---|
| `database is locked` | WAL mode is automatic; check network drive connectivity or other exclusive-lock processes |
| Schema version mismatch | Apply pending migrations via `flask apply-migrations` or the in-app migration prompt |
| `UnicodeEncodeError` on Windows | `app.py` reconfigures stdout/stderr to UTF-8 on startup; ensure you are running via the venv `python` binary |
| Login fails | Check the user's `is_active` flag in the Admin panel |

## License

Proprietary — All rights reserved

---

**NukeWorks** © 2025 | Nuclear Project Management Database
