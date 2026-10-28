-- Migration 021: Company documents (file attachments)
-- Files live on disk next to the database; this table holds metadata only.

BEGIN TRANSACTION;

CREATE TABLE company_documents (
    document_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id        INTEGER NOT NULL REFERENCES companies(company_id),
    title             TEXT NOT NULL,
    description       TEXT,
    category          TEXT,
    access_level      TEXT NOT NULL DEFAULT 'standard',
    original_filename TEXT NOT NULL,
    stored_filename   TEXT NOT NULL UNIQUE,
    mime_type         TEXT,
    size_bytes        INTEGER NOT NULL DEFAULT 0,
    sha256            TEXT,
    uploaded_by       INTEGER REFERENCES users(user_id),
    uploaded_at       DATETIME NOT NULL DEFAULT (datetime('now')),
    is_deleted        INTEGER NOT NULL DEFAULT 0,
    deleted_at        DATETIME,
    deleted_by        INTEGER REFERENCES users(user_id)
);

CREATE INDEX idx_company_documents_company ON company_documents(company_id, is_deleted);

INSERT INTO schema_version (version, applied_date, applied_by, description)
SELECT 21, datetime('now'), 'system', 'Add company_documents table'
WHERE NOT EXISTS (SELECT 1 FROM schema_version WHERE version = 21);

COMMIT;
