-- Migration 010: Remove meeting_date and convert created_date to datetime timestamp
-- This changes roundtable entries to be timestamped automatically when saved

-- SQLite doesn't support ALTER COLUMN, so we need to:
-- 1. Create new table with updated schema
-- 2. Copy data (converting created_date to datetime)
-- 3. Drop old table
-- 4. Rename new table

-- Step 1: Create new table with updated schema
CREATE TABLE roundtable_history_new (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    discussion TEXT,
    action_items TEXT,
    next_steps TEXT,
    client_near_term_focus TEXT,
    mpr_work_targets TEXT,
    created_by INTEGER,
    created_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (user_id)
);

-- Step 2: Copy existing data
-- Convert created_date (DATE) to created_timestamp (DATETIME)
INSERT INTO roundtable_history_new (
    history_id,
    entity_type,
    entity_id,
    discussion,
    action_items,
    next_steps,
    client_near_term_focus,
    mpr_work_targets,
    created_by,
    created_timestamp
)
SELECT 
    history_id,
    entity_type,
    entity_id,
    discussion,
    action_items,
    next_steps,
    client_near_term_focus,
    mpr_work_targets,
    created_by,
    datetime(created_date || ' 00:00:00')
FROM roundtable_history;

-- Step 3: Drop old table
DROP TABLE roundtable_history;

-- Step 4: Rename new table
ALTER TABLE roundtable_history_new RENAME TO roundtable_history;

-- Step 5: Recreate indexes
CREATE INDEX idx_roundtable_entity ON roundtable_history (entity_type, entity_id);
CREATE INDEX idx_roundtable_created ON roundtable_history (created_timestamp);




