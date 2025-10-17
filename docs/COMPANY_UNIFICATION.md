# Company Unification - Schema Migration & Implementation

**Status:** WORK IN PROGRESS - Schema implemented, production migration pending
**Last Updated:** October 2025
**Related Documents:**
- `02_DATABASE_SCHEMA.md` - Unified company schema
- `03_DATABASE_RELATIONSHIPS.md` - Relationship implementations
- `company_refactor_status.md` - Original status document (archived reference)

---

## Executive Summary

This document describes the complete company unification initiative: the strategic shift from role-specific company tables (technology_vendors, owners_developers, operators, etc.) to a unified **companies** table with flexible role-based relationships. This enables organizations to have multiple roles, simplifies data consistency, and improves reporting and CRM functionality.

**Current Status (October 2025):**
- ✅ Unified schema created and tested in dev/staging
- ✅ CRUD operations sync to new schema
- ⏳ Production migration awaiting approval
- ⏳ Legacy table cleanup deferred 3-6 months post-production

---

## Goals & Rationale

### The Problem
Legacy structure used role-specific tables:
- `technology_vendors` - Technology vendors only
- `owners_developers` - Utilities/project developers only
- `operators` - Facility operators only
- `constructors` - Construction companies only
- `offtakers` - Energy off-takers only
- `clients` - CRM clients only

**Issues:**
- Organizations playing multiple roles required duplicate records
- Example: Holtec is both a technology vendor AND an operator
- Difficult to maintain consistent CRM/analytics views
- Data duplication and inconsistency

### The Solution
Unified **companies** table with:
- Single source of truth for all organizations
- Flexible role assignments via `company_role_assignments` table
- Support for multi-role companies
- Rich CRM profiles via `client_profiles` extension
- Normalized personnel relationships via `person_company_affiliations`

### Expected Benefits
- Single record per organization regardless of roles
- Supports multi-role representation (Holtec as vendor AND operator)
- Simplified CRM and reporting
- Better data consistency
- Improved performance through normalized schema

---

## High-Level Architecture

### New Unified Schema

```
Company (company_id, name, type, website, country, ...)
  ├─ CompanyRole (role_id, code='vendor', label='Technology Vendor')
  ├─ CompanyRoleAssignment (assignment_id, company_id, role_id, context_type, context_id)
  │   └─ Contexts: General (NULL) or Project-scoped ('Project', project_id)
  ├─ ClientProfile (company_id PK/FK, relationship_strength, client_priority, ...)
  └─ PersonCompanyAffiliation (affiliation_id, person_id, company_id, title, is_primary)

CompanyRole (reference table)
  ├─ 'vendor' - Technology vendor
  ├─ 'developer' - Owner/developer
  ├─ 'operator' - Facility operator
  ├─ 'constructor' - Constructor
  ├─ 'offtaker' - Energy off-taker
  └─ 'client' - MPR client

InternalExternalLink (for company-to-company relationships)
```

### Multi-Role Example

**Organization:** Holtec
- Record: companies.company_id = 50
- Roles:
  - CompanyRoleAssignment: (50, role_id='vendor', context_type=NULL) - Vendor globally
  - CompanyRoleAssignment: (50, role_id='operator', context_type=NULL) - Operator globally
  - CompanyRoleAssignment: (50, role_id='vendor', context_type='Project', context_id=10) - Vendor for Project 10
  - ClientProfile: relationship_strength='Strong', client_priority='High' - MPR client

---

## Implementation Status

### ✅ COMPLETED: Phase 1 - Schema & Models

**Schema Creation (October 2025)**
- Created 6 new ORM models:
  - `Company` - Unified company table
  - `CompanyRole` - Role catalog
  - `CompanyRoleAssignment` - Role assignments
  - `ClientProfile` - CRM extension
  - `PersonCompanyAffiliation` - Personnel links
  - `InternalExternalLink` - Company-to-company relationships

**Migration & Sync Services**
- `app/services/company_sync.py` - Sync legacy ↔ unified
- `app/services/company_query.py` - Query unified schema
- `app/services/company_analytics.py` - Analytics helpers

**Test Harness**
- 19 passing unit tests
- Fixtures for all new models
- Edge case coverage

### ✅ COMPLETED: Phase 2 - CRUD Integration

**Create/Edit Operations**
- Vendor create/edit routes sync to unified schema
- Owner create/edit routes sync to unified schema
- Client create/edit routes sync to unified schema
- Operator create/edit routes sync to unified schema
- Constructor create/edit routes sync to unified schema
- Off-taker create/edit routes sync to unified schema

**List/Detail Views**
- `/companies` list view with role filtering
- Company detail page shows all roles
- Backward links to legacy pages

**Network Integration**
- Network diagram builds from unified schema
- Nodes and edges derived from CompanyRoleAssignments
- Links to unified company detail pages

**Dashboard**
- Updated to query unified schema
- Company counts by role accurate
- Analytics working correctly

### ✅ COMPLETED: Phase 3 - Backfill & Validation

**Backfill Scripts (Ready)**
- `scripts/backfill_companies.py` - Migrate base companies
- `scripts/backfill_personnel_affiliations.py` - Migrate personnel links
- `scripts/backfill_project_relationships.py` - Migrate project relationships
- `scripts/backfill_all.py` - Master script (runs all three in order)
- `scripts/validate_company_migration.py` - Validation & integrity checks
- `scripts/resolve_duplicate_companies.py` - Interactive duplicate resolution

**Dev Run Results**
- Vendors: 13 → unified
- Owners: 24 → unified
- Clients: 1 → unified
- Operators: 4 → unified
- Constructors: 5 → unified
- Off-takers: 6 → unified
- **Total: 53 companies successfully migrated**

**Migration Documentation**
- `docs/MIGRATION_PLAN.md` - Production migration procedures
- Pre-migration checklist
- Step-by-step migration phases
- Rollback procedures
- Success criteria

---

## Outstanding Work

### ⏳ PENDING: Phase 4 - Production Migration

**Pre-Production (Immediate)**
1. Execute staging environment backfill
2. Run validation script on staging
3. Test all critical workflows
4. Leave staging running 24-48 hours for monitoring

**Production Migration (Scheduled)**
1. **Phase 1: Preparation**
   - Deploy dual-write enabled code
   - Run pre-migration validation
   - Notify team and prepare rollback

2. **Phase 2: Migration Window**
   - Create full database backup
   - Run master backfill script
   - Execute post-migration validation
   - Smoke test critical features

3. **Phase 3: Monitoring (T+1 to T+7 days)**
   - Monitor logs for errors
   - Track dashboard/report performance
   - Collect user feedback
   - Address any data issues

**See docs/MIGRATION_PLAN.md for complete procedures**

### ⏳ DEFERRED: Phase 5 - Legacy Table Cleanup

**Post-Stability Window (3-6 months after production)**
1. Migrate remaining legacy views to unified schema
   - Network table view (`app/routes/network_view.py`)
   - Any custom queries using legacy tables

2. Remove dual-write code
   - No longer write to legacy tables
   - All reads use unified schema

3. Drop legacy tables (only after confirmed no dependencies)
   - technology_vendors
   - owners_developers
   - operators
   - constructors
   - offtakers
   - All legacy relationship tables

4. Clean up legacy models and routes

---

## Key Design Decisions

### 1. Dual Schema During Transition
**Decision:** Keep legacy tables active during transition period
**Rationale:**
- Allows gradual cutover
- Enables easy rollback if needed
- Doesn't disrupt business operations
- Tests sync logic in production before full cutover

**Timeline:** Legacy tables will be dropped 3-6 months post-production migration

### 2. Polymorphic Context for Relationships
**Decision:** Use context_type/'context_id for flexible relationships
**Rationale:**
- Single table handles all company relationships
- Supports project-scoped roles
- Easy to add new context types in future
- Reduces schema complexity

**Example:**
```sql
-- General role (NULL context)
INSERT INTO company_role_assignments
(company_id=1, role_id=1, context_type=NULL, context_id=NULL)
-- "NuScale is a vendor (globally)"

-- Project-specific role
INSERT INTO company_role_assignments
(company_id=1, role_id=1, context_type='Project', context_id=5)
-- "NuScale is the vendor for Project 5"
```

### 3. Idempotent Backfill Scripts
**Decision:** All backfill scripts are safe to run multiple times
**Rationale:**
- Can retry after fixing issues
- Safe to run against running systems
- Detects and handles duplicates
- Validates completeness

**Features:**
- `--dry-run` mode for testing
- Environment support (dev/staging/production)
- Progress reporting
- Rollback-safe (no destructive operations)

### 4. CRM Profiles as Extension Table
**Decision:** Use `client_profiles` as 1:1 extension to companies
**Rationale:**
- Optional CRM data only for clients
- Clean separation of concerns
- Can add more extensions in future
- Supports partial CRM adoption

---

## Migration Procedure Overview

### Pre-Migration Checklist
- [ ] Run full test suite (19 tests pass)
- [ ] Run validation in dry-run mode
- [ ] Create database backup
- [ ] Test key workflows
- [ ] Deploy dual-write code

### Migration Window (Off-Hours Recommended)
1. **Backup** - Create pre-migration snapshot
2. **Validate** - Run validation (record baseline)
3. **Backfill** - Run master backfill script (~5-15 mins)
4. **Validate** - Run validation (compare with baseline)
5. **Smoke Test** - Verify critical features
6. **Resolve Issues** - Address any data problems

### Post-Migration (24-48 Hours)
- Monitor logs for errors
- Track performance metrics
- Collect user feedback
- Verify new records sync correctly

### Success Criteria
✓ Validation passes (all entities migrated)
✓ All entity counts match (legacy vs unified)
✓ Project relationship coverage ≥ 95%
✓ Personnel affiliation coverage ≥ 95%
✓ Dashboard/reports load without errors
✓ No user-reported data loss
✓ New CRUD operations sync to unified schema
✓ Performance acceptable

---

## Data Migration Specifics

### Company Records
**Source:** 5 legacy tables (vendors, owners, clients, operators, constructors, offtakers)
**Target:** Single `companies` table with role assignments
**Process:**
1. Migrate company names, contact info, notes
2. Create CompanyRoleAssignment records for each role
3. Handle duplicates (same company in multiple legacy tables)
4. Backfill is idempotent (can run multiple times safely)

**Example:**
```python
# Legacy: NuScale in technology_vendors table
# Migration creates:
companies (company_id=42, company_name='NuScale Power', ...)
company_role_assignments (company_id=42, role_id=1, context_type=NULL)
  # role_id=1 → 'vendor'
```

### Personnel Relationships
**Source:** `personnel_entity_relationships` polymorphic table
**Target:** `person_company_affiliations` explicit relationships
**Process:**
1. Filter for company-related relationships
2. Create PersonCompanyAffiliation records
3. Preserve title, dates, notes
4. Set is_primary based on legacy primary flag

### Project Relationships
**Source:** Legacy project relationship tables
- project_vendor_relationships
- project_owner_relationships
- project_constructor_relationships
- project_operator_relationships
- project_offtaker_relationships

**Target:** `company_role_assignments` with context_type='Project'
**Process:**
1. Create one CompanyRoleAssignment per relationship
2. Set context_type='Project', context_id=project_id
3. Set is_primary if was primary vendor/owner/etc
4. Preserve notes

---

## Query Patterns (Post-Migration)

### Get All Vendors
```sql
SELECT c.* FROM companies c
JOIN company_role_assignments cra ON c.company_id = cra.company_id
JOIN company_roles cr ON cra.role_id = cr.role_id
WHERE cr.role_code = 'vendor' AND cra.context_type IS NULL
```

### Get Companies for a Project
```sql
SELECT c.*, cr.role_label FROM companies c
JOIN company_role_assignments cra ON c.company_id = cra.company_id
JOIN company_roles cr ON cra.role_id = cr.role_id
WHERE cra.context_type = 'Project' AND cra.context_id = ?
```

### Get Company with All Roles
```sql
SELECT c.company_id, c.company_name,
       GROUP_CONCAT(cr.role_label) as roles
FROM companies c
LEFT JOIN company_role_assignments cra ON c.company_id = cra.company_id
LEFT JOIN company_roles cr ON cra.role_id = cr.role_id
WHERE cra.context_type IS NULL
GROUP BY c.company_id
```

---

## Risk Mitigation

### Data Loss Prevention
- All backfill scripts are non-destructive
- Legacy data remains intact during transition
- Validation detects missing/orphaned records
- Rollback available via database backup

### Performance Impact
- Unified schema indexed appropriately
- Queries tested for performance
- Dashboard response times verified
- No expected performance degradation

### Business Continuity
- Dual-write allows gradual cutover
- Legacy queries still work during transition
- Easy rollback if issues discovered
- Comprehensive monitoring plan

### Testing Coverage
- 19 unit tests for new models
- Integration tests for backfill
- User workflow testing
- Edge case handling (duplicates, orphaned records)

---

## Timeline Estimate

### Current (October 2025)
- Schema complete ✅
- Development testing complete ✅
- Backfill scripts tested ✅

### Near-term (Next 1-2 weeks)
1. Run staging migration
2. Validate and monitor staging (24-48 hours)
3. User acceptance testing
4. Schedule production migration

### Production (After stakeholder approval)
1. Execute production migration in off-hours
2. Post-migration monitoring (1 week)
3. Begin phase-out of legacy code (if no issues)
4. Full legacy cleanup (3-6 months post-migration)

---

## See Also

- `docs/02_DATABASE_SCHEMA.md` - Unified schema technical details
- `docs/03_DATABASE_RELATIONSHIPS.md` - Relationship table definitions
- `docs/MIGRATION_PLAN.md` - Production migration procedures
- `scripts/README.md` - Backfill script documentation
- `app/services/company_sync.py` - Sync implementation
- `app/services/company_query.py` - Query helpers
- `app/services/company_analytics.py` - Analytics functions

---

**Status:** WORK IN PROGRESS - Ready for production migration
**Next Action:** Schedule and execute production migration per docs/MIGRATION_PLAN.md

---

**Document End**
