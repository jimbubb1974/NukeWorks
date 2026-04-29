-- Migration 019: Add relationship_strength to external_personnel
-- Values: Strong, Medium, Skeptical, Unaware

BEGIN TRANSACTION;

ALTER TABLE external_personnel ADD COLUMN relationship_strength TEXT;

INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (
    19,
    datetime('now'),
    'system',
    'Add relationship_strength field to external_personnel (Strong/Medium/Skeptical/Unaware)'
);

COMMIT;
