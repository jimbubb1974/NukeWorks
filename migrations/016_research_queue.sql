-- Migration 016: Add research import queue tables
-- Supports the AI research workflow: staged review before DB writes

BEGIN TRANSACTION;

CREATE TABLE research_import_runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name        TEXT NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT (datetime('now')),
    created_by      INTEGER REFERENCES users(user_id),
    status          TEXT NOT NULL DEFAULT 'in_progress',
    chunk_count     INTEGER NOT NULL DEFAULT 1,
    total_items     INTEGER NOT NULL DEFAULT 0,
    accepted_items  INTEGER NOT NULL DEFAULT 0,
    skipped_items   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE research_queue_items (
    item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES research_import_runs(run_id),
    entity_type     TEXT NOT NULL,
    entity_db_id    INTEGER,
    entity_name     TEXT NOT NULL,
    change_type     TEXT NOT NULL,
    proposed_data   TEXT NOT NULL,
    current_data    TEXT,
    changed_fields  TEXT,
    source_urls     TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    reviewed_at     DATETIME,
    reviewed_by     INTEGER REFERENCES users(user_id),
    review_notes    TEXT
);

CREATE INDEX idx_research_queue_run ON research_queue_items(run_id);
CREATE INDEX idx_research_queue_status ON research_queue_items(run_id, status);

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (
    16,
    datetime('now'),
    'system',
    'Add research_import_runs and research_queue_items tables for AI research workflow'
);

COMMIT;
