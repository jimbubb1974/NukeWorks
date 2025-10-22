Legacy cleanup plan: unify Owner/Developer and remove old structures

Scope

- Normalize legacy role_code 'owner' to unified 'developer'
- Deduplicate assignments after normalization
- Drop any lingering legacy tables (safe if already dropped)
- Add a protective uniqueness index to prevent duplicates

Why this is needed

- Older seeds/migrations used role_code 'owner' while the unified app uses 'developer'. Mixed data caused invisible relationships and duplicate checks to misfire.

High-level steps

1. Ensure the unified role exists
2. Remap all 'owner' assignments → 'developer'
3. Delete now-redundant 'owner' assignments that would collide with existing 'developer' rows
4. Drop legacy 'owner' role row
5. Drop legacy tables if they still exist (no-op if already removed)
6. Add a uniqueness index on company_role_assignments (company_id, role_id, context_type, context_id)
7. Optional: run integrity checks and VACUUM

Runbook (SQLite)

1. Stop the app.
2. Back up the database file.
3. Execute the migration SQL:
   - Using sqlite3 CLI: sqlite3 path/to/db.sqlite < migrations/013_owner_developer_cleanup.sql
4. Start the app and verify:
   - Project pages show Owner/Developer relationships
   - Adding Owner/Developer does not falsely report duplicates

Verification checklist

- company_roles contains 'developer' and does NOT contain 'owner'
- company_role_assignments has no rows referencing a role_code of 'owner'
- Unique index exists: idx_cra_unique(company_id, role_id, context_type, context_id)
- No legacy tables remain (owners_developers, owner_developers, etc.)

Rollback

- Restore the database backup if needed.

Notes

- The UI label can remain "Owner/Developer" but the stored role_code must be 'developer'.
- The app accepts legacy 'owner' only as a display alias (read-only). All writes should use 'developer'.

