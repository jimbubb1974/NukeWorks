# 01_ARCHITECTURE.md - System Architecture

**Document Version:** 1.0  
**Last Updated:** December 4, 2025

**Related Documents:**
- `00_MASTER_SPECIFICATION.md` - Overview
- `02_DATABASE_SCHEMA.md` - Data structures
- `19_SECURITY.md` - Security considerations

---

## Overview

NukeWorks is a standalone desktop application with a web-based interface, designed for 20-50 users accessing a shared SQLite database on a Windows network drive.

**Key Architectural Decisions:**
- File-based SQLite database (not client-server)
- Local Flask web server per user
- Browser-based UI (localhost)
- Standalone .exe with embedded Python runtime

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Deployment Architecture](#deployment-architecture)
3. [Application Structure](#application-structure)
4. [Database Configuration](#database-configuration)
5. [Concurrency Handling](#concurrency-handling)
6. [Packaging & Distribution](#packaging--distribution)
7. [Performance Considerations](#performance-considerations)

---

## Technology Stack

### Backend

**Core:**
- **Python:** 3.9+
- **Web Framework:** Flask 2.3+
- **Database:** SQLite 3
- **ORM:** SQLAlchemy 2.0+ (recommended)

**Authentication & Security:**
- **Password Hashing:** bcrypt or Werkzeug security
- **Session Management:** Flask-Login or Flask-Session
- **CSRF Protection:** Flask-WTF

**Additional Libraries:**
- **Date/Time:** python-dateutil
- **File Operations:** pathlib, shutil
- **Network Operations:** requests (for update checking)

### Frontend

**Core Technologies:**
- **HTML5:** Semantic markup
- **CSS3:** Modern styling, flexbox, grid
- **JavaScript:** ES6+ (no transpilation needed)

**Optional Frameworks:**
- **CSS Framework:** Bootstrap 5 (recommended for MVP)
- **JavaScript Libraries:**
  - Vis.js or Cytoscape.js (network diagram)
  - Optional: Alpine.js for interactivity (lightweight)

**No Build Process Required** (for MVP)

### Reports & Export

**PDF Generation:**
- **Primary:** ReportLab 4.0+ or WeasyPrint 59+
- **Image Handling:** Pillow (PIL)

**Excel/CSV:**
- **Excel Export:** openpyxl 3.1+ or xlsxwriter
- **CSV Import:** Python csv module or pandas
- **CSV Parsing:** Standard library csv module

### Network Diagram

**Visualization Library:**
- **Option 1:** Vis.js 9+ (force-directed graphs)
- **Option 2:** Cytoscape.js 3+ (network visualization)
- **Recommendation:** Vis.js for simpler integration

### Packaging

**Executable Creation:**
- **PyInstaller:** 5.13+ (creates standalone .exe)
- **Alternative:** cx_Freeze (if PyInstaller issues)

**Target Platform:**
- Windows 10/11 (64-bit)

---

## Deployment Architecture

### User Machine Setup

```
User's Desktop
├── NukeWorks.exe (standalone executable)
│   ├── Embedded Python runtime
│   ├── All dependencies bundled
│   └── Application code
│
├── Config file (local)
│   └── %APPDATA%\NukeWorks\config.json
│
└── Browser (Chrome/Edge/Firefox)
    └── Opens to http://localhost:5000
```

### Network Drive Setup

```
\\networkdrive\nuclear_projects\
│
├── nukeworks_db.sqlite (shared database)
│   └── Accessed by all users
│
├── snapshots\ (automatic backups)
│   ├── nukeworks_db_backup_20251201_020000.sqlite
│   └── nukeworks_db_backup_20251202_020000.sqlite
│
└── application\ (update distribution)
    ├── NukeWorks_v1.6.0.exe (latest)
    ├── NukeWorks_v1.5.0.exe (previous)
    └── version.json (version metadata)
```

### Application Flow

```
1. User double-clicks NukeWorks.exe
   ↓
2. Application starts Flask server on localhost:5000
   ↓
3. Application auto-opens default browser to localhost:5000
   ↓
4. User sees login screen
   ↓
5. User authenticates
   ↓
6. Application connects to \\networkdrive\...\nukeworks_db.sqlite
   ↓
7. User interacts with web interface
   ↓
8. All users share same database file
```

### Multi-User Scenario

```
User A's Machine          User B's Machine          User C's Machine
├── NukeWorks.exe        ├── NukeWorks.exe        ├── NukeWorks.exe
├── Flask :5000          ├── Flask :5000          ├── Flask :5000
└── Browser              └── Browser              └── Browser
        ↓                        ↓                        ↓
        └────────────────────────┴────────────────────────┘
                                 ↓
                    \\networkdrive\nuclear_projects\
                         nukeworks_db.sqlite
                    
                    [SQLite WAL mode for concurrency]
```

---

## Application Structure

### Recommended Project Layout

```
nukeworks/
├── app.py (main Flask application)
├── config.py (configuration)
├── requirements.txt (Python dependencies)
│
├── models/ (database models)
│   ├── __init__.py
│   ├── user.py
│   ├── vendor.py
│   ├── project.py
│   └── ... (other models)
│
├── routes/ (Flask routes)
│   ├── __init__.py
│   ├── auth.py (login/logout)
│   ├── vendors.py (vendor CRUD)
│   ├── projects.py (project CRUD)
│   ├── crm.py (CRM features)
│   ├── reports.py (report generation)
│   └── admin.py (admin functions)
│
├── services/ (business logic)
│   ├── __init__.py
│   ├── permissions.py (access control)
│   ├── reports.py (report generation)
│   ├── imports.py (Excel/CSV import)
│   └── snapshots.py (backup management)
│
├── templates/ (Jinja2 templates)
│   ├── base.html
│   ├── dashboard.html
│   ├── vendors/
│   │   ├── list.html
│   │   ├── detail.html
│   │   └── form.html
│   └── ... (other templates)
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── main.js
│   │   └── network-diagram.js
│   └── images/
│       └── logo.png
│
├── migrations/ (database migrations)
│   ├── 001_initial_schema.sql
│   ├── 002_add_us_domestic_content.sql
│   └── ... (future migrations)
│
├── tests/ (test suite)
│   ├── test_models.py
│   ├── test_routes.py
│   ├── test_permissions.py
│   └── ... (other tests)
│
└── utils/ (utility functions)
    ├── __init__.py
    ├── db.py (database utilities)
    ├── audit.py (audit logging)
    └── validators.py (data validation)
```

### Main Application Entry Point

```python
# app.py

import webbrowser
from threading import Timer
from flask import Flask, render_template
from flask_login import LoginManager
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import routes
from routes import auth, vendors, projects, crm, reports, admin
app.register_blueprint(auth.bp)
app.register_blueprint(vendors.bp)
app.register_blueprint(projects.bp)
app.register_blueprint(crm.bp)
app.register_blueprint(reports.bp)
app.register_blueprint(admin.bp)

# Initialize database
from utils.db import init_db, check_migrations
init_db(app.config['DATABASE_PATH'])
check_migrations(app.config['DATABASE_PATH'])

# Open browser after short delay
def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Check if running from PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        Timer(1, open_browser).start()
    
    # Start Flask server
    app.run(host='127.0.0.1', port=5000, debug=False)
```

---

## Database Configuration

### SQLite Configuration for Network Drives

**Critical Settings:**

```python
# config.py

import os
import sqlite3

class Config:
    # Database location
    DATABASE_PATH = os.getenv('NUKEWORKS_DB_PATH', 
                              r'\\networkdrive\nuclear_projects\nukeworks_db.sqlite')
    
    # SQLite connection settings
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    SECRET_KEY = os.urandom(32)  # Generate per installation
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 28800  # 8 hours
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
```

**Connection Helper:**

```python
# utils/db.py

import sqlite3
from contextlib import contextmanager

def get_db_connection(db_path, timeout=30.0):
    """
    Get database connection with proper settings for network drive
    
    Args:
        db_path: Path to SQLite database file
        timeout: Seconds to wait for lock (default 30)
    
    Returns:
        sqlite3.Connection object
    """
    conn = sqlite3.connect(
        db_path,
        timeout=timeout,
        isolation_level='DEFERRED',  # Reduces lock contention
        check_same_thread=False
    )
    
    # Enable WAL mode for better concurrent access
    conn.execute('PRAGMA journal_mode=WAL')
    
    # Enable foreign keys
    conn.execute('PRAGMA foreign_keys=ON')
    
    # Set busy timeout
    conn.execute(f'PRAGMA busy_timeout={int(timeout * 1000)}')
    
    return conn


@contextmanager
def get_db_session(db_path):
    """Context manager for database sessions"""
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### WAL Mode Benefits

**Write-Ahead Logging (WAL) mode provides:**
- Better concurrency (readers don't block writers)
- Better performance on network drives
- Atomic commits
- Crash recovery

**Trade-offs:**
- Creates .wal and .shm files alongside main database
- All files must be on same network share
- Slightly more complex backup (need to checkpoint)

---

## Concurrency Handling

### Optimistic Locking Strategy

**Implementation:**

```python
# models/base.py

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class TimestampMixin:
    """Mixin for timestamp-based optimistic locking"""
    created_date = Column(DateTime, default=datetime.now, nullable=False)
    modified_date = Column(DateTime, onupdate=datetime.now)
    
    def check_concurrent_modification(self, original_modified_date):
        """
        Check if record was modified by another user
        
        Args:
            original_modified_date: Timestamp when user loaded the record
        
        Raises:
            ConcurrentModificationError if record was modified
        """
        if self.modified_date and original_modified_date:
            if self.modified_date > original_modified_date:
                raise ConcurrentModificationError(
                    f"Record was modified by another user at {self.modified_date}"
                )
```

**Usage in Routes:**

```python
# routes/projects.py

@app.route('/projects/<int:project_id>/edit', methods=['POST'])
@login_required
def save_project(project_id):
    project = db.query(Projects).get_or_404(project_id)
    
    # Get original timestamp from hidden form field
    original_modified = request.form.get('original_modified_date')
    
    try:
        # Check for concurrent modifications
        project.check_concurrent_modification(original_modified)
        
        # Update fields
        project.project_name = request.form.get('project_name')
        # ... other fields
        
        project.modified_by = current_user.user_id
        project.modified_date = datetime.now()
        
        db.commit()
        flash('Project saved successfully', 'success')
        
    except ConcurrentModificationError as e:
        flash(str(e), 'error')
        return render_template('projects/conflict.html', 
                             project=project,
                             user_changes=request.form)
    
    return redirect(url_for('view_project', project_id=project_id))
```

### Database Lock Handling

**Retry Logic:**

```python
# utils/db.py

import time
from sqlite3 import OperationalError

def execute_with_retry(conn, sql, params=None, max_retries=5):
    """
    Execute SQL with automatic retry on database lock
    
    Args:
        conn: Database connection
        sql: SQL statement
        params: Query parameters
        max_retries: Maximum retry attempts
    
    Returns:
        Cursor object
    
    Raises:
        OperationalError if all retries exhausted
    """
    for attempt in range(max_retries):
        try:
            if params:
                return conn.execute(sql, params)
            else:
                return conn.execute(sql)
        except OperationalError as e:
            if 'database is locked' in str(e) and attempt < max_retries - 1:
                wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                time.sleep(wait_time)
                continue
            raise
```

---

## Packaging & Distribution

### PyInstaller Configuration

**Spec File (nukeworks.spec):**

```python
# nukeworks.spec

import sys
from pathlib import Path

# Analysis
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('migrations', 'migrations'),
        ('config.py', '.'),
    ],
    hiddenimports=[
        'flask',
        'sqlite3',
        'sqlalchemy',
        'werkzeug',
        'jinja2',
        'wtforms',
        'flask_login',
        'openpyxl',
        'reportlab',
        # Add other dependencies
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # Exclude unused heavy dependencies
        'numpy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NukeWorks',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/images/icon.ico',  # Application icon
    version='version_info.txt'  # Version information
)
```

**Build Command:**

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller nukeworks.spec

# Output: dist/NukeWorks.exe
```

### Version Information

**version_info.txt:**

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [StringStruct('CompanyName', 'Your Company'),
           StringStruct('FileDescription', 'NukeWorks - Nuclear Project Database'),
           StringStruct('FileVersion', '1.0.0'),
           StringStruct('InternalName', 'NukeWorks'),
           StringStruct('LegalCopyright', 'Copyright (C) 2025'),
           StringStruct('OriginalFilename', 'NukeWorks.exe'),
           StringStruct('ProductName', 'NukeWorks'),
           StringStruct('ProductVersion', '1.0.0')])
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
```

### Update Distribution

**version.json (on network drive):**

```json
{
  "latest_version": "1.6.0",
  "release_date": "2025-12-01",
  "download_url": "\\\\networkdrive\\nuclear_projects\\application\\NukeWorks_v1.6.0.exe",
  "release_notes": "Added CRM features, improved network diagram performance, bug fixes",
  "required_schema_version": 9,
  "breaking_changes": false,
  "minimum_compatible_version": "1.4.0",
  "file_size_bytes": 45000000,
  "sha256_checksum": "a1b2c3..."
}
```

**Update Check (in application):**

```python
# utils/updates.py

import requests
import json
from packaging import version

CURRENT_VERSION = "1.5.0"
VERSION_URL = r'\\networkdrive\nuclear_projects\application\version.json'

def check_for_updates():
    """Check if newer version available"""
    try:
        with open(VERSION_URL, 'r') as f:
            version_info = json.load(f)
        
        latest = version_info['latest_version']
        
        if version.parse(latest) > version.parse(CURRENT_VERSION):
            return {
                'update_available': True,
                'latest_version': latest,
                'release_date': version_info['release_date'],
                'release_notes': version_info['release_notes'],
                'download_url': version_info['download_url']
            }
        
        return {'update_available': False}
        
    except Exception as e:
        print(f"Update check failed: {e}")
        return {'update_available': False, 'error': str(e)}
```

---

## Performance Considerations

### Database Performance

**Indexes (defined in schema):**
```sql
-- Critical indexes for performance
CREATE INDEX idx_projects_status ON Projects(project_status);
CREATE INDEX idx_projects_location ON Projects(location);
CREATE INDEX idx_vendors_name ON Technology_Vendors(vendor_name);
CREATE INDEX idx_audit_log_timestamp ON Audit_Log(timestamp);
CREATE INDEX idx_audit_log_table_record ON Audit_Log(table_name, record_id);
```

**Query Optimization:**
- Use `EXPLAIN QUERY PLAN` to analyze slow queries
- Avoid `SELECT *` - specify needed columns
- Use proper JOINs instead of multiple queries
- Implement pagination for large result sets

### Caching Strategy

**Session Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_system_setting(setting_name, default=None):
    """Cache system settings in memory"""
    setting = db.query(System_Settings).filter_by(
        setting_name=setting_name
    ).first()
    
    return setting.setting_value if setting else default
```

**Frontend Caching:**
- Browser caching for static assets (CSS, JS, images)
- Cache-Control headers for appropriate resources
- Version static files to bust cache on updates

### Network Latency Mitigation

**Strategies:**
- Minimize database round-trips (batch operations)
- Use connection pooling
- Implement lazy loading for large datasets
- Show loading indicators for long operations
- Consider client-side caching for reference data

---

## Summary

### Architecture Highlights

- ✅ **Standalone executable** - No installation required
- ✅ **Web-based UI** - Modern, familiar interface
- ✅ **Shared SQLite database** - Simple, no database server
- ✅ **Concurrent access** - WAL mode + optimistic locking
- ✅ **Easy updates** - Copy new .exe to network drive

### Key Decisions Rationale

| Decision | Rationale |
|----------|-----------|
| SQLite vs PostgreSQL | 1-2 concurrent users typical, simpler deployment |
| Local server per user | No server management, works offline |
| PyInstaller | Single .exe, no Python installation needed |
| Flask | Lightweight, flexible, well-documented |
| WAL mode | Better concurrency on network drives |
| Optimistic locking | Rare conflicts, better UX than pessimistic |

### Next Steps

1. Set up development environment
2. Create project structure
3. Implement database layer
4. Build Flask application
5. Test on network drive
6. Package with PyInstaller
7. Deploy to users

---

**Document End**