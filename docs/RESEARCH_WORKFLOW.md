# Research Workflow — Implementation Plan

## Overview

A manual, clipboard-based workflow that lets a user periodically refresh the database
with public market intelligence gathered by an AI research agent. The user exports a
context file (non-confidential DB snapshot + research instructions), delivers it to an
AI tool of their choice, then imports the structured response back into the app for
one-by-one review before anything is written to the main database.

No direct API integration. No automated scheduling. The user controls when research
runs and what gets accepted.

---

## Confirmed Design Decisions

| Decision | Choice |
|---|---|
| API integration | None — clipboard/file handoff only |
| Entity types in scope | Companies, Projects, Company-Project relationships, Company-Company relationships |
| Personnel | Excluded from v1 |
| AI context | Export current non-confidential DB state so AI can detect changes vs. what we already have |
| Entity matching | Derive slug from name + embed `db_id` in export; AI echoes `db_id` back for existing records |
| Scope | User selects all entities or a chosen subset before export |
| Chunking | Auto-calculate chunk count based on entity volume; user can adjust; files named `research_package_1of3.json` etc. |
| Cross-chunk references | Accepted at import time; staged as new entities/relationships for human review |
| Confidentiality | Export strips all encrypted fields, confidentially-flagged fields, NED-only content, and `is_confidential` relationships |

---

## Confidentiality Filter Rules

The following are **never included** in any export file:

**Project fields excluded:**
- `capex`, `opex`, `fuel_cost`, `lcoe` (all encrypted)
- `mpr_project_id` (internal reference)
- `last_project_interaction_date`, `last_project_interaction_by` (internal activity)
- `primary_firm_contact` (internal personnel link)
- Any field flagged by a `ConfidentialFieldFlag` record for that project

**Company fields excluded:**
- CRM profile: `relationship_strength`, `client_priority`, `client_status`,
  `relationship_notes`, `last_contact_date`, `next_planned_contact_date`,
  `client_near_term_focus`, `client_strategic_objectives`
- `is_mpr_client` (internal business classification)
- `is_internal` (internal flag)
- Any field flagged by a `ConfidentialFieldFlag` record for that company

**Relationships excluded:**
- Any `CompanyRoleAssignment` where `is_confidential = True`
- Any relationship involving an internal company (`is_internal = True`)

**What IS included (public-facing skeleton):**
- Company: `db_id`, `slug`, `company_name`, `company_type`, `website`,
  `headquarters_country`, `roles` (role names only), `notes` (if not confidential)
- Project: `db_id`, `slug`, `project_name`, `location`, `project_status`,
  `licensing_approach`, `configuration`, `project_schedule`, `target_cod`,
  `project_health`, `firm_involvement`, `notes` (if not confidential)
- Relationships: project-company links, company-company links (non-confidential only)

---

## Database Changes

### New table: `research_import_runs`

Tracks each import session (one run = one batch of AI responses, potentially
from multiple chunk files).

```sql
CREATE TABLE research_import_runs (
    run_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name      TEXT NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT (datetime('now')),
    created_by    INTEGER REFERENCES users(user_id),
    status        TEXT NOT NULL DEFAULT 'in_progress',  -- in_progress, complete
    chunk_count   INTEGER DEFAULT 1,
    total_items   INTEGER DEFAULT 0,
    accepted_items INTEGER DEFAULT 0,
    skipped_items  INTEGER DEFAULT 0
);
```

### New table: `research_queue_items`

One row per proposed change. `entity_db_id` is null for new entities the AI found
that don't exist in the DB yet.

```sql
CREATE TABLE research_queue_items (
    item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES research_import_runs(run_id),
    entity_type     TEXT NOT NULL,   -- company, project, relationship
    entity_db_id    INTEGER,         -- null for new entities
    entity_name     TEXT NOT NULL,   -- display label
    change_type     TEXT NOT NULL,   -- new, update, conflict
    proposed_data   TEXT NOT NULL,   -- JSON blob of AI-returned fields
    current_data    TEXT,            -- JSON snapshot of current DB values (null for new)
    changed_fields  TEXT,            -- JSON array of field names that differ
    source_urls     TEXT,            -- JSON array of source URLs from AI
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending, accepted, skipped
    reviewed_at     DATETIME,
    reviewed_by     INTEGER REFERENCES users(user_id),
    review_notes    TEXT
);
```

**Migration:** `016_research_queue.sql`  
**Schema version bump:** 15 → 16

---

## New Code Structure

```
app/
  routes/
    research.py              # New blueprint, prefix /research
  services/
    research_export.py       # Export logic: slug generation, confidentiality filter, chunking
    research_import.py       # Import logic: parsing, entity matching, diffing, queue writing
  models/
    research.py              # ResearchImportRun + ResearchQueueItem ORM models
  templates/
    research/
      index.html             # Main page: export controls + import upload + run history
      run_detail.html        # Review queue for a specific import run
  forms/
    research.py              # ExportForm, ImportForm
migrations/
  016_research_queue.sql
docs/
  research_prompt.txt        # Already exists — will be enhanced
  Research spec.md           # Already exists — used as AI output contract
```

---

## Blueprint Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/research/` | Main page: export config, upload, run history |
| POST | `/research/export` | Generate and download export package(s) |
| POST | `/research/import` | Upload AI response file(s), create import run |
| GET | `/research/runs/<run_id>` | Review queue for a specific run |
| POST | `/research/runs/<run_id>/items/<item_id>/accept` | Accept a queued item |
| POST | `/research/runs/<run_id>/items/<item_id>/skip` | Skip a queued item |
| POST | `/research/runs/<run_id>/accept-all-new` | Bulk accept all "new" items in run |
| POST | `/research/runs/<run_id>/skip-all` | Bulk skip all remaining items in run |

All routes require `@login_required`. Accept/skip/bulk actions also require `@edit_required`.

---

## Phase 1 — Export

### `research_export.py` functions

**`derive_slug(name: str) -> str`**  
Converts a company or project name to a kebab-case slug.
`"NuScale Power, LLC" → "nuscale-power-llc"`

**`get_export_stats(db_session, company_ids=None) -> dict`**  
Returns counts of companies, projects, relationships in scope. Used to calculate
recommended chunk size and display a preview before the user commits to export.

**`build_export_chunks(db_session, company_ids=None, chunk_size=20) -> list[dict]`**  
Core export function. Returns a list of chunk dicts (one per file to generate).
Each chunk contains:
- `metadata` block (chunk number, total chunks, timestamp, scope summary)
- `instructions` block (research prompt text, embedded verbatim)
- `existing_data` block with companies, projects, and relationships for that batch

Grouping logic: companies are sorted by name and divided into batches of `chunk_size`.
Each chunk includes only the projects and relationships linked to that batch's companies.

**Confidentiality filter applied at field level** — the export functions query the DB
normally then strip fields per the rules in the "Confidentiality Filter Rules" section
above before writing them to the output dict.

### Export package format (per chunk file)

```json
{
  "metadata": {
    "exported_at": "2026-04-27T14:00:00Z",
    "chunk": 1,
    "total_chunks": 3,
    "scope": "all",
    "chunk_company_count": 20,
    "app_version": "1.0"
  },
  "instructions": "...full research prompt text...",
  "existing_data": {
    "companies": [
      {
        "db_id": 31,
        "slug": "elementl-power",
        "company_name": "Elementl Power",
        "company_type": "IPP",
        "website": null,
        "headquarters_country": "USA",
        "roles": ["owner_developer"],
        "notes": null
      }
    ],
    "projects": [
      {
        "db_id": 5,
        "slug": "clinch-river-smr",
        "project_name": "Clinch River SMR",
        "location": "Oak Ridge, Tennessee, USA",
        "project_status": "Planning",
        "licensing_approach": "Part 52",
        "project_health": "On Track",
        "notes": null
      }
    ],
    "relationships": [
      {
        "relationship_type": "project_owner",
        "project_db_id": 5,
        "project_slug": "clinch-river-smr",
        "company_db_id": 31,
        "company_slug": "elementl-power"
      }
    ]
  }
}
```

### Research prompt enhancements

The embedded prompt (based on existing `docs/research_prompt.txt`) will be updated to:

1. Tell the AI it is receiving a snapshot of existing data and should compare against it
2. Instruct it to echo `db_id` back for any entity that matches an existing record
3. Instruct it to set `db_id: null` for entities it finds that are not in the existing data
4. Include the full output spec (from `Research spec.md`) inline
5. Add explicit instruction: "Do not invent data. Use null for any value you cannot
   confirm from a public source. Include at least one source URL per entity."

---

## Phase 2 — Import & Staging

### `research_import.py` functions

**`parse_and_stage(json_data: dict, run_id: int, db_session) -> int`**  
Top-level import function. Parses one AI response file, matches entities to DB records,
diffs field values, and writes `ResearchQueueItem` rows. Returns count of items staged.

**`match_company(proposed: dict, db_session) -> Company | None`**  
Attempts to find an existing DB record for the proposed company. Matching strategy:
1. If `db_id` is present and non-null, look up by `company_id` (authoritative)
2. Else, fuzzy-match on `company_name` (case-insensitive, strip punctuation)
3. Return None if no confident match (item will be staged as `new`)

**`match_project(proposed: dict, db_session) -> Project | None`**  
Same strategy as `match_company` using `project_id` / `project_name`.

**`diff_entity(proposed: dict, current_record, entity_type: str) -> tuple[str, list, dict]`**  
Compares proposed fields against current DB values. Returns:
- `change_type`: `"update"` if fields differ, `"conflict"` if the existing DB value was
  manually entered (not previously AI-sourced), `"unchanged"` if nothing differs
- `changed_fields`: list of field names with differences
- `current_snapshot`: dict of current DB values for those fields only

Items with `change_type = "unchanged"` are **not staged** (no point cluttering the queue).

**`apply_queue_item(item: ResearchQueueItem, db_session, applied_by_user_id: int)`**  
Called when a user clicks Accept. Writes the `proposed_data` fields to the main DB record
(or creates a new record for `new` items). Logs the change source as `"AI Research"` in
the notes/audit trail.

### Change type definitions

| change_type | Meaning |
|---|---|
| `new` | Entity/relationship not found in DB — would be a new record |
| `update` | AI has different values for fields that were previously AI-sourced or empty |
| `conflict` | AI disagrees with a field that has a manually-entered value — highest review priority |

---

## Phase 3 — Review UI

### Main research page (`research/index.html`)

Three sections:

**Export section**
- Scope selector: radio buttons for "All entities" vs. "Select specific companies"
  - If "Select specific companies": searchable checklist of company names
- Chunk size control: numeric input, default 20, with helper text showing estimated
  chunk count based on current selection
- "Preview Export" button: shows a summary (N companies, M projects, K relationships,
  will produce X files) without downloading yet
- "Generate Export Package" button: downloads the file(s)

**Import section**
- Run name field (e.g., "April 2026 Quarterly Research")
- File upload (accepts multiple `.json` files — all chunks from one research run)
- "Import & Stage for Review" button

**Run history table**
- Lists all past import runs with: name, date, created by, total/accepted/skipped counts,
  status, link to review queue

### Run detail page (`research/run_detail.html`)

Shows one import run's queue. Layout:

- Summary bar: total items, pending, accepted, skipped; bulk action buttons
- Items grouped into sections:
  - **Conflicts** (shown first — these need most attention)
  - **Updates**
  - **New Entities**
- Each item is a card showing:
  - Entity name and type (badge)
  - For updates/conflicts: side-by-side table of current value vs. proposed value,
    with changed fields highlighted
  - For new entities: all proposed fields displayed
  - Source URLs as clickable links (opens in new tab)
  - Accept / Skip buttons
- After all items in a run are reviewed (accepted or skipped), run status → `complete`

---

## Implementation Order

Work proceeds in this sequence so each phase is independently testable:

1. **Migration** — `016_research_queue.sql`, ORM models, schema version bump to 16
2. **Export service** — `research_export.py`, no UI yet; test via Flask shell
3. **Export UI** — blueprint skeleton, main page export section, download endpoint
4. **Prompt update** — revise `docs/research_prompt.txt` for the new context-aware format
5. **Import service** — `research_import.py`, entity matching, diffing, queue writing
6. **Import UI** — file upload endpoint, run creation
7. **Review UI** — run detail page, accept/skip actions, bulk actions
8. **Navigation** — add Research to the nav bar (NED team + admin only, using existing
   permission pattern)

---

## Permissions

| Action | Required permission |
|---|---|
| View research page and run history | `is_ned_team` or `is_admin` |
| Generate export | `is_ned_team` or `is_admin` |
| Upload import file | `is_ned_team` or `is_admin` |
| Accept/skip queue items | `can_edit()` (i.e., not read-only) + above |

---

## Open Questions (resolve during implementation)

1. **Conflict detection granularity**: Should `conflict` only trigger for fields the user
   has explicitly edited, or for any field that currently has a non-null value? Using
   the `AuditLog` table to detect manual edits would be more precise but adds complexity.
   Simpler default: treat any non-null existing value as potentially manual and flag it.

2. **New company acceptance**: When accepting a `new` company, what roles and additional
   fields should the user be prompted to fill in? Options: (a) accept with AI-provided
   fields only, user edits later via normal company form; (b) show a mini-form inline
   in the review UI. Recommendation: option (a) to keep the review UI simple.

3. **Rejected AI data memory**: Should skipped items be permanently forgotten, or stored
   so the same suggestion doesn't re-appear in the next research run? For v1, store them
   (they're already in `research_queue_items` with `status = skipped`) and note the
   slug in the next export so the AI doesn't keep re-suggesting the same thing.

---

## Files to Create

| File | Notes |
|---|---|
| `migrations/016_research_queue.sql` | Two new tables + schema version bump |
| `app/models/research.py` | `ResearchImportRun`, `ResearchQueueItem` ORM models |
| `app/services/research_export.py` | Export logic |
| `app/services/research_import.py` | Import, matching, diffing logic |
| `app/routes/research.py` | Blueprint with all routes |
| `app/forms/research.py` | `ExportForm`, `ImportForm` |
| `app/templates/research/index.html` | Main page |
| `app/templates/research/run_detail.html` | Review queue |

## Files to Modify

| File | Change |
|---|---|
| `app/models/__init__.py` | Import new research models |
| `app/routes/__init__.py` or `app/__init__.py` | Register research blueprint |
| `app/templates/base.html` | Add Research to nav (NED/admin only) |
| `config.py` | Bump `REQUIRED_SCHEMA_VERSION` to 16 |
| `app/utils/migrations.py` | Bump `APPLICATION_REQUIRED_SCHEMA_VERSION` to 16 |
| `docs/research_prompt.txt` | Rewrite for context-aware format |
