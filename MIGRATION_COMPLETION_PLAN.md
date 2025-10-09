# Migration Completion Plan: Legacy to Unified Schema

**Created:** October 7, 2025
**Status:** Ready for execution
**Goal:** Complete the migration from legacy company-specific tables to the unified company schema

---

## Executive Summary

**Current State:** You're ~70% through the migration
- ✅ New unified schema exists (migration 005)
- ✅ Data has been backfilled to new schema
- ✅ Some features use new schema (dashboard, navigation, network diagrams)
- ⚠️ Legacy routes/models still active - users can still use old URLs
- ⚠️ Some code writes to BOTH schemas (sync functions)

**End State:** 100% on unified schema
- ✅ All code uses only new schema
- ✅ Legacy routes removed/redirected
- ✅ Legacy models marked deprecated
- ✅ Dual-write sync code removed
- 🎯 Legacy tables can be dropped (after validation period)

**Timeline:** Estimated 3-5 work sessions (6-10 hours total)

---

## Phase 1: Preparation & Validation

### Step 1.1: Validate Current Data Migration
**Goal:** Ensure all legacy data is in new schema

```bash
cd "C:\Users\jimbu\Coding Projects\NukeWorks"
python scripts/validate_company_migration.py
```

**Expected Output:**
- Company counts match between old and new schemas
- All project relationships exist in company_role_assignments
- All personnel affiliations exist in person_company_affiliations

**If validation fails:**
```bash
# Run backfill scripts
python scripts/backfill_all.py
```

**Checkpoint:** ✅ All data exists in new schema

---

### Step 1.2: Create Backup
**Goal:** Safety net before making code changes

```bash
# Create snapshot via Flask CLI
python -m flask check-migrations
python -m flask apply-migrations  # Ensure DB is up to date
```

Then via admin interface:
1. Log in as admin
2. Navigate to Admin → Snapshots
3. Create manual snapshot: "Pre-migration-completion backup"
4. Mark as retained

**Checkpoint:** ✅ Backup created and retained

---

### Step 1.3: Document Current Routes
**Goal:** Know what URLs will change

**Legacy URLs that will be affected:**
- `/vendors` → Redirect to `/companies?role=vendor`
- `/vendors/<id>` → Redirect to `/companies/<unified_id>`
- `/owners` → Redirect to `/companies?role=developer`
- `/owners/<id>` → Redirect to `/companies/<unified_id>`
- `/operators` → Redirect to `/companies?role=operator`
- `/operators/<id>` → Redirect to `/companies/<unified_id>`
- `/constructors` → Redirect to `/companies?role=constructor`
- `/constructors/<id>` → Redirect to `/companies/<unified_id>`
- `/offtakers` → Redirect to `/companies?role=offtaker`
- `/offtakers/<id>` → Redirect to `/companies/<unified_id>`

**Checkpoint:** ✅ User communication plan ready (if needed)

---

## Phase 2: Code Migration (Critical Path)

### Step 2.1: Update Projects Module
**File:** `app/routes/projects.py`

**Current:** Project relationships still create legacy junction table records
**Goal:** Use ONLY company_role_assignments

**Changes needed:**
1. **Project detail view** - Query company_role_assignments instead of project_vendor_relationships, etc.
2. **Add relationship forms** - Create only company_role_assignments (remove sync calls)
3. **Remove relationship functions** - Remove code that creates legacy relationship records

**Test:**
```python
# After changes, test:
# 1. View project detail page
# 2. Add vendor to project
# 3. Add constructor to project
# 4. Verify only company_role_assignments created (not legacy tables)
```

**Files to modify:**
- `app/routes/projects.py` (~400 lines)
- `app/templates/projects/view.html` (display relationships)
- `app/templates/projects/edit.html` (edit forms)

**Estimated time:** 2 hours

**Checkpoint:** ✅ Projects use unified schema only

---

### Step 2.2: Update Admin Permission Scrubbing
**File:** `app/routes/admin.py`

**Current:** `RELATIONSHIP_CONFIG` dict references legacy relationship models
**Goal:** Update to use company_role_assignments

**Changes needed:**
1. **Line 69-102:** Update `RELATIONSHIP_CONFIG` to reference CompanyRoleAssignment
2. **Line 147:** Update `_resolve_field_display()` to query companies instead of owners_developers
3. **Permission scrubbing UI:** Update templates to show unified schema

**Files to modify:**
- `app/routes/admin.py` (lines 69-150)
- `app/templates/admin/permissions.html`

**Estimated time:** 1 hour

**Checkpoint:** ✅ Admin permission scrubbing uses unified schema

---

### Step 2.3: Update Contact Log
**File:** `app/routes/contact_log.py`

**Current:** Likely uses entity_type='Owner' with owner_id
**Goal:** Use entity_type='Company' with company_id

**Changes needed:**
1. Update contact log creation to reference companies
2. Update contact log queries to join with companies
3. Migration: Update existing contact_log records to point to companies

**Files to modify:**
- `app/routes/contact_log.py`
- `app/models/contact.py` (if needed)
- Create migration script to update existing contact_log records

**Estimated time:** 1.5 hours

**Checkpoint:** ✅ Contact log uses unified schema

---

### Step 2.4: Update Personnel Routes
**File:** `app/routes/personnel.py`

**Current:** May create PersonnelEntityRelationship records
**Goal:** Use ONLY person_company_affiliations

**Changes needed:**
1. Personnel creation - link via person_company_affiliations
2. Personnel editing - update affiliations instead of entity relationships
3. Remove sync code that writes to both schemas

**Files to modify:**
- `app/routes/personnel.py`
- `app/templates/personnel/create.html`
- `app/templates/personnel/edit.html`

**Estimated time:** 1.5 hours

**Checkpoint:** ✅ Personnel module uses unified schema only

---

### Step 2.5: Update Network Diagram
**File:** `app/services/network_diagram.py`

**Current Status:** According to company_refactor_status.md, this already uses unified schema ✅

**Action:** Verify, no changes needed

**Estimated time:** 15 minutes (verification only)

**Checkpoint:** ✅ Network diagram confirmed using unified schema

---

## Phase 3: Deprecate Legacy Routes

### Step 3.1: Make Legacy Routes Read-Only
**Goal:** Prevent new data from going into legacy tables

**Strategy:** Convert legacy CRUD routes to:
- **List views:** Redirect to `/companies?role=X`
- **Detail views:** Show deprecation warning, redirect to unified view
- **Create/Edit forms:** Disabled with message "Use Companies module"

**Files to modify:**
- `app/routes/vendors.py` - Add redirects
- `app/routes/owners.py` - Add redirects
- `app/routes/operators.py` - Add redirects
- `app/routes/constructors.py` - Add redirects
- `app/routes/offtakers.py` - Add redirects

**Implementation:**
```python
# Example: app/routes/vendors.py

@bp.route('/')
@login_required
def list_vendors():
    """DEPRECATED: Redirect to unified companies view"""
    flash('Vendor management has moved to the unified Companies module', 'info')
    return redirect(url_for('companies.list_companies', role='vendor'))

@bp.route('/<int:vendor_id>')
@login_required
def view_vendor(vendor_id):
    """DEPRECATED: Redirect to unified company view"""
    # Look up corresponding company_id
    from app.services.company_sync import get_company_for_vendor
    company = get_company_for_vendor(vendor_id)
    if company:
        return redirect(url_for('companies.view_company', company_id=company.company_id))
    flash('Vendor not found in unified system', 'warning')
    return redirect(url_for('companies.list_companies', role='vendor'))

# Disable create/edit routes
@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_vendor():
    flash('Please use the Companies module to create new vendors', 'warning')
    return redirect(url_for('companies.create_company'))
```

**Estimated time:** 2 hours (5 files × 20-30 minutes each)

**Checkpoint:** ✅ Legacy routes redirect to unified views

---

### Step 3.2: Update Navigation (Already Done ✅)
**File:** `app/templates/base.html`

**Status:** Already using unified companies URLs

**Action:** Verify, no changes needed

---

### Step 3.3: Add Deprecation Warnings to Models
**Goal:** Make it obvious in code that these models are deprecated

**Files to modify:**
- `app/models/vendor.py`
- `app/models/owner.py`
- `app/models/operator.py`
- `app/models/constructor.py`
- `app/models/offtaker.py`

**Implementation:**
```python
# Example: app/models/vendor.py

class TechnologyVendor(Base, TimestampMixin):
    """
    **DEPRECATED:** Use Company model with role='vendor' instead.

    This model is maintained for backward compatibility only.
    Will be removed in a future version.

    See: app/models/company.py::Company
    """
    __tablename__ = 'technology_vendors'

    # ... rest of model

    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn(
            "TechnologyVendor is deprecated. Use Company with role='vendor' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
```

**Estimated time:** 30 minutes

**Checkpoint:** ✅ Legacy models marked deprecated

---

## Phase 4: Remove Dual-Write Sync Code

### Step 4.1: Remove Sync Functions
**File:** `app/services/company_sync.py`

**Current:** Functions that write to both old and new schemas
**Goal:** Remove dual-write code (keep read helpers for migration)

**Functions to remove/simplify:**
- `sync_vendor_to_company()` - Remove
- `sync_owner_to_company()` - Remove
- `sync_operator_to_company()` - Remove
- `sync_constructor_to_company()` - Remove
- `sync_offtaker_to_company()` - Remove

**Functions to keep (temporarily):**
- `get_company_for_vendor()` - Keep for redirects
- `get_company_for_owner()` - Keep for redirects
- etc.

**Estimated time:** 1 hour

**Checkpoint:** ✅ No more dual writes

---

### Step 4.2: Remove Sync Calls from Routes
**Goal:** Remove calls to sync functions throughout codebase

**Search for:** `sync_.*_to_company`

**Files likely affected:**
- Already done in Step 2 updates
- Verify no lingering calls

**Estimated time:** 30 minutes (verification)

**Checkpoint:** ✅ No sync calls in active code

---

## Phase 5: Testing & Validation

### Step 5.1: Manual Testing Checklist

**Companies Module:**
- [ ] Create new company with role
- [ ] Edit company
- [ ] Add second role to company
- [ ] View company detail page
- [ ] Filter companies by role
- [ ] Delete company (if no relationships)

**Projects Module:**
- [ ] View project detail page
- [ ] Add vendor to project (creates company_role_assignment)
- [ ] Add owner to project
- [ ] Add operator to project
- [ ] Remove company from project
- [ ] Verify NO legacy relationship records created

**Personnel Module:**
- [ ] Create personnel with company affiliation
- [ ] Edit personnel affiliations
- [ ] View personnel detail page showing affiliations
- [ ] Verify NO legacy entity relationships created

**Admin Module:**
- [ ] Permission scrubbing shows unified schema
- [ ] Audit log works correctly
- [ ] Engine cache management works

**Legacy Routes:**
- [ ] Visit `/vendors` → redirects to companies
- [ ] Visit `/vendors/123` → redirects to company view
- [ ] Try to create vendor → blocked/redirected
- [ ] Same for owners, operators, constructors, offtakers

**Navigation:**
- [ ] All menu links work
- [ ] Breadcrumbs correct
- [ ] No 404 errors

**Estimated time:** 1.5 hours

**Checkpoint:** ✅ All manual tests pass

---

### Step 5.2: Run Validation Script

```bash
python scripts/validate_company_migration.py --check-legacy-usage
```

**Should report:**
- ✅ No new records in legacy tables since migration
- ✅ All companies have at least one role assignment
- ✅ All project relationships in company_role_assignments
- ✅ All personnel affiliations in person_company_affiliations

**Estimated time:** 15 minutes

**Checkpoint:** ✅ Validation script passes

---

### Step 5.3: Check for Remaining References

**Search codebase for legacy references:**

```bash
# Search for direct table queries
grep -r "technology_vendors" app/ --include="*.py" | grep -v "# LEGACY" | grep -v "__pycache__"
grep -r "owners_developers" app/ --include="*.py" | grep -v "# LEGACY" | grep -v "__pycache__"
grep -r "operators\." app/ --include="*.py" | grep -v "# LEGACY" | grep -v "__pycache__"
grep -r "constructors\." app/ --include="*.py" | grep -v "# LEGACY" | grep -v "__pycache__"

# Search for legacy relationship models
grep -r "ProjectVendorRelationship" app/ --include="*.py" | grep -v "# LEGACY"
grep -r "ProjectOwnerRelationship" app/ --include="*.py" | grep -v "# LEGACY"
```

**Expected:** Only hits in deprecated model files and migration scripts

**Estimated time:** 30 minutes

**Checkpoint:** ✅ No active code uses legacy tables

---

## Phase 6: Documentation Updates

### Step 6.1: Update Schema Documentation ✅
**File:** `docs/02_DATABASE_SCHEMA.md`

**Status:** Already completed in Phase 1

---

### Step 6.2: Update Relationships Documentation
**File:** `docs/03_DATABASE_RELATIONSHIPS.md`

**Action:** Mark legacy relationships as deprecated, document new unified approach

**Estimated time:** 1 hour

---

### Step 6.3: Update Status Document
**File:** `docs/company_refactor_status.md`

**Action:** Update "Outstanding Work" section to mark migration as complete

**Estimated time:** 15 minutes

---

### Step 6.4: Create User Migration Guide (If Needed)
**File:** `docs/USER_MIGRATION_GUIDE.md`

**Content:**
- Old URLs → New URLs mapping
- How to find your data in unified system
- Benefits of unified schema

**Estimated time:** 30 minutes (if needed)

---

## Phase 7: Cleanup (Future - Not Immediate)

### Step 7.1: Monitor for 3-6 Months
**Goal:** Ensure no unexpected issues

**Actions:**
- Monitor error logs for legacy table references
- Collect user feedback
- Verify no data gaps

---

### Step 7.2: Remove Legacy Code (Future)
**After 3-6 months of stability:**

**Files to delete:**
- `app/routes/vendors.py`
- `app/routes/owners.py`
- `app/routes/operators.py`
- `app/routes/constructors.py`
- `app/routes/offtakers.py`
- `app/forms/vendors.py`
- `app/forms/owners.py`
- `app/forms/operators.py`
- `app/forms/constructors.py`
- `app/forms/offtakers.py`
- `app/templates/vendors/` (entire directory)
- `app/templates/owners/` (entire directory)
- `app/templates/operators/` (entire directory)
- `app/templates/constructors/` (entire directory)
- `app/templates/offtakers/` (entire directory)

**Models to delete:**
- `app/models/vendor.py`
- `app/models/owner.py`
- `app/models/operator.py`
- `app/models/constructor.py`
- `app/models/offtaker.py`
- `app/models/relationships.py` (legacy relationships)

**Update `app/models/__init__.py`:**
- Remove imports of deleted models

---

### Step 7.3: Drop Legacy Database Tables (Future)
**After code cleanup:**

**Create migration:** `007_drop_legacy_tables.sql`

```sql
-- WARNING: This is destructive!
-- Only run after:
-- 1. All code uses unified schema
-- 2. 3-6 months of production stability
-- 3. Recent backup created

BEGIN TRANSACTION;

DROP TABLE IF EXISTS vendor_supplier_relationships;
DROP TABLE IF EXISTS owner_vendor_relationships;
DROP TABLE IF EXISTS project_vendor_relationships;
DROP TABLE IF EXISTS project_constructor_relationships;
DROP TABLE IF EXISTS project_operator_relationships;
DROP TABLE IF EXISTS project_owner_relationships;
DROP TABLE IF EXISTS project_offtaker_relationships;
DROP TABLE IF EXISTS vendor_preferred_constructors;

DROP TABLE IF EXISTS technology_vendors;
DROP TABLE IF EXISTS owners_developers;
DROP TABLE IF EXISTS operators;
DROP TABLE IF EXISTS constructors;
DROP TABLE IF EXISTS offtakers;

-- Update schema version
INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (7, datetime('now'), 'system', 'Drop legacy company tables after unified migration');

COMMIT;
```

---

## Timeline Summary

| Phase | Tasks | Estimated Time | Can Parallelize? |
|-------|-------|----------------|------------------|
| **Phase 1: Prep** | Validation, backup, documentation | 1 hour | No |
| **Phase 2: Code Migration** | Projects, admin, contact log, personnel, network | 6.5 hours | Some tasks yes |
| **Phase 3: Deprecation** | Legacy routes, models | 2.5 hours | Somewhat |
| **Phase 4: Remove Syncs** | Remove dual-write code | 1.5 hours | No |
| **Phase 5: Testing** | Manual testing, validation, checks | 2.25 hours | Somewhat |
| **Phase 6: Docs** | Update documentation | 1.75 hours | Yes |
| **Phase 7: Cleanup** | Future - after stability period | TBD | N/A |

**Total Estimated Time (Phases 1-6):** ~15.5 hours
**Realistic Timeline:** 3-5 work sessions over 1-2 weeks

---

## Risk Mitigation

### High-Risk Areas
1. **Project relationships** - Most critical, heavily used
   - **Mitigation:** Thorough testing, backup before changes

2. **URL redirects** - Users may have bookmarked old URLs
   - **Mitigation:** Keep redirects permanently, not temporary

3. **Data loss** - Accidentally deleting legacy data before validation
   - **Mitigation:** NEVER delete tables in Phases 1-6, only in Phase 7

### Rollback Plan
If critical issues discovered:
1. **Code rollback:** Git revert to pre-migration commit
2. **Database rollback:** Restore from Phase 1.2 snapshot
3. **Partial rollback:** Re-enable specific legacy routes temporarily

---

## Success Criteria

**Phase 2-6 Complete When:**
- ✅ All CRUD operations use unified schema
- ✅ No dual-write sync code remains
- ✅ Legacy routes redirect to unified views
- ✅ All tests pass
- ✅ Validation script reports no issues
- ✅ Documentation updated
- ✅ User communication complete (if needed)

**Phase 7 Complete When:**
- ✅ 3-6 months of production stability
- ✅ No error logs referencing legacy tables
- ✅ Legacy code files deleted
- ✅ Legacy database tables dropped
- ✅ Schema clean and maintainable

---

## Questions Before Starting

1. **Timing:** When do you want to start this migration?
2. **Testing:** Do you have a staging environment, or test directly in development?
3. **Users:** How many active users? Do they need notification about URL changes?
4. **Data:** Have you run `scripts/validate_company_migration.py` recently?
5. **Backup:** Do you have a current backup of your development database?

---

## Next Steps

**Immediate:**
1. ✅ Review this plan
2. ✅ Answer questions above
3. Run validation script (Phase 1.1)
4. Create backup (Phase 1.2)
5. Start with Phase 2.1 (Projects module)

**Ready to proceed?** Let me know and I'll help you execute each phase step-by-step!

---

**Plan End**
