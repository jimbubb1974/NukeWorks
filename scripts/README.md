# Company Unification Migration Scripts

This directory contains scripts for migrating from legacy role-specific company tables to the unified company schema.

## Quick Start

### 1. Run Validation (Check Current State)
```bash
python scripts/validate_company_migration.py
```

### 2. Test Backfill (Dry Run)
```bash
python scripts/backfill_all.py --dry-run
```

### 3. Run Full Backfill
```bash
python scripts/backfill_all.py
```

### 4. Validate Results
```bash
python scripts/validate_company_migration.py
```

### 5. Check for Duplicates (Optional)
```bash
python scripts/resolve_duplicate_companies.py
```

## Scripts Overview

### Migration Scripts

#### `backfill_all.py` (Master Script)
Runs complete backfill process in correct order.

**Usage:**
```bash
# Development (default)
python scripts/backfill_all.py

# Dry run (no changes saved)
python scripts/backfill_all.py --dry-run

# Staging environment
python scripts/backfill_all.py --config staging

# Production
python scripts/backfill_all.py --config production
```

**What it does:**
1. Backfills base company records from legacy tables
2. Migrates personnel-entity relationships to PersonCompanyAffiliation
3. Migrates project relationships to CompanyRoleAssignment
4. Provides detailed progress reporting

**Expected duration:** 5-15 minutes depending on data volume

#### `backfill_companies.py`
Backfills only base company records (vendors, owners, clients, operators, constructors, offtakers).

**Usage:**
```bash
python scripts/backfill_companies.py [--config ENV]
```

#### `backfill_personnel_affiliations.py`
Backfills only personnel-company affiliations.

**Usage:**
```bash
python scripts/backfill_personnel_affiliations.py [--config ENV]
```

#### `backfill_project_relationships.py`
Backfills only project-company relationships.

**Usage:**
```bash
python scripts/backfill_project_relationships.py [--config ENV]
```

### Validation & Analysis Scripts

#### `validate_company_migration.py`
Comprehensive validation of migration integrity.

**Usage:**
```bash
python scripts/validate_company_migration.py [--config ENV]
```

**Checks:**
- ✓ All legacy entities have corresponding company records
- ✓ No missing company assignments
- ✓ Project relationship coverage
- ✓ Personnel affiliation coverage
- ⚠️ Duplicate company names

**Example output:**
```
Company Coverage Check
Vendors:      13 total, 0 missing
Owners:       24 total, 0 missing
...

Duplicate Company Name Check
✓ No duplicate company names found

Project Relationship Coverage Check
Vendor: 45/45 (100.0%)
Owner: 32/32 (100.0%)
...
```

#### `resolve_duplicate_companies.py`
Identifies and resolves duplicate company records.

**Usage:**
```bash
# Report only (safe)
python scripts/resolve_duplicate_companies.py

# Interactive resolution (modifies database)
python scripts/resolve_duplicate_companies.py --interactive
```

**Interactive mode:**
- Shows detailed analysis of each duplicate set
- Suggests merge strategy based on usage
- Allows manual resolution decisions
- Safely merges duplicate records

**Example:**
```
Duplicate Name: "ACME Corporation"
Instances: 2

[1] Company ID: 42
    Role Assignments: 15
    Affiliations: 3
    Created: 2024-01-15

[2] Company ID: 87
    Role Assignments: 2
    Affiliations: 0
    Created: 2024-03-20

SUGGESTED ACTION:
  Keep ID 42 (score: 175) - has most relationships

Action? [(s)kip, (m)erge as suggested, (c)ustom, (q)uit]:
```

### Other Scripts

#### `companies_report.py`
Generates summary report of company counts by role.

**Usage:**
```bash
python scripts/companies_report.py [--config ENV]
```

## Migration Workflow

### Development Environment
1. Run validation to establish baseline
2. Run dry-run backfill to preview changes
3. Run actual backfill
4. Validate results
5. Check for duplicates and resolve if needed
6. Test application functionality

### Staging Environment
1. Deploy code
2. Create database backup
3. Run validation (pre-migration)
4. Run backfill
5. Run validation (post-migration)
6. Spot-check samples
7. Test critical workflows
8. Monitor for 24-48 hours

### Production Environment
**See `docs/MIGRATION_PLAN.md` for detailed production migration steps.**

Quick checklist:
- [ ] Create backup
- [ ] Run pre-migration validation
- [ ] Execute backfill
- [ ] Run post-migration validation
- [ ] Perform smoke tests
- [ ] Monitor for issues

## Troubleshooting

### "Missing X company companies"
**Cause:** Company backfill incomplete or failed
**Fix:** Re-run `backfill_companies.py`

### "Project relationships not synced"
**Cause:** Company records missing for legacy entities
**Fix:** Ensure company backfill completed first, then re-run project backfill

### "Duplicate company names found"
**Cause:** Same company name in multiple legacy tables
**Options:**
1. Legitimate duplicates (e.g., subsidiary vs parent) - can keep separate
2. True duplicates - use `resolve_duplicate_companies.py --interactive` to merge

### Performance issues
**Cause:** Missing indexes (rare)
**Fix:** Check `company_role_assignments` table has proper indexes on:
- `company_id`
- `role_id`
- `context_type, context_id`

## Configuration

Scripts use Flask configuration from environment variable:
```bash
# Development (default)
export FLASK_ENV=development

# Staging
export FLASK_ENV=staging

# Production
export FLASK_ENV=production
```

Or pass `--config` parameter to individual scripts.

## Safety Features

All scripts:
- ✓ Support `--dry-run` mode (where applicable)
- ✓ Idempotent (safe to run multiple times)
- ✓ Preserve existing data (additive, not destructive)
- ✓ Detailed logging and progress reporting
- ✓ Transaction-based (rollback on error)

## Getting Help

For detailed migration planning, see: `docs/MIGRATION_PLAN.md`

For refactor status and progress, see: `docs/company_refactor_status.md`

For questions or issues, contact the migration lead.
