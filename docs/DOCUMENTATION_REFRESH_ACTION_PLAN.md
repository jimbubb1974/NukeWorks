# Documentation Refresh Action Plan

## Overview

This document outlines the systematic approach to refresh and consolidate documentation to align with the current implementation state. The codebase has evolved significantly with company unification, per-field encryption, and database selection features that need to be reflected in the specifications.

**Total Actions:** 13 items
**Estimated Time:** 4-6 hours
**Priority:** Medium (nice-to-have, non-blocking)

---

## SECTION 1: CRITICAL CLARIFICATIONS (Update Existing Specs)

### ACTION 1: Update 02_DATABASE_SCHEMA.md
**Priority:** HIGH
**Time:** 45-60 minutes
**File:** `docs/02_DATABASE_SCHEMA.md`

**Current State:** Spec describes unified schema as if migration is complete

**Changes Required:**

1. **Add "Migration Status" section at top:**
   ```markdown
   ## Migration Status (October 2025)

   **Current State: WORK IN PROGRESS**

   The application is currently running with BOTH legacy and unified schemas active.
   This is intentional during the transition from separate vendor/owner/operator/etc.
   tables to a unified company schema with role assignments.

   ### Timeline:
   - Dev/Staging: Unified schema implemented, backfill tested ✓
   - Production: Awaiting migration execution (see docs/MIGRATION_PLAN.md)
   - Post-Migration: Legacy tables retained for 3-6 months before cleanup

   ### Key Point:
   Developers should expect BOTH schemas in database queries, relationships,
   and business logic during this transition period.
   ```

2. **Add Project encryption columns to schema section:**
   - Add section "Encrypted Fields (Phase 3 In Progress)"
   - Document new columns: `capex_encrypted`, `opex_encrypted`, `fuel_cost_encrypted`, `lcoe_encrypted`
   - Include encryption mechanism and key types

3. **Update table count if necessary:**
   - Verify if legacy tables are still documented or removed from count
   - Clarify which tables are "legacy/deprecated" vs. "active"

**Testing:**
- [ ] Cross-reference against actual `app/models/company.py` for unified tables
- [ ] Cross-reference against `app/models/project.py` for encryption columns
- [ ] Verify relationship tables still accurate

---

### ACTION 2: Update 03_DATABASE_RELATIONSHIPS.md
**Priority:** HIGH
**Time:** 40-50 minutes
**File:** `docs/03_DATABASE_RELATIONSHIPS.md`

**Current State:** Partially describes both legacy and new relationships, confusing

**Changes Required:**

1. **Clarify transition status:**
   - Add explicit section: "These relationships describe the UNIFIED schema endpoint"
   - Include note: "Legacy relationships still active during transition"

2. **Clean up deprecated table mentions:**
   - If legacy tables still exist, keep in separate "Deprecated Tables (Transition Period)" section
   - Otherwise, remove completely

3. **Verify current relationships:**
   - `CompanyRoleAssignment` (new unified model)
   - `PersonCompanyAffiliation` (replacement for PersonnelEntityRelationship)
   - `ClientProfile` (new CRM model)
   - `InternalExternalLink` (company-to-company relationships)

**Testing:**
- [ ] Cross-reference `app/models/company.py` for all relationship models
- [ ] Verify junction table counts are accurate
- [ ] Check foreign keys match actual implementations

---

### ACTION 3: Update 04_DATA_DICTIONARY.md
**Priority:** HIGH
**Time:** 60-90 minutes
**File:** `docs/04_DATA_DICTIONARY.md`

**Current State:** Missing encryption field documentation

**Changes Required:**

1. **Add Project encryption fields:**
   ```markdown
   ### Project Model - Encrypted Fields (New in October 2025)

   | Field | Type | Encryption | Access | Description |
   |-------|------|-----------|--------|-------------|
   | capex_encrypted | BLOB | 'confidential' key | `has_confidential_access=True` | Capital expenditure (encrypted) |
   | opex_encrypted | BLOB | 'confidential' key | `has_confidential_access=True` | Operating expenditure (encrypted) |
   | fuel_cost_encrypted | BLOB | 'confidential' key | `has_confidential_access=True` | Fuel costs (encrypted) |
   | lcoe_encrypted | BLOB | 'confidential' key | `has_confidential_access=True` | Levelized cost of energy (encrypted) |
   ```

2. **Update Project model field list:**
   - Note which fields are encrypted vs. plaintext
   - Add encryption key requirements to permission rules

3. **Add encryption validation rules:**
   - Encrypted fields cannot be NULL (if required)
   - Encrypted fields are BLOB type, not original type
   - Decryption fails if user lacks appropriate access level

4. **Document upcoming encryptions (pending):**
   - ClientProfile fields (ned_team encryption)
   - RoundtableHistory fields (ned_team encryption)
   - CompanyRoleAssignment notes (confidential encryption)
   - InternalExternalLink fields (ned_team encryption)
   - Mark as "PLANNED: Phase 3b-3e"

**Testing:**
- [ ] Verify all encrypted fields listed in FIELDS_FOR_ENCRYPTION.md are documented
- [ ] Cross-reference `app/models/project.py` for actual encrypted column names
- [ ] Verify access requirements match `app/models/confidential.py` logic

---

### ACTION 4: Update 05_PERMISSION_SYSTEM.md
**Priority:** MEDIUM
**Time:** 30-45 minutes
**File:** `docs/05_PERMISSION_SYSTEM.md`

**Current State:** Good coverage but needs encryption clarification

**Changes Required:**

1. **Add encryption access control section:**
   ```markdown
   ### Encryption and Field-Level Access

   Encrypted fields add an additional layer of access control:

   - **Confidential Encryption:** User must have `has_confidential_access=True` to view decrypted values
   - **NED Team Encryption:** User must have `is_ned_team=True` to view decrypted values
   - **Default Display:** Non-authorized users see placeholder text (e.g., "[Confidential]", "[NED Team Only]")

   Example: Project.capex is encrypted with 'confidential' key
   - Sally (has_confidential_access=True): Sees actual capex value
   - Joe (standard user): Sees "[Confidential]"
   ```

2. **Link to encryption implementation:**
   - Reference `docs/ENCRYPTION_IMPLEMENTATION_PLAN.md` (see ACTION 8)
   - Cross-reference `app/models/confidential.py` for implementation details

3. **Update permission rules table:**
   - Add row for "Encrypted Field Access"
   - Specify encryption key vs. user flag mapping

**Testing:**
- [ ] Verify permission checks in `app/models/confidential.py` match documentation
- [ ] Test with different user permission levels
- [ ] Verify placeholder text matches documentation

---

## SECTION 2: CREATE NEW DOCUMENTATION (Missing Features)

### ACTION 5: Create docs/ENCRYPTION_IMPLEMENTATION_STATUS.md (NEW)
**Priority:** HIGH
**Time:** 30-40 minutes
**File:** `docs/ENCRYPTION_IMPLEMENTATION_STATUS.md` (NEW)

**Purpose:** Show which encryption is implemented vs. planned

**Content:**

```markdown
# Encryption Implementation Status

## Overview
Per-field encryption for sensitive data is being implemented in phases to protect
confidential financial data and NED Team internal notes.

## Implementation Timeline

### Phase 3a: Project Financial Fields (✅ COMPLETE - October 2025)

**Status:** LIVE IN PRODUCTION

**Encrypted Fields:**
- `capex` (Capital expenditure)
- `opex` (Operating expenditure)
- `fuel_cost` (Fuel costs)
- `lcoe` (Levelized cost of energy)

**Encryption Key:** 'confidential'
**Access Required:** `has_confidential_access=True`
**Display for Non-Authorized Users:** `[Confidential]`

**Database Changes:**
- Added columns: capex_encrypted, opex_encrypted, fuel_cost_encrypted, lcoe_encrypted (BLOB type)
- Migration: `009_add_project_encryption.sql`
- Old plaintext columns retained for safety (not yet removed)

**Testing:**
- Encrypted values stored and decrypted correctly
- Access control working (authorized users see values, others see placeholder)
- Forms save encrypted data
- Reports handle encrypted fields

---

### Phase 3b-3e: Other Models (⏳ PENDING)

**ClientProfile** (Planned):
- relationship_strength, relationship_notes, client_priority, client_status (ned_team encryption)
- Status: Implementation script ready, awaiting execution

**RoundtableHistory** (Planned):
- discussion, action_items, next_steps, client_near_term_focus, mpr_work_targets (ned_team encryption)
- Status: Implementation script ready, awaiting execution

**CompanyRoleAssignment** (Planned):
- notes (conditional confidential encryption based on is_confidential flag)
- Status: Waiting for other phases to complete

**InternalExternalLink** (Planned):
- relationship_strength, notes (ned_team encryption)
- Status: Lower priority, may combine with other company model updates

---

## See Also
- `docs/FIELDS_FOR_ENCRYPTION.md` - Detailed field analysis and rationale
- `docs/04_DATA_DICTIONARY.md` - Field definitions and encryption details
- `app/models/confidential.py` - Encryption implementation code
- `app/models/project.py` - Project model with encryption
```

**Testing:**
- [ ] Verify phases match FIELDS_FOR_ENCRYPTION.md
- [ ] Cross-reference against actual migrations in `migrations/` directory
- [ ] Verify database column existence

---

### ACTION 6: Create docs/DATABASE_SELECTION_FEATURE.md (NEW)
**Priority:** MEDIUM
**Time:** 30-40 minutes
**File:** `docs/DATABASE_SELECTION_FEATURE.md` (NEW)

**Purpose:** Document the new database selection feature

**Content:** (To be created based on actual `app/routes/db_select.py` implementation)

Should include:
- Feature overview and use cases
- User interface flow
- Database schema changes (if any)
- Access control (who can select databases)
- API endpoints
- Connection validation procedures
- Error handling

**Actions:**
1. Read `app/routes/db_select.py` to understand implementation
2. Check for related templates in `app/templates/`
3. Determine if there are database schema changes
4. Document user workflow and technical details

**Testing:**
- [ ] Feature description matches actual implementation
- [ ] All routes/endpoints documented
- [ ] UI flow accurate

---

### ACTION 7: Create docs/ENCRYPTION_IMPLEMENTATION_PLAN.md (Rename FIELDS_FOR_ENCRYPTION.md)
**Priority:** MEDIUM
**Time:** 15-20 minutes
**File:** Move/rename `docs/FIELDS_FOR_ENCRYPTION.md`

**Rationale:** Current filename is confusing (sounds like a checklist of which fields need it, not a plan)

**Action:**
1. Rename: `docs/FIELDS_FOR_ENCRYPTION.md` → `docs/ENCRYPTION_IMPLEMENTATION_PLAN.md`
2. Add header clarification:
   ```markdown
   # Encryption Implementation Plan

   **Status:** This document is a PLANNING guide for implementing per-field encryption.

   **Current Status:** Phase 3a (Project model) is COMPLETE.
   See `docs/ENCRYPTION_IMPLEMENTATION_STATUS.md` for current implementation status.
   ```

**Testing:**
- [ ] File renamed successfully
- [ ] Links in other docs updated to reference new filename
- [ ] Cross-references from 02_DATABASE_SCHEMA.md, 04_DATA_DICTIONARY.md work

---

## SECTION 3: CONSOLIDATE AND DEDUPLICATE DOCUMENTS

### ACTION 8: Consolidate Company Unification Docs
**Priority:** MEDIUM
**Time:** 45-60 minutes
**Files to Consolidate:**
- `docs/company_refactor_status.md` (current status)
- `docs/company_unification_plan.md` (plan)
- `docs/MIGRATION_PLAN.md` (detailed procedures)

**Result:** `docs/COMPANY_UNIFICATION.md`

**Structure:**
```markdown
# Company Unification

## Overview & Objectives
[From company_refactor_status.md - Background & Goals]

## Completed Work
[From company_refactor_status.md - Completed Work]

## Outstanding Work
[From company_refactor_status.md - Outstanding Work]

## Migration Plan for Production
[From docs/MIGRATION_PLAN.md - Detailed procedures]

## See Also
- `docs/ENCRYPTION_IMPLEMENTATION_STATUS.md` - Field encryption status
- `docs/02_DATABASE_SCHEMA.md` - Unified schema documentation
- `docs/03_DATABASE_RELATIONSHIPS.md` - Relationship definitions
```

**Actions:**
1. Create new consolidated file
2. Update cross-references in 02_DATABASE_SCHEMA.md, 03_DATABASE_RELATIONSHIPS.md
3. Delete old individual files (or mark as deprecated with redirect)

**Testing:**
- [ ] All information from 3 source files preserved
- [ ] Cross-references work
- [ ] Structure is logical and readable

---

### ACTION 9: Consolidate Database Selection Docs
**Priority:** LOW (if these exist)
**Time:** 15-20 minutes
**Files to Consolidate:**
- `docs/DB_SELECTION_SPEC.md` (if exists)
- `docs/DB_SELECTION_IMPLEMENTATION.md` (if exists)
- New file from ACTION 6

**Result:** Single `docs/DATABASE_SELECTION.md`

**Testing:**
- [ ] All information preserved
- [ ] No duplication
- [ ] References updated

---

## SECTION 4: VERIFICATION & TESTING

### ACTION 10: Verify API Endpoints Documentation
**Priority:** HIGH
**Time:** 45-60 minutes
**File:** `docs/16_API_ENDPOINTS.md`

**Current State:** File appears incomplete/truncated in earlier reads

**Actions:**
1. Read full file to understand current state
2. Compare against actual routes in `app/routes/`:
   - Check all routes are documented
   - Verify parameters match
   - Verify response formats are accurate
3. Add any missing endpoints:
   - Database selection routes (new)
   - Company unification routes (new)
   - Encryption-related changes
4. Add recent changes log at top

**Testing:**
- [ ] Run actual API endpoints and verify against documentation
- [ ] All routes in `app/routes/` have matching documentation
- [ ] Response examples are current

---

### ACTION 11: Cross-Reference Check All Specs
**Priority:** MEDIUM
**Time:** 60 minutes
**Process:** Verify key specs don't contradict each other

**Specs to Cross-Check:**
- 02_DATABASE_SCHEMA.md ↔ 03_DATABASE_RELATIONSHIPS.md (table/relationship consistency)
- 04_DATA_DICTIONARY.md ↔ 02_DATABASE_SCHEMA.md (field definitions match)
- 05_PERMISSION_SYSTEM.md ↔ 04_DATA_DICTIONARY.md (permission requirements match)
- 08_UI_VIEWS_CORE.md ↔ 16_API_ENDPOINTS.md (routes/views match)
- 09_UI_VIEWS_CRM.md ↔ 16_API_ENDPOINTS.md (CRM routes exist)

**Actions:**
1. Create cross-reference verification checklist
2. Walk through each spec pair
3. Document any inconsistencies found
4. Create follow-up issues if needed

**Testing:**
- [ ] No contradictions between specs
- [ ] All cross-references are consistent

---

## SECTION 5: CLEANUP & ORGANIZATION

### ACTION 12: Update Master Specification Navigation
**Priority:** MEDIUM
**Time:** 20-30 minutes
**File:** `docs/00_MASTER_SPECIFICATION.md`

**Changes Required:**
1. Update spec listing to reflect new/consolidated files:
   - Remove references to deleted files
   - Add new files (ENCRYPTION_IMPLEMENTATION_STATUS, DATABASE_SELECTION_FEATURE)
   - Update consolidated file references

2. Add status indicators:
   ```markdown
   | Doc # | File | Status | Last Updated |
   |-------|------|--------|--------------|
   | 01 | ARCHITECTURE | ✅ Current | Oct 2025 |
   | 02 | DATABASE_SCHEMA | ⚠️ Refreshed - Migration in Progress | [Date] |
   | ... | ... | ... | ... |
   | NEW | ENCRYPTION_IMPLEMENTATION_STATUS | ✅ New | [Date] |
   | NEW | DATABASE_SELECTION_FEATURE | ✅ New | [Date] |
   ```

3. Update "Quick Start" section if needed

**Testing:**
- [ ] All links work
- [ ] Navigation is clear
- [ ] Status indicators are accurate

---

### ACTION 13: Update README.md
**Priority:** MEDIUM
**Time:** 30-40 minutes
**File:** `README.md` (root)

**Current State:** Likely stale

**Changes Required:**
1. Update feature list to reflect latest work:
   - Company unification (in progress)
   - Per-field encryption (partially complete)
   - Database selection (new)

2. Update "Current Status" section:
   - Phase progress
   - What's in development
   - What's ready for production

3. Update setup instructions if needed

4. Update documentation links to point to updated/new docs

**Testing:**
- [ ] All links work
- [ ] Feature descriptions are current
- [ ] Setup instructions are accurate

---

## EXECUTION ROADMAP

### Phase 1: Critical Updates (URGENT - Do First)
**Time: 2.5-3.5 hours**

1. ACTION 1: Update 02_DATABASE_SCHEMA.md
2. ACTION 2: Update 03_DATABASE_RELATIONSHIPS.md
3. ACTION 3: Update 04_DATA_DICTIONARY.md
4. ACTION 5: Create ENCRYPTION_IMPLEMENTATION_STATUS.md

**Rationale:** These changes clarify the biggest source of confusion (migration status + encryption)

### Phase 2: Documentation Structure (HIGH PRIORITY - Do Second)
**Time: 1.5-2 hours**

5. ACTION 4: Update 05_PERMISSION_SYSTEM.md
6. ACTION 7: Rename/clarify FIELDS_FOR_ENCRYPTION.md
7. ACTION 12: Update 00_MASTER_SPECIFICATION.md

**Rationale:** Improves navigation and reduces confusion about which docs are plans vs. status

### Phase 3: New Features & Consolidation (MEDIUM PRIORITY - Do Third)
**Time: 1.5-2 hours**

8. ACTION 6: Create DATABASE_SELECTION_FEATURE.md
9. ACTION 8: Consolidate Company Unification docs
10. ACTION 13: Update README.md

**Rationale:** Captures new feature documentation and cleans up duplication

### Phase 4: Verification (FINAL - Do Last)
**Time: 1.5-2 hours**

11. ACTION 10: Verify API Endpoints
12. ACTION 11: Cross-reference check
13. ACTION 9: Consolidate Database Selection docs (if exists)

**Rationale:** Final pass to ensure consistency and completeness

---

## TOTAL TIME ESTIMATE

| Phase | Time | Status |
|-------|------|--------|
| Phase 1: Critical Updates | 2.5-3.5h | 🔴 NOT STARTED |
| Phase 2: Documentation Structure | 1.5-2h | 🔴 NOT STARTED |
| Phase 3: New Features & Consolidation | 1.5-2h | 🔴 NOT STARTED |
| Phase 4: Verification | 1.5-2h | 🔴 NOT STARTED |
| **TOTAL** | **7-9 hours** | 🔴 NOT STARTED |

**Recommendation:** Spread across 2-3 sessions to avoid fatigue and allow for testing between phases.

---

## SUCCESS CRITERIA

Upon completion:
- [ ] No phase completion marker files remain
- [ ] All consolidated files are merged
- [ ] All specs reflect current implementation status (not future plans)
- [ ] Encryption status clearly shows what's implemented vs. pending
- [ ] Company unification migration status is explicit
- [ ] Database selection feature is documented
- [ ] No contradictions between specs
- [ ] Master specification is accurate and up-to-date
- [ ] README is current and informative
- [ ] All cross-references and links work
- [ ] AI agents reading these docs understand current state accurately

