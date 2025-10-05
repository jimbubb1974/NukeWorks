# NukeWorks - Nuclear Project Management Database

A multi-user web-based database application for managing nuclear project data, technology vendors, stakeholders, and client relationships with granular confidentiality controls.

## Features

- **Multi-User SQLite Database** on network drive with WAL mode for concurrency
- **Two-Tier Permission System**:
  - Tier 1: Confidential Access (business data)
  - Tier 2: NED Team Access (internal strategy notes)
- **Client Relationship Management (CRM)** for tracking interactions
- **Network Diagram Visualization** of relationships
- **PDF Report Generation** with confidentiality filtering
- **Automated Backup/Snapshot System**
- **Database Migration System** for schema evolution

## Technology Stack

- **Backend**: Python 3.9+, Flask 3.0, SQLAlchemy 2.0
- **Database**: SQLite 3 (with WAL mode)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Reports**: ReportLab (PDF generation), openpyxl (Excel export)
- **Authentication**: Flask-Login, bcrypt

## Project Structure

```
nukeworks/
├── app.py                      # Main application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variable template
│
├── app/                       # Application package
│   ├── __init__.py           # Flask app factory
│   ├── exceptions.py         # Custom exceptions
│   │
│   ├── models/               # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── base.py           # Base model and mixins
│   │   ├── user.py           # User authentication
│   │   ├── vendor.py         # Technology vendors
│   │   ├── project.py        # Projects
│   │   ├── owner.py          # Owners/developers
│   │   ├── personnel.py      # Personnel
│   │   ├── relationships.py  # Junction tables
│   │   └── ...              # Other models
│   │
│   ├── routes/               # Flask blueprints
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication routes
│   │   ├── dashboard.py      # Dashboard
│   │   ├── vendors.py        # Vendor CRUD
│   │   ├── projects.py       # Project CRUD
│   │   ├── owners.py         # Owner CRUD
│   │   ├── crm.py            # CRM features
│   │   ├── reports.py        # Report generation
│   │   └── admin.py          # Administration
│   │
│   ├── services/             # Business logic
│   │   └── ...
│   │
│   ├── templates/            # Jinja2 templates
│   │   ├── base.html        # Base template
│   │   ├── dashboard.html   # Dashboard
│   │   ├── auth/            # Authentication pages
│   │   ├── vendors/         # Vendor pages
│   │   ├── projects/        # Project pages
│   │   └── ...
│   │
│   ├── static/              # Static files
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── permissions.py   # Permission checking
│       └── db_init.py      # Database initialization
│
├── migrations/              # Database migrations
├── tests/                   # Test suite
└── docs/                    # Specification documents
```

## Installation & Setup

### 1. Clone the Repository

```bash
cd /path/to/NukeWorks
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env
```

**Important environment variables:**
- `FLASK_ENV`: Set to `development` or `production`
- `SECRET_KEY`: Generate a secure random key for production
- `NUKEWORKS_DB_PATH`: Path to SQLite database file
- `NUKEWORKS_SNAPSHOT_DIR`: Path to snapshot backup directory

### 5. Initialize Database

```bash
# Initialize database with default settings
flask init-db-cmd
```

This creates:
- All database tables
- Default system settings
- Default admin user (username: `admin`, password: `admin123`)

**⚠️ IMPORTANT**: Change the default admin password immediately after first login!

### 6. Run the Application

```bash
# Development mode
python app.py

# Or using Flask CLI
flask run
```

The application will start on `http://127.0.0.1:5000/`

## Default Credentials

**Username**: `admin`
**Password**: `admin123`

**⚠️ SECURITY WARNING**: Change this password immediately after first login!

## Usage

### Creating Additional Users

Use the Flask CLI command:

```bash
flask create-admin --username newadmin --email admin@example.com --password securepassword
```

Or create users through the Admin interface after logging in.

### Permission Levels

#### Regular User
- View all public data
- Cannot see confidential fields or NED Team notes

#### User with Confidential Access (Tier 1)
- View all public + confidential business data
- Financial information (CAPEX, OPEX, etc.)
- Confidential relationships

#### NED Team Member (Tier 2)
- View internal client assessments
- View roundtable discussion history
- Access CRM internal notes

#### Administrator
- Full access to all data
- User management
- System settings
- Database snapshots

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py
```

### Code Formatting

```bash
# Format code with black
black app/

# Check code style with flake8
flake8 app/
```

### Database Migrations

```bash
# Create a new migration
# (Future: Will use Alembic)

# Apply migrations
# (Future: Will use Alembic)
```

## Deployment

### For Production

1. **Set environment to production**:
   ```bash
   export FLASK_ENV=production
   ```

2. **Generate secure secret key**:
   ```python
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Add this to `.env` as `SECRET_KEY`

3. **Configure network database path**:
   ```
   NUKEWORKS_DB_PATH=\\networkdrive\nuclear_projects\nukeworks_db.sqlite
   NUKEWORKS_SNAPSHOT_DIR=\\networkdrive\nuclear_projects\snapshots
   ```

4. **Package as standalone executable** (future):
   ```bash
   pyinstaller nukeworks.spec
   ```

## Architecture Highlights

### Database Concurrency
- **WAL Mode**: Enabled for better concurrent access on network drives
- **Optimistic Locking**: Detects conflicts at save time using timestamps
- **Automatic Retry**: Up to 5 attempts for database locks

### Permission System
- **Two Independent Tiers**: Confidential Access and NED Team
- **Field-Level Confidentiality**: Mark specific fields as confidential per record
- **Relationship Confidentiality**: Hide sensitive business relationships

### Security
- **Password Hashing**: bcrypt with salt
- **Session Management**: Secure session tokens, 8-hour timeout
- **CSRF Protection**: All forms protected
- **Input Validation**: Server-side validation for all inputs

## Documentation

Complete specification documents are in the `docs/` directory:

- `00_MASTER_SPECIFICATION.md` - Overview and navigation
- `01_ARCHITECTURE.md` - System architecture
- `02_DATABASE_SCHEMA.md` - Core entity tables
- `03_DATABASE_RELATIONSHIPS.md` - Junction tables
- `04_DATA_DICTIONARY.md` - Field definitions
- `05_PERMISSION_SYSTEM.md` - Access control
- And 17 more detailed specification documents...

## Troubleshooting

### Database Locked Errors
If you see "database is locked" errors:
1. Ensure WAL mode is enabled (automatic in this app)
2. Check network drive connectivity
3. Verify no other processes have the database open exclusively

### Login Issues
1. Verify username/password
2. Check that user account is active
3. Review logs for authentication errors

### Permission Issues
1. Verify user has correct permission flags
2. Check confidentiality settings on specific fields
3. Review NED Team access requirements

## Contributing

1. Follow Python PEP 8 style guide
2. Write tests for new features
3. Update documentation
4. Use meaningful commit messages

## License

Proprietary - All rights reserved

## Support

For questions or issues:
1. Check the `docs/21_TROUBLESHOOTING.md` guide
2. Review `docs/20_GLOSSARY.md` for terminology
3. Contact the technical lead

---

**NukeWorks** © 2025 | Nuclear Project Management Database
