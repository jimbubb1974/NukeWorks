# NukeWorks Quick Setup Guide

## Prerequisites
- Python 3.9 or higher
- Terminal/Command Line access
- Network drive access (for production deployment)

## Quick Start (5 minutes)

### Step 1: Activate Virtual Environment

```bash
cd "/home/jim/Coding Project/NukeWorks"

# Activate virtual environment
source venv/bin/activate

# Verify activation (should show venv Python)
which python
```

### Step 2: Initialize Database

```bash
# Initialize database with default settings and admin user
flask init-db-cmd
```

**Expected Output:**
```
Initializing database...
WARNING: Default admin user created with username 'admin' and password 'admin123'
PLEASE CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!
Database initialized successfully!
```

### Step 3: Run the Application

```bash
# Start the Flask development server
python app.py
```

**Expected Output:**
```
============================================================
NukeWorks - Nuclear Project Management Database
============================================================
Environment: development
Database: /home/jim/Coding Project/NukeWorks/dev_nukeworks.sqlite
Starting Flask server on http://127.0.0.1:5000/
============================================================

Press CTRL+C to quit
```

### Step 4: Access the Application

1. Open your web browser
2. Navigate to: `http://127.0.0.1:5000/`
3. Login with:
   - **Username**: `admin`
   - **Password**: `admin123`

### Step 5: Change Default Password

1. After logging in, click on your username in the top right
2. Select "Change Password"
3. Enter current password (`admin123`) and set a new secure password

## Next Steps

### Create Additional Users (Optional)

```bash
# Using Flask CLI
flask create-admin --username yourusername --email you@example.com

# You'll be prompted for password
```

### Configure for Network Drive (Production)

1. Create `.env` file:
   ```bash
   cp .env.example .env
   nano .env
   ```

2. Edit `.env` with production settings:
   ```
   FLASK_ENV=production
   SECRET_KEY=<generate-secure-key>
   NUKEWORKS_DB_PATH=\\networkdrive\nuclear_projects\nukeworks_db.sqlite
   NUKEWORKS_SNAPSHOT_DIR=\\networkdrive\nuclear_projects\snapshots
   ```

3. Generate secure secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

## Verification Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed (see requirements.txt)
- [ ] Database initialized successfully
- [ ] Application starts without errors
- [ ] Can access login page at http://127.0.0.1:5000/
- [ ] Can login with default credentials
- [ ] Can access dashboard after login
- [ ] Admin password changed from default

## Project Structure Overview

```
nukeworks/
├── app.py                      # ✅ Main entry point - START HERE
├── config.py                   # ✅ Configuration settings
├── requirements.txt            # ✅ Python dependencies
├── .env.example               # ✅ Environment template
│
├── app/                       # ✅ Application package
│   ├── __init__.py           # ✅ Flask app factory
│   ├── models/               # ✅ 15 core database models
│   ├── routes/               # ✅ 8 blueprint modules
│   ├── templates/            # ✅ HTML templates
│   ├── static/               # ✅ CSS, JS, images
│   └── utils/                # ✅ Permission system & utilities
│
├── migrations/               # Database migration scripts
├── tests/                    # Test suite (to be implemented)
└── docs/                     # ✅ 23 specification documents
```

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python app.py

# Initialize/reset database
flask init-db-cmd

# Create admin user
flask create-admin

# Run tests (future)
pytest

# Format code
black app/

# Check code style
flake8 app/
```

## Troubleshooting

### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database errors
```bash
# Delete existing database and reinitialize
rm dev_nukeworks.sqlite
rm dev_nukeworks.sqlite-wal
rm dev_nukeworks.sqlite-shm
flask init-db-cmd
```

### Port already in use
```bash
# Change port in app.py (line with app.run)
# Or find and kill process using port 5000
lsof -ti:5000 | xargs kill -9
```

## What's Implemented

✅ **Complete Infrastructure**
- Flask application factory pattern
- 15 core database models (all tables from spec)
- 9 relationship/junction tables
- Two-tier permission system (Confidential + NED Team)
- User authentication with Flask-Login
- 8 blueprint modules for routes
- Base templates with Bootstrap 5
- Configuration management (dev/prod)

✅ **Core Features**
- User login/logout
- Password management
- Dashboard with statistics
- Vendor list/detail views
- Project list/detail views
- Owner list/detail views
- Admin user management
- Permission checking utilities
- Database initialization script

⏳ **To Be Implemented** (Future Phases)
- Full CRUD operations for all entities
- CRM features (contact logging, roundtable history)
- Network diagram visualization
- PDF report generation
- Excel/CSV import/export
- Database snapshot system
- Advanced search and filtering
- Complete test suite

## Getting Help

1. **README.md** - Comprehensive project documentation
2. **docs/** - 23 detailed specification documents
3. **docs/21_TROUBLESHOOTING.md** - Common issues and solutions
4. **docs/22_IMPLEMENTATION_CHECKLIST.md** - Development roadmap

## Security Reminders

⚠️ **IMPORTANT**:
1. Change default admin password immediately
2. Generate secure SECRET_KEY for production
3. Never commit .env file with secrets
4. Use HTTPS in production (configure separately)
5. Review docs/19_SECURITY.md for security best practices

---

**Setup complete!** You now have a working Flask application with:
- Complete database schema (15 core tables + 9 junction tables)
- Two-tier permission system
- User authentication
- Basic CRUD views
- Admin interface
- Professional project structure

Ready to start building features! 🚀
