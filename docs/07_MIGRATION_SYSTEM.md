# 07_MIGRATION_SYSTEM.md

**Document:** Database Migration System  
**Version:** 1.0  
**Last Updated:** December 4, 2025  
**Related Documents:** `02_DATABASE_SCHEMA.md`, `14_AUDIT_SNAPSHOTS.md`

---

## Table of Contents

1. [Overview](#overview)
2. [Migration Architecture](#migration-architecture)
3. [Migration File Structure](#migration-file-structure)
4. [Migration Process](#migration-process)
5. [Writing Migrations](#writing-migrations)
6. [Version Management](#version-management)
7. [Error Handling](#error-handling)
8. [Testing Migrations](#testing-migrations)

---

## 1. Overview

The migration system allows the database schema to evolve over time without data loss. It provides a structured, versioned approach to applying schema changes across multiple user installations.

### Key Features

- **Versioned schema changes** - Sequential migration files
- **Automatic detection** - Application checks for pending migrations on startup
- **Automatic backups** - Creates snapshot before applying migrations
- **Rollback capability** - Restore from backup if migration fails
- **Transaction-based** - All migrations run within transactions
- **Audit trail** - All migrations logged in Schema_Version table

### Migration Workflow

```
Application Startup
â†"
Check current schema version
â†"
Compare with required version
â†"
If versions match â†' Continue normally
If current > required â†' Show error (app too old)
If current < required â†' Show migration dialog
                        â†"
                        User confirms
                        â†"
                        Create automatic backup
                        â†"
                        Apply migrations in sequence
                        â†"
                        Update Schema_Version
                        â†"
                        Continue normally
```

---

## 2. Migration Architecture

### 2.1 Schema Version Table

```sql
CREATE TABLE Schema_Version (
    version INTEGER PRIMARY KEY,
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by TEXT,
    description TEXT
);

-- Initial entry
INSERT INTO Schema_Version (version, applied_date, applied_by, description)
VALUES (1, CURRENT_TIMESTAMP, 'system', 'Initial schema creation');
```

### 2.2 Version Detection

```python
def get_current_schema_version(db_path):
    """
    Get the current schema version from the database
    Returns 0 if Schema_Version table doesn't exist (new database)
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("""
            SELECT MAX(version) as current_version 
            FROM Schema_Version
        """)
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else 0
        
    except sqlite3.OperationalError:
        # Schema_Version table doesn't exist - this is a new database
        return 0
```

```python
def get_required_schema_version():
    """
    Get the required schema version for this application version
    This is hardcoded in the application
    """
    return APPLICATION_REQUIRED_SCHEMA_VERSION  # e.g., 5
```

### 2.3 Migration Detection

```python
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
```

---

## 3. Migration File Structure

### 3.1 File Naming Convention

```
migrations/
â"œâ"€â"€ 001_initial_schema.sql
â"œâ"€â"€ 002_add_us_domestic_content.sql
â"œâ"€â"€ 003_add_crm_features.sql
â"œâ"€â"€ 004_add_supplier_diversity.sql
â""â"€â"€ 005_enhance_personnel.sql
```

**Naming Rules:**
- Format: `{VERSION}_{description}.sql`
- VERSION: 3-digit zero-padded number (001, 002, etc.)
- description: lowercase with underscores, describes the change
- File extension: `.sql`

### 3.2 Migration File Template

```sql
-- migrations/002_add_us_domestic_content.sql
-- Description: Add US domestic content tracking to Projects table
-- Version: 2
-- Date: 2025-03-15
-- Author: [Developer Name]

-- IMPORTANT: This migration runs within a transaction
-- If any statement fails, entire migration is rolled back

BEGIN TRANSACTION;

-- ============================================================================
-- MIGRATION STATEMENTS
-- ============================================================================

-- Add new columns to Projects table
ALTER TABLE Projects ADD COLUMN us_domestic_content_pct REAL;
ALTER TABLE Projects ADD COLUMN us_domestic_content_notes TEXT;

-- Create index for performance (if needed)
-- CREATE INDEX idx_projects_us_content ON Projects(us_domestic_content_pct);

-- Migrate existing data (if needed)
-- UPDATE Projects SET us_domestic_content_pct = 0.0 WHERE us_domestic_content_pct IS NULL;

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO Schema_Version (version, applied_date, applied_by, description)
VALUES (2, datetime('now'), 'system', 'Added US domestic content tracking');

-- ============================================================================
-- COMMIT TRANSACTION
-- ============================================================================

COMMIT;
```

### 3.3 Migration File Components

**Header Comments:**
- Description of what the migration does
- Version number
- Date created
- Author

**Migration Statements:**
- DDL statements (ALTER TABLE, CREATE TABLE, CREATE INDEX)
- Data migration statements (UPDATE, INSERT)
- Must be SQLite-compatible

**Schema Version Update:**
- Insert record into Schema_Version table
- MUST be included in every migration

**Transaction Management:**
- Wrap entire migration in BEGIN TRANSACTION / COMMIT
- Ensures atomicity

---

## 4. Migration Process

### 4.1 Startup Migration Check

```python
def check_and_apply_migrations(db_path):
    """
    Called on application startup
    Checks for pending migrations and applies them if needed
    """
    try:
        # Get current and required versions
        current_version = get_current_schema_version(db_path)
        required_version = get_required_schema_version()
        
        logging.info(f"Current schema version: {current_version}")
        logging.info(f"Required schema version: {required_version}")
        
        # Check version compatibility
        if current_version == required_version:
            logging.info("Schema is up to date")
            return True
        
        elif current_version > required_version:
            # Database is newer than application
            show_error_dialog(
                title="Database Version Too New",
                message=f"This database (version {current_version}) is newer than this application version (requires version {required_version}).\n\n"
                        f"Please update the application to the latest version.",
                details="You may need to download the latest version from the network drive."
            )
            return False
        
        else:
            # Pending migrations exist
            pending_migrations = get_pending_migrations(current_version, required_version)
            
            # Show migration dialog to user
            if user_confirms_migration(current_version, required_version, pending_migrations):
                apply_migrations(db_path, pending_migrations)
                return True
            else:
                logging.info("User cancelled migration")
                return False
    
    except Exception as e:
        logging.error(f"Migration check failed: {str(e)}")
        show_error_dialog(
            title="Migration Error",
            message="An error occurred while checking database version.",
            details=str(e)
        )
        return False
```

### 4.2 User Confirmation Dialog

```python
def user_confirms_migration(current_version, required_version, pending_migrations):
    """
    Show dialog to user explaining the migration
    
    Returns:
        True if user clicks "Update Database"
        False if user clicks "Cancel"
    """
    migration_list = []
    
    for migration_file in pending_migrations:
        version, description = parse_migration_filename(migration_file)
        migration_list.append(f"• Version {version}: {description}")
    
    dialog = MigrationDialog(
        current_version=current_version,
        required_version=required_version,
        migrations=migration_list
    )
    
    return dialog.show()
```

**Dialog Display:**
```
┌────────────────────────────────────────────────────────────┐
│              DATABASE UPDATE REQUIRED                    │
├────────────────────────────────────────────────────────────┤
│ Your database needs to be updated to work with this      │
│ version of the application.                              │
│                                                          │
│ Current database version: 3                              │
│ Required version: 5                                      │
│                                                          │
│ The following updates will be applied:                   │
│ • Version 4: Add supplier diversity tracking             │
│ • Version 5: Enhanced CRM features                       │
│                                                          │
│ A backup will be created before updating.                │
│                                                          │
│ This process may take a few minutes.                     │
│                                                          │
│ [Cancel]                              [Update Database]  │
└────────────────────────────────────────────────────────────┘
```

### 4.3 Applying Migrations

```python
def apply_migrations(db_path, migration_files):
    """
    Apply a list of migrations in sequence
    Creates backup before starting
    Rolls back if any migration fails
    """
    try:
        # Step 1: Create backup
        logging.info("Creating backup before migration...")
        backup_path = create_migration_backup(db_path)
        logging.info(f"Backup created: {backup_path}")
        
        # Step 2: Apply each migration
        for migration_file in migration_files:
            logging.info(f"Applying migration: {migration_file}")
            
            try:
                apply_single_migration(db_path, migration_file)
                logging.info(f"Successfully applied: {migration_file}")
                
            except Exception as e:
                logging.error(f"Migration failed: {migration_file}")
                logging.error(f"Error: {str(e)}")
                
                # Rollback: restore from backup
                logging.info("Rolling back changes...")
                restore_from_backup(db_path, backup_path)
                
                # Show error to user
                show_migration_error(migration_file, e, backup_path)
                
                raise MigrationError(f"Migration {migration_file} failed: {str(e)}")
        
        # Step 3: Verify final version
        final_version = get_current_schema_version(db_path)
        required_version = get_required_schema_version()
        
        if final_version != required_version:
            raise MigrationError(f"Version mismatch after migration. Expected {required_version}, got {final_version}")
        
        # Step 4: Show success
        show_migration_success(backup_path)
        logging.info("All migrations applied successfully")
        
    except MigrationError:
        raise
    except Exception as e:
        logging.error(f"Unexpected error during migration: {str(e)}")
        raise MigrationError(f"Migration failed: {str(e)}")
```

### 4.4 Applying Single Migration

```python
def apply_single_migration(db_path, migration_file):
    """
    Apply a single migration file
    Migration file must contain BEGIN TRANSACTION and COMMIT
    """
    # Read migration SQL
    migration_path = get_migration_file_path(migration_file)
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # Validate migration SQL
    validate_migration_sql(migration_sql)
    
    # Execute migration
    conn = sqlite3.connect(db_path)
    
    try:
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Execute the migration
        # Note: Migration file contains BEGIN TRANSACTION and COMMIT
        conn.executescript(migration_sql)
        
        conn.close()
        
    except Exception as e:
        conn.close()
        raise e
```

### 4.5 Migration Backup

```python
def create_migration_backup(db_path):
    """
    Create backup before applying migrations
    Separate from regular automated backups
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"migration_backup_{timestamp}.sqlite"
    
    backup_dir = get_snapshot_directory()
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Copy database file
    shutil.copy2(db_path, backup_path)
    
    # Record in database (after copy, in the backup file)
    record_snapshot(
        snapshot_path=backup_path,
        snapshot_type='MIGRATION_BACKUP',
        created_by=None,  # System
        size=os.path.getsize(backup_path),
        description="Automatic backup before schema migration"
    )
    
    return backup_path
```

---

## 5. Writing Migrations

### 5.1 Migration Best Practices

**DO:**
- ✅ Wrap entire migration in BEGIN TRANSACTION / COMMIT
- ✅ Test on copy of production database before deploying
- ✅ Include descriptive comments
- ✅ Update Schema_Version table at end
- ✅ Use IF NOT EXISTS for creating tables/indexes
- ✅ Make migrations idempotent when possible
- ✅ Keep migrations small and focused
- ✅ Include data migration for existing records if needed

**DON'T:**
- ❌ Modify existing migration files after deployment
- ❌ Delete data without careful consideration
- ❌ Use database-specific features (stick to SQLite standard)
- ❌ Forget to update Schema_Version
- ❌ Make breaking changes without transition period

### 5.2 Common Migration Patterns

#### Adding a Column

```sql
-- Safe pattern: Add column with default value
ALTER TABLE Projects ADD COLUMN project_health TEXT DEFAULT 'Unknown';

-- Update existing rows if needed
UPDATE Projects SET project_health = 'On track' WHERE project_status = 'Operating';
```

#### Renaming a Column (Two-Step Process)

**Migration 1: Add new column, copy data**
```sql
-- Version 7: Prepare for column rename
ALTER TABLE Projects ADD COLUMN commercial_operation_date DATE;
UPDATE Projects SET commercial_operation_date = cod WHERE cod IS NOT NULL;

INSERT INTO Schema_Version (version, applied_date, applied_by, description)
VALUES (7, datetime('now'), 'system', 'Added commercial_operation_date column');
```

**Migration 2: Remove old column (later version)**
```sql
-- Version 8: Complete column rename
-- First verify all users have migrated to version 7

-- Create new table without old column
CREATE TABLE Projects_new (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    commercial_operation_date DATE,
    -- ... other columns ...
);

-- Copy data
INSERT INTO Projects_new SELECT 
    project_id, project_name, commercial_operation_date, ...
FROM Projects;

-- Drop old table
DROP TABLE Projects;

-- Rename new table
ALTER TABLE Projects_new RENAME TO Projects;

INSERT INTO Schema_Version (version, applied_date, applied_by, description)
VALUES (8, datetime('now'), 'system', 'Completed cod to commercial_operation_date rename');
```

#### Adding a Table

```sql
-- Use IF NOT EXISTS for safety
CREATE TABLE IF NOT EXISTS New_Table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_new_table_name ON New_Table(name);
```

#### Adding a Relationship

```sql
-- Create new junction table
CREATE TABLE IF NOT EXISTS Entity1_Entity2_Relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity1_id INTEGER NOT NULL,
    entity2_id INTEGER NOT NULL,
    is_confidential BOOLEAN DEFAULT 0,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity1_id) REFERENCES Entity1(entity1_id),
    FOREIGN KEY (entity2_id) REFERENCES Entity2(entity2_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_e1e2_entity1 ON Entity1_Entity2_Relationships(entity1_id);
CREATE INDEX IF NOT EXISTS idx_e1e2_entity2 ON Entity1_Entity2_Relationships(entity2_id);
```

#### Modifying Data

```sql
-- Safe data migration pattern
UPDATE Projects 
SET project_status = 'On Hold' 
WHERE project_status = 'Paused';  -- Rename enum value

-- Add validation
-- (Note: SQLite doesn't support CHECK constraints via ALTER TABLE)
-- Validation should be enforced in application code
```

### 5.3 Migration Validation

```python
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
    if 'Schema_Version' not in migration_sql:
        raise ValidationError("Migration must update Schema_Version table")
    
    # Check for dangerous operations (optional warning)
    if 'DROP TABLE' in migration_sql.upper():
        logging.warning("Migration contains DROP TABLE - ensure data is backed up")
    
    if 'DELETE FROM' in migration_sql.upper():
        logging.warning("Migration contains DELETE - ensure this is intentional")
```

---

## 6. Version Management

### 6.1 Application Version Mapping

```python
# In application code
APPLICATION_VERSION = "1.6.0"
APPLICATION_REQUIRED_SCHEMA_VERSION = 5

# Version history
VERSION_SCHEMA_MAP = {
    "1.0.0": 1,  # Initial release
    "1.1.0": 1,  # Bug fixes, no schema changes
    "1.2.0": 2,  # Added US domestic content
    "1.3.0": 3,  # Added CRM features
    "1.4.0": 3,  # Bug fixes, no schema changes
    "1.5.0": 4,  # Added supplier diversity
    "1.6.0": 5,  # Enhanced personnel tracking
}
```

### 6.2 Schema Version Query

```python
def get_schema_version_info(db_path):
    """
    Get detailed schema version information
    
    Returns:
        {
            'current_version': 5,
            'migration_history': [
                {'version': 1, 'date': '2024-01-15', 'description': 'Initial schema'},
                {'version': 2, 'date': '2024-03-20', 'description': 'Added US domestic content'},
                ...
            ]
        }
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute("""
        SELECT version, applied_date, applied_by, description
        FROM Schema_Version
        ORDER BY version
    """)
    
    history = [dict(row) for row in cursor.fetchall()]
    
    current_version = history[-1]['version'] if history else 0
    
    conn.close()
    
    return {
        'current_version': current_version,
        'migration_history': history
    }
```

---

## 7. Error Handling

### 7.1 Migration Error Dialog

```python
def show_migration_error(migration_file, error, backup_path):
    """
    Show detailed error message when migration fails
    """
    version, description = parse_migration_filename(migration_file)
    
    dialog = ErrorDialog(
        title="Migration Failed",
        message=f"An error occurred while updating the database:\n\n"
                f"Error in migration version {version}:\n"
                f"{str(error)}\n\n"
                f"The database has been restored to its previous state from the automatic backup.",
        details=f"Backup location:\n{backup_path}\n\n"
                f"Please contact your system administrator.",
        icon="error"
    )
    
    dialog.show()
```

**Error Dialog Display:**
```
┌────────────────────────────────────────────────────────────┐
│              MIGRATION FAILED                            │
├────────────────────────────────────────────────────────────┤
│ An error occurred while updating the database:           │
│                                                          │
│ Error in migration version 4:                            │
│ Table 'Projects' already has column 'us_domestic_content'│
│                                                          │
│ The database has been restored to its previous state     │
│ from the automatic backup.                               │
│                                                          │
│ Backup location:                                         │
│ \\networkdrive\...\migration_backup_20251204_100530.sqlite│
│                                                          │
│ Please contact your system administrator.                │
│                                                          │
│ [OK]                                                     │
└────────────────────────────────────────────────────────────┘
```

### 7.2 Common Migration Errors

**Error:** Column already exists
```
sqlite3.OperationalError: duplicate column name: us_domestic_content_pct
```
**Cause:** Migration was partially applied before
**Solution:** Check Schema_Version table to determine actual state

**Error:** Foreign key constraint failed
```
sqlite3.IntegrityError: FOREIGN KEY constraint failed
```
**Cause:** Referenced table/record doesn't exist
**Solution:** Ensure foreign key references are valid, or disable foreign keys temporarily

**Error:** Table doesn't exist
```
sqlite3.OperationalError: no such table: New_Table
```
**Cause:** Previous migration didn't complete
**Solution:** Restore from backup and re-apply migrations

---

## 8. Testing Migrations

### 8.1 Migration Test Process

```python
def test_migration(migration_file, test_db_path):
    """
    Test a migration on a copy of production database
    
    Steps:
    1. Copy production database to test location
    2. Apply migration
    3. Verify schema changes
    4. Run application tests
    5. Check data integrity
    """
    # Create test database copy
    prod_db = "\\\\networkdrive\\nuclear_projects\\nukeworks_db.sqlite"
    test_db = os.path.join(TEST_DIR, "test_migration.sqlite")
    shutil.copy2(prod_db, test_db)
    
    # Get version before migration
    version_before = get_current_schema_version(test_db)
    
    try:
        # Apply migration
        apply_single_migration(test_db, migration_file)
        
        # Get version after migration
        version_after = get_current_schema_version(test_db)
        
        # Verify version incremented
        assert version_after == version_before + 1, "Schema version did not increment correctly"
        
        # Verify schema changes
        verify_schema_changes(test_db, migration_file)
        
        # Run integrity checks
        verify_database_integrity(test_db)
        
        print(f"✓ Migration {migration_file} passed all tests")
        return True
        
    except Exception as e:
        print(f"✗ Migration {migration_file} failed: {str(e)}")
        return False
    
    finally:
        # Clean up test database
        if os.path.exists(test_db):
            os.remove(test_db)
```

### 8.2 Schema Verification

```python
def verify_schema_changes(db_path, migration_file):
    """
    Verify expected schema changes were applied
    """
    conn = sqlite3.connect(db_path)
    
    # Get table list
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get column information for each table
    schema = {}
    for table in tables:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]  # row[1] is column name
        schema[table] = columns
    
    conn.close()
    
    # Verify expected changes based on migration
    # This would be migration-specific logic
    # Example: verify new column exists
    if '002_add_us_domestic_content' in migration_file:
        assert 'Projects' in schema, "Projects table not found"
        assert 'us_domestic_content_pct' in schema['Projects'], "us_domestic_content_pct column not found"
        assert 'us_domestic_content_notes' in schema['Projects'], "us_domestic_content_notes column not found"
```

### 8.3 Data Integrity Checks

```python
def verify_database_integrity(db_path):
    """
    Run SQLite integrity checks on database
    """
    conn = sqlite3.connect(db_path)
    
    # Run integrity check
    cursor = conn.execute("PRAGMA integrity_check")
    result = cursor.fetchone()[0]
    
    if result != "ok":
        raise IntegrityError(f"Database integrity check failed: {result}")
    
    # Check foreign key constraints
    cursor = conn.execute("PRAGMA foreign_key_check")
    violations = cursor.fetchall()
    
    if violations:
        raise IntegrityError(f"Foreign key violations found: {violations}")
    
    conn.close()
```

---

## 9. Migration Checklist

### For Developers Creating Migrations

- [ ] Migration file named correctly: `{VERSION}_{description}.sql`
- [ ] Header comments complete (description, version, date, author)
- [ ] Wrapped in `BEGIN TRANSACTION` / `COMMIT`
- [ ] Includes `Schema_Version` update
- [ ] Tested on copy of production database
- [ ] Verified schema changes are correct
- [ ] Verified existing data still valid
- [ ] No breaking changes (or documented transition plan)
- [ ] Rollback instructions in comments
- [ ] Added to migration directory
- [ ] Updated `APPLICATION_REQUIRED_SCHEMA_VERSION`

### For Administrators Deploying Migrations

- [ ] Backup production database manually (in addition to automatic backup)
- [ ] Test migration on copy of production database
- [ ] Verify all application features work after migration
- [ ] Update application version on network drive
- [ ] Update `version.json` with new version
- [ ] Notify users of update
- [ ] Monitor for issues after deployment

---

## 10. Example Migration Scenarios

### Scenario 1: Adding CRM Features (v1.2 → v1.3)

**Migration 003_add_crm_features.sql:**
```sql
-- migrations/003_add_crm_features.sql
-- Description: Add CRM tracking features (Contact_Log, Roundtable_History)
-- Version: 3
-- Date: 2025-04-15

BEGIN TRANSACTION;

-- Create Contact_Log table
CREATE TABLE IF NOT EXISTS Contact_Log (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    contact_date DATE NOT NULL,
    contact_type TEXT,
    contacted_by INTEGER NOT NULL,
    contact_person_id INTEGER,
    contact_person_freetext TEXT,
    summary TEXT,
    is_confidential BOOLEAN DEFAULT 0,
    follow_up_needed BOOLEAN DEFAULT 0,
    follow_up_date DATE,
    follow_up_assigned_to INTEGER,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (contacted_by) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (contact_person_id) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (follow_up_assigned_to) REFERENCES Personnel(personnel_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);

-- Create Roundtable_History table
CREATE TABLE IF NOT EXISTS Roundtable_History (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    meeting_date DATE NOT NULL,
    discussion TEXT,
    action_items TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(user_id)
);

-- Add CRM fields to Owners_Developers
ALTER TABLE Owners_Developers ADD COLUMN relationship_strength TEXT;
ALTER TABLE Owners_Developers ADD COLUMN relationship_notes TEXT;
ALTER TABLE Owners_Developers ADD COLUMN client_priority TEXT;
ALTER TABLE Owners_Developers ADD COLUMN client_status TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_contact_log_entity ON Contact_Log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_contact_log_date ON Contact_Log(contact_date);
CREATE INDEX IF NOT EXISTS idx_roundtable_entity ON Roundtable_History(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_roundtable_date ON Roundtable_History(meeting_date);

-- Update schema version
INSERT INTO Schema_Version (version, applied_date, applied_by, description)
VALUES (3, datetime('now'), 'system', 'Added CRM features (Contact_Log, Roundtable_History)');

COMMIT;
```

### Scenario 2: Data Type Change (v1.4 → v1.5)

**Migration 005_change_capacity_precision.sql:**
```sql
-- migrations/005_change_capacity_precision.sql
-- Description: Increase precision for thermal_capacity field
-- Version: 5
-- Date: 2025-06-01

BEGIN TRANSACTION;

-- SQLite doesn't support ALTER COLUMN directly
-- Need to recreate table

-- Step 1: Create new table with updated schema
CREATE TABLE Products_new (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    vendor_id INTEGER NOT NULL,
    reactor_type TEXT,
    thermal_capacity DECIMAL(10,3),  -- Changed from REAL to DECIMAL(10,3)
    thermal_efficiency REAL,
    burnup REAL,
    design_status TEXT,
    notes TEXT,
    created_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER,
    modified_date TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES Technology_Vendors(vendor_id),
    FOREIGN KEY (created_by) REFERENCES Users(user_id),
    FOREIGN KEY (modified_by) REFERENCES Users(user_id)
);

-- Step 2: Copy data from old table
INSERT INTO Products_new SELECT * FROM Products;

-- Step 3: Drop old table
DROP TABLE Products;

-- Step 4: Rename new table
ALTER TABLE Products_new RENAME TO Products;

-- Step 5: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_products_vendor ON Products(vendor_id);

-- Update schema version
INSERT INTO Schema_Version (version, applied_date, applied_by, description)
VALUES (5, datetime('now'), 'system', 'Increased precision for thermal_capacity field');

COMMIT;
```

---

## 11. Rollback Strategy

### Automatic Rollback

Migrations automatically rollback if they fail:
1. Migration executes within transaction
2. If any statement fails, transaction is rolled back
3. Database is restored from automatic backup
4. User is notified of failure

### Manual Rollback

If needed, administrators can manually rollback:

```python
def manual_rollback_to_version(db_path, target_version):
    """
    Manually rollback database to specific version
    WARNING: This requires a backup at that version
    """
    # Find backup closest to target version
    backups = find_backups_by_version(target_version)
    
    if not backups:
        raise RollbackError(f"No backup found for version {target_version}")
    
    # Show confirmation dialog
    if not confirm_rollback(target_version, backups[0]):
        return False
    
    # Restore from backup
    restore_from_backup(db_path, backups[0])
    
    # Verify version
    current_version = get_current_schema_version(db_path)
    
    if current_version != target_version:
        raise RollbackError(f"Rollback failed. Expected version {target_version}, got {current_version}")
    
    return True
```

---

## 12. Migration Patterns Reference

### Safe Patterns

✅ **Add nullable column**
```sql
ALTER TABLE TableName ADD COLUMN new_column TEXT;
```

✅ **Add column with default**
```sql
ALTER TABLE TableName ADD COLUMN new_column TEXT DEFAULT 'default_value';
```

✅ **Create new table**
```sql
CREATE TABLE IF NOT EXISTS NewTable (...);
```

✅ **Add index**
```sql
CREATE INDEX IF NOT EXISTS idx_name ON TableName(column_name);
```

### Careful Patterns

⚠️ **Rename column (two-step)**
```sql
-- Migration N: Add new column, copy data
ALTER TABLE TableName ADD COLUMN new_name TEXT;
UPDATE TableName SET new_name = old_name;

-- Migration N+1: Drop old column (after all users migrated)
-- Recreate table without old column
```

⚠️ **Change column type**
```sql
-- Recreate table with new type
CREATE TABLE TableName_new (...);
INSERT INTO TableName_new SELECT ... FROM TableName;
DROP TABLE TableName;
ALTER TABLE TableName_new RENAME TO TableName;
```

### Dangerous Patterns

❌ **Drop column without migration path**
```sql
-- DON'T: Immediate DROP
ALTER TABLE TableName DROP COLUMN old_column;

-- DO: Two-step with warning
-- Migration N: Mark as deprecated
-- Migration N+1: Remove after transition period
```

❌ **Delete data without backup**
```sql
-- DON'T: Delete without safety check
DELETE FROM TableName WHERE condition;

-- DO: Verify data before deleting
-- Manual backup recommended
```

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Dec 4, 2025 | Initial migration system specification | [Author] |

---

**END OF DOCUMENT**