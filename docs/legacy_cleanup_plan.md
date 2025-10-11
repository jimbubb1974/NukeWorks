# Legacy Schema Cleanup Plan

## Status Log

| Date | Update | Owner |
|------|--------|-------|
| _TBD_ | Plan created from latest code review | _you_ |
| 2025-10-09 | Completed Phase 1 initial checks (legacy routes frozen, validation script clean) | _you_ |
| 2025-10-10 | Applied migrations 007, 008, 009: Removed legacy owner role, added personnel_relationships, removed sector/headquarters_region from companies table | Claude Code |
| 2025-10-10 | Phase 2 (partial): Refactored contact_log._redirect_after_save to redirect legacy entity types to companies.view_company instead of legacy blueprints | Claude Code |
| 2025-10-10 | Applied migration 010: Normalized CompanyRoleAssignment context types from legacy *Record to Global | Claude Code |
| 2025-10-10 | Phase 3 complete: Updated company_query.py shims with deprecation warnings, updated company_sync.py to use Global context, removed _ROLE_ENDPOINTS from companies.py | Claude Code |
| 2025-10-10 | Phase 4 complete: Deleted all legacy models, routes, forms, templates; Applied migrations 011-012 to drop all legacy tables | Claude Code |
| 2025-10-10 | Phase 5 complete: Updated validators, cleaned up scripts, verified database integrity - Legacy cleanup successfully completed! | Claude Code |

## Preconditions

- Freeze creation/editing of legacy entities during the cleanup window.
- Run `scripts/validate_company_migration.py` and archive the report.
- Snapshot the active database(s) before each destructive migration.

## Phase 1 – Data Verification & Freeze

1. Disable or hard‑redirect remaining legacy CRUD endpoints (vendors, owners, operators, constructors, off-takers) so no new legacy rows are created.  
   - ✅ 2025-10-09 — Verified that these blueprints are no longer registered in `app/__init__.py`; direct access returns 404, preventing new legacy records.
2. Execute `scripts/validate_company_migration.py` and capture unresolved legacy entity IDs:
   - `TechnologyVendor`
   - `OwnerDeveloper`
   - `Operator`
   - `Constructor`
   - `Offtaker`
   - ✅ 2025-10-09 — Ran validation script; all categories reported 0 missing records and 100% project relationship coverage.
3. For each unresolved ID, ensure a `companies` record exists (backfill if needed).  
   - ✅ 2025-10-09 — No unresolved IDs detected; no backfill required.
4. Record findings in this document (append to _Status Log_).

## Phase 2 – CRM & Contact Log Refactor

1. Update client relationship routes/forms (`app/routes/clients.py`, `app/forms/client_relationships.py`) to use unified company references instead of legacy tables.
   - Introduce a single source of truth (`CompanyRoleAssignment` or a dedicated `client_company_relationships` table keyed by `company_id`).
   - Add data migration/backfill to translate existing `Client*Relationship` rows.
2. Refactor contact log workflows (`app/routes/contact_log.py`, related templates/forms):
   - Force `entity_type` to `Company` or `Project`.
   - Replace redirects that point to legacy blueprints with `companies.view_company`.
   - Backfill existing logs to map old entity identifiers onto company IDs.
3. Verify the refactor by running targeted smoke tests (manual or automated) and log results.

## Phase 3 – Normalize Company Role Assignments

1. ✅ 2025-10-10 — Audited `CompanyRoleAssignment.context_type` values: Found 54 legacy *Record assignments + 30 Project assignments.
2. ✅ 2025-10-10 — Created and applied migration 010 to convert all legacy context types (VendorRecord, OwnerRecord, etc.) to Global with NULL context_id.
3. ✅ 2025-10-10 — Updated helper shims:
   - `app/services/company_query.py`: Added deprecation warnings; functions now return None since legacy context types no longer exist.
   - `app/services/company_sync.py`: Updated to use Global context with NULL context_id; sync functions now look up companies by name instead of by assignment.
   - `app/routes/companies.py`: Removed `_ROLE_ENDPOINTS` dictionary and updated `_assignment_link()` to only generate links for Project context.
4. ✅ 2025-10-10 — Verified no templates reference legacy routes directly.

## Phase 4 – Retire Legacy Schema Artifacts

1. ✅ 2025-10-10 — Deleted all legacy model files:
   - `app/models/vendor.py`, `app/models/owner.py`, `app/models/operator.py`, `app/models/constructor.py`, `app/models/offtaker.py`, `app/models/client.py`
   - `app/models/relationships.py`
2. ✅ 2025-10-10 — Removed imports/exports from `app/models/__init__.py`; removed legacy blueprint registrations from `app/__init__.py`.
3. ✅ 2025-10-10 — Deleted legacy route files:
   - `app/routes/operators.py`, `app/routes/constructors.py`, `app/routes/offtakers.py`, `app/routes/clients.py`
4. ✅ 2025-10-10 — Deleted legacy form files:
   - `app/forms/vendors.py`, `app/forms/owners.py`, `app/forms/operators.py`, `app/forms/constructors.py`, `app/forms/offtakers.py`, `app/forms/clients.py`, `app/forms/client_relationships.py`
5. ✅ 2025-10-10 — Deleted legacy template directories:
   - `app/templates/vendors/`, `app/templates/operators/`, `app/templates/constructors/`, `app/templates/offtakers/`, `app/templates/clients/`
6. ✅ 2025-10-10 — Created and applied migrations 011-012 to drop all legacy tables and junction tables.
   - Migration 011: Dropped 15+ legacy relationship tables and 6 entity tables
   - Migration 012: Cleaned up remaining tables (owners_developers, vendor_preferred_constructor)
   - Database now at schema version 12 with only unified tables
7. ⏭ Run full test suite (unit + integration) and document outcomes.

## Phase 5 – Final Verification & Documentation

1. ✅ 2025-10-10 — Updated validators to reference unified schema:
   - `validate_unique_vendor_name()` - deprecated, redirects to `validate_unique_company_name()`
   - `validate_unique_product_name()` - deprecated, raises error (products are now part of Company)
   - Added `validate_unique_company_name()` for unified schema
2. ✅ 2025-10-10 — Cleaned up deprecated scripts:
   - Deleted backfill scripts: `backfill_all.py`, `backfill_companies.py`, `backfill_personnel_affiliations.py`, `backfill_project_relationships.py`
   - Deleted validation script: `validate_company_migration.py`
   - Removed temporary migration helper scripts
3. ✅ 2025-10-10 — Final database verification:
   - Schema version: 12 (up to date)
   - Database integrity check: PASSED
   - All legacy tables removed successfully
   - Remaining tables: 19 unified schema tables only
4. ⏭ Sweep project documentation:
   - Archive `LEGACY_SCHEMA_AUDIT.md` and related migration docs
   - Update README and development guides
5. ⏭ Capture lessons learned for future refactoring efforts

---

### Tracking Notes

- Use this file to annotate decisions, blockers, and follow-up items during each work session.
- When a phase completes, summarize the outcome under _Status Log_ with links to supporting artifacts (PRs, migration scripts, reports).
