# Company Unification Migration Plan

## Overview
This document outlines the step-by-step process for migrating from legacy role-specific company tables to the unified company schema in production environments.

## Migration Components

### 1. Backfill Scripts
Three backfill scripts populate the unified schema from legacy data:

- **`scripts/backfill_companies.py`** - Migrates base company records from legacy tables
- **`scripts/backfill_personnel_affiliations.py`** - Migrates personnel-entity relationships
- **`scripts/backfill_project_relationships.py`** - Migrates project-company relationships

**Master Script:**
- **`scripts/backfill_all.py`** - Runs all three backfills in correct order with progress reporting

### 2. Validation Script
- **`scripts/validate_company_migration.py`** - Validates migration integrity
  - Checks all legacy entities have company records
  - Detects duplicate company names
  - Verifies project relationship coverage
  - Validates personnel affiliation migration

## Pre-Migration Checklist

### Development Environment
- [ ] Run full test suite: `pytest -xvs`
- [ ] Run validation script: `python scripts/validate_company_migration.py`
- [ ] Review any duplicates flagged by validation
- [ ] Test backfill in dry-run mode: `python scripts/backfill_all.py --dry-run`
- [ ] Run actual backfill: `python scripts/backfill_all.py`
- [ ] Re-run validation to confirm success
- [ ] Manually verify samples via `/companies` view
- [ ] Test key workflows (create vendor, link to project, etc.)

### Staging Environment
- [ ] Deploy updated code to staging
- [ ] Run database migrations (if any schema changes)
- [ ] Run validation script to check current state
- [ ] Create database backup before backfill
- [ ] Run backfill: `python scripts/backfill_all.py --config staging`
- [ ] Run validation script to verify
- [ ] Sample spot-checks (10-20 companies across different roles)
- [ ] Test critical user workflows
- [ ] Performance testing on dashboard and reports
- [ ] Leave staging running for 24-48 hours, monitor for issues

## Production Migration Steps

### Phase 1: Preparation (T-1 week)
1. **Code Deployment**
   - Deploy application code with dual-write capability
   - All new CRUD operations sync to both legacy and unified schemas
   - All queries still use legacy tables (no breaking changes)

2. **Validation**
   - Run validation script on production (read-only check)
   - Document baseline stats

3. **Communication**
   - Notify team of upcoming migration window
   - Prepare rollback plan

### Phase 2: Migration Window (T-0)
**Recommended:** Off-hours or maintenance window

1. **Pre-Migration**
   ```bash
   # Create backup
   pg_dump nukeworks_prod > nukeworks_backup_$(date +%Y%m%d_%H%M%S).sql

   # Run validation (pre-migration state)
   python scripts/validate_company_migration.py --config production > pre_migration_report.txt
   ```

2. **Execute Backfill**
   ```bash
   # Run master backfill script
   python scripts/backfill_all.py --config production
   ```

   Expected duration: 5-15 minutes depending on data volume

3. **Post-Migration Validation**
   ```bash
   # Run validation again
   python scripts/validate_company_migration.py --config production > post_migration_report.txt

   # Compare reports
   diff pre_migration_report.txt post_migration_report.txt
   ```

4. **Smoke Tests**
   - Access `/companies` view - verify company list loads
   - Check dashboard - verify counts are reasonable
   - View network diagram - verify nodes/edges render
   - Create test vendor - verify appears in unified schema
   - Link test vendor to project - verify relationship syncs

5. **Issue Resolution**
   - Address any duplicates flagged by validation
   - Verify suspicious data points
   - Check logs for errors

### Phase 3: Monitoring (T+1 to T+7 days)
1. **Daily Checks**
   - Monitor application logs for errors
   - Check for data inconsistencies
   - Verify new records sync correctly

2. **User Feedback**
   - Collect user reports of issues
   - Validate any concerns about missing/duplicate data

3. **Performance Monitoring**
   - Dashboard load times
   - Report generation times
   - Query performance on unified schema

## Rollback Plan

### If Issues Discovered During Migration
1. **Stop** - Do not commit database transaction if using explicit transaction
2. **Rollback** - Revert database to backup
3. **Investigate** - Review logs and validation output
4. **Fix** - Correct issues in development/staging
5. **Retry** - Schedule new migration window

### If Issues Discovered Post-Migration
**Note:** Rollback is complex after migration since dual-write is in place

**Option 1: Data Correction**
- Fix issues in unified schema tables directly
- Re-run validation
- Monitor

**Option 2: Full Rollback** (extreme cases only)
- Restore from backup
- Revert application code to pre-migration version
- Plan corrective actions

## Post-Migration Cleanup (Optional - Future)

### After Unified Schema Proven Stable (3-6 months)
1. **Migrate Remaining Views**
   - Update network table view to query unified schema
   - Update any remaining legacy queries

2. **Deprecate Legacy Tables**
   - Add warnings to legacy CRUD interfaces
   - Redirect users to unified views

3. **Final Cutover**
   - Remove dual-write code
   - Drop legacy tables (AFTER confirmed no dependencies)
   - Remove old models and routes

## Success Criteria

Migration is considered successful when:
- ✓ Validation script passes with no critical issues
- ✓ All entity counts match (legacy vs unified)
- ✓ Project relationship coverage ≥ 95%
- ✓ Personnel affiliation coverage ≥ 95%
- ✓ No user-reported data loss
- ✓ Dashboard and reports load without errors
- ✓ New CRUD operations sync to unified schema
- ✓ No performance degradation

## Contact & Support

**Migration Lead:** [Your Name]
**Database Admin:** [DBA Name]
**Escalation:** [Manager Name]

## Appendix: Common Issues

### Duplicate Company Names
**Symptom:** Validation reports multiple companies with same name
**Resolution:** Review context - may be legitimate (e.g., subsidiary vs parent)
**Action:** Use `CompanyRoleAssignment.context_type` to distinguish

### Missing Relationships
**Symptom:** Project relationships not syncing
**Cause:** Company record missing for legacy entity
**Resolution:** Re-run company backfill for that entity type

### Performance Issues
**Symptom:** Dashboard slow after migration
**Cause:** Missing indexes on unified schema
**Resolution:** Add indexes to `company_role_assignments` table

### Orphaned Records
**Symptom:** PersonCompanyAffiliation without matching company
**Cause:** Legacy entity deleted but relationship remains
**Resolution:** Clean up orphaned PersonnelEntityRelationship records first
