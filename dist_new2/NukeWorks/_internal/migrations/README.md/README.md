# Database Migration System

This directory contains versioned database migration scripts for NukeWorks.

## Overview

The migration system allows the database schema to evolve over time without data loss. It provides:

- **Versioned schema changes** - Sequential migration files
- **Automatic detection** - Application checks for pending migrations on startup
- **Automatic backups** - Creates snapshot before applying migrations
- **Rollback capability** - Restore from backup if migration fails
- **Transaction-based** - All migrations run within transactions
- **Audit trail** - All migrations logged in `schema_version` table

## Directory Structure

```
migrations/
├── README.md                    # This file
├── 001_initial_schema.sql       # Initial database schema
├── 002_add_feature.sql          # Future migration example
└── 003_add_field.sql            # Future migration example
```

## Migration File Naming Convention

**Format:** `{VERSION}_{description}.sql`

- **VERSION**: 3-digit zero-padded number (001, 002, 003, etc.)
- **description**: lowercase with underscores, describes the change
- **Extension**: `.sql`

**Examples:**
- `001_initial_schema.sql`
- `002_add_us_domestic_content.sql`
- `003_add_crm_features.sql`

## CLI Commands

### Check Migration Status

```bash
flask check-migrations
```

Shows current vs. required schema version.

### View Migration History

```bash
flask migration-history
```

Lists all applied migrations with timestamps.

### Apply Pending Migrations

```bash
flask apply-migrations
```

Applies all pending migrations interactively.

## Migration File Template

Every migration must follow this structure:

```sql
-- migrations/002_add_feature.sql
-- Description: What this migration does
-- Version: 2
-- Date: YYYY-MM-DD
-- Author: Your Name

-- IMPORTANT: This migration runs within a transaction
-- If any statement fails, entire migration is rolled back

BEGIN TRANSACTION;

-- ============================================================================
-- MIGRATION STATEMENTS
-- ============================================================================

-- Your DDL/DML statements here
ALTER TABLE projects ADD COLUMN new_field TEXT;

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (2, datetime('now'), 'system', 'Added new_field to projects');

-- ============================================================================
-- COMMIT TRANSACTION
-- ============================================================================

COMMIT;
```

## Creating a New Migration

### Step 1: Determine Next Version Number

Look at existing migrations to find the highest version number, then increment by 1.

```bash
ls migrations/
# If highest is 001_initial_schema.sql, next is 002
```

### Step 2: Create Migration File

```bash
# Create new migration file
touch migrations/002_add_new_feature.sql
```

### Step 3: Write Migration SQL

Use the template above and include:

1. **Header comments** (description, version, date, author)
2. **BEGIN TRANSACTION** statement
3. **Migration statements** (ALTER TABLE, CREATE TABLE, etc.)
4. **Schema version update** (INSERT INTO schema_version)
5. **COMMIT** statement

### Step 4: Test Migration

```bash
# Test on a copy of production database
cp nukeworks_db.sqlite test_db.sqlite
flask apply-migrations  # (configure to use test_db.sqlite)
```

### Step 5: Update Application Version

Edit `config.py`:

```python
REQUIRED_SCHEMA_VERSION = 2  # Increment to match new migration
```

### Step 6: Deploy

1. Commit migration file to version control
2. Update application on network drive
3. Notify users to update

## Migration Best Practices

### DO:

✅ Wrap entire migration in `BEGIN TRANSACTION` / `COMMIT`
✅ Test on copy of production database before deploying
✅ Include descriptive comments
✅ Update `schema_version` table at end
✅ Use `IF NOT EXISTS` for creating tables/indexes
✅ Make migrations idempotent when possible
✅ Keep migrations small and focused
✅ Include data migration for existing records if needed

### DON'T:

❌ Modify existing migration files after deployment
❌ Delete data without careful consideration
❌ Use database-specific features (stick to SQLite standard)
❌ Forget to update `schema_version`
❌ Make breaking changes without transition period

## Common Migration Patterns

### Add Column (Safe)

```sql
ALTER TABLE table_name ADD COLUMN new_column TEXT;
```

### Add Column with Default

```sql
ALTER TABLE table_name ADD COLUMN new_column TEXT DEFAULT 'value';
UPDATE table_name SET new_column = 'calculated_value' WHERE condition;
```

### Create New Table

```sql
CREATE TABLE IF NOT EXISTS new_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_new_table_name ON new_table(name);
```

### Rename Column (Two-Step)

**Migration N: Add new column, copy data**
```sql
ALTER TABLE projects ADD COLUMN new_name TEXT;
UPDATE projects SET new_name = old_name;
```

**Migration N+1: Remove old column (after all users migrated)**
```sql
-- Recreate table without old column
CREATE TABLE projects_new (...);
INSERT INTO projects_new SELECT ... FROM projects;
DROP TABLE projects;
ALTER TABLE projects_new RENAME TO projects;
```

### Change Column Type (Recreate Table)

```sql
-- Step 1: Create new table with updated schema
CREATE TABLE table_new (...);

-- Step 2: Copy data
INSERT INTO table_new SELECT * FROM table_old;

-- Step 3: Drop old table
DROP TABLE table_old;

-- Step 4: Rename new table
ALTER TABLE table_new RENAME TO table_old;

-- Step 5: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_name ON table_old(column);
```

## Rollback Strategy

### Automatic Rollback

Migrations automatically rollback if they fail:

1. Migration executes within transaction
2. If any statement fails, transaction is rolled back
3. Database is restored from automatic backup
4. User is notified of failure

### Manual Rollback

If needed, restore from backup:

```bash
# Find backup in snapshots directory
ls -l snapshots/migration_backup_*.sqlite

# Copy backup over current database
cp snapshots/migration_backup_YYYYMMDD_HHMMSS.sqlite nukeworks_db.sqlite
```

## Troubleshooting

### Error: "Missing migration file for version X"

**Cause:** Migration file is missing or named incorrectly
**Solution:** Ensure migration file exists with correct naming: `00X_description.sql`

### Error: "Migration must contain BEGIN TRANSACTION"

**Cause:** Migration file missing transaction wrapper
**Solution:** Add `BEGIN TRANSACTION` at start and `COMMIT` at end

### Error: "Column already exists"

**Cause:** Migration was partially applied before
**Solution:** Check `schema_version` table to determine actual state, restore from backup if needed

### Error: "Foreign key constraint failed"

**Cause:** Referenced table/record doesn't exist
**Solution:** Ensure foreign key references are valid, or temporarily disable foreign keys

## Schema Version Table

The `schema_version` table tracks all applied migrations:

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    applied_by TEXT,
    description TEXT
);
```

Query migration history:

```sql
SELECT version, applied_date, applied_by, description
FROM schema_version
ORDER BY version;
```

## More Information

See full documentation: `docs/07_MIGRATION_SYSTEM.md`
