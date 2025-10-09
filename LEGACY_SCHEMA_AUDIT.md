# Legacy Schema Audit Report
**Date:** 2025-10-07
**Purpose:** Identify all remaining references to legacy company-type-specific tables

## Executive Summary

The application has partially migrated from a legacy schema with separate tables for each company type (`technology_vendors`, `owners_developers`, `constructors`, `operators`, `offtakers`) to a unified `companies` table with role-based relationships via `company_role_assignments`.

However, **significant legacy code remains** that still references the old schema. This audit identifies all locations requiring updates.

---

## Legacy Schema Components Still in Use

### 1. **Model Files** (5 files)
Legacy company-type models that still exist:

| File | Table Name | Status |
|------|-----------|--------|
| `app/models/vendor.py` | `technology_vendors` | **LEGACY** - Still defined, imported, used |
| `app/models/owner.py` | `owners_developers` | **LEGACY** - Still defined, imported, used |
| `app/models/operator.py` | `operators` | **LEGACY** - Still defined, imported, used |
| `app/models/constructor.py` | `constructors` | **LEGACY** - Still defined, imported, used |
| `app/models/offtaker.py` | `offtakers` | **LEGACY** - Still defined, imported, used |

**Impact:** These models are actively imported in `app/models/__init__.py` and used throughout the application.

---

### 2. **Relationship Models** (8 relationship tables)
Legacy junction tables connecting old company types:

| Relationship Class | Table Name | Foreign Keys |
|-------------------|-----------|--------------|
| `VendorSupplierRelationship` | `vendor_supplier_relationships` | `technology_vendors` → `technology_vendors` |
| `OwnerVendorRelationship` | `owner_vendor_relationships` | `owners_developers` → `technology_vendors` |
| `ProjectVendorRelationship` | `project_vendor_relationships` | `projects` → `technology_vendors` |
| `ProjectConstructorRelationship` | `project_constructor_relationships` | `projects` → `constructors` |
| `ProjectOperatorRelationship` | `project_operator_relationships` | `projects` → `operators` |
| `ProjectOwnerRelationship` | `project_owner_relationships` | `projects` → `owners_developers` |
| `ProjectOfftakerRelationship` | `project_offtaker_relationships` | `projects` → `offtakers` |
| `VendorPreferredConstructor` | `vendor_preferred_constructors` | `technology_vendors` → `constructors` |

**File:** `app/models/relationships.py`

**Impact:** All defined in one file, but extensively used for project relationships throughout the app.

---

### 3. **Route Files** (5 files)
Complete CRUD route files for legacy entities:

| File | Blueprint Name | Endpoints | Status |
|------|---------------|-----------|--------|
| `app/routes/vendors.py` | `vendors` | `/vendors/*` | **LEGACY** - Full CRUD |
| `app/routes/owners.py` | `owners` | `/owners/*` | **LEGACY** - Full CRUD + CRM |
| `app/routes/operators.py` | `operators` | `/operators/*` | **LEGACY** - Full CRUD |
| `app/routes/constructors.py` | `constructors` | `/constructors/*` | **LEGACY** - Full CRUD |
| `app/routes/offtakers.py` | `offtakers` | `/offtakers/*` | **LEGACY** - Full CRUD |

**Registered in:** `app/__init__.py` lines 306, 308-310, 313

**Impact:** These blueprints are still registered and accessible. Users can still create/edit entities using old schema.

---

### 4. **Form Files** (5 files)
WTForms for legacy entities:

| File | Forms Defined |
|------|--------------|
| `app/forms/vendors.py` | `VendorForm`, `VendorFilterForm`, `ProductForm` |
| `app/forms/owners.py` | `OwnerForm`, `OwnerFilterForm` |
| `app/forms/operators.py` | `OperatorForm`, `OperatorFilterForm` |
| `app/forms/constructors.py` | `ConstructorForm`, `ConstructorFilterForm` |
| `app/forms/offtakers.py` | `OfftakerForm`, `OfftakerFilterForm` |

**Impact:** Forms used by legacy route files for validation.

---

### 5. **Template Directories** (5 directories)
Complete template sets for legacy entities:

| Directory | Templates |
|-----------|-----------|
| `app/templates/vendors/` | list.html, view.html, create.html, edit.html, etc. |
| `app/templates/owners/` | list.html, view.html, create.html, edit.html, etc. |
| `app/templates/operators/` | list.html, view.html, create.html, edit.html, etc. |
| `app/templates/constructors/` | list.html, view.html, create.html, edit.html, etc. |
| `app/templates/offtakers/` | list.html, view.html, create.html, edit.html, etc. |

**Impact:** 74 template references found to legacy routes (from grep count).

---

### 6. **Mixed References in Active Code**

#### `app/routes/admin.py`
- **Lines 17-28:** Imports legacy models (`TechnologyVendor`, `OwnerDeveloper`, `VendorSupplierRelationship`, etc.)
- **Lines 69-102:** `RELATIONSHIP_CONFIG` dict defines permission scrubbing for legacy relationship types
- **Line 147:** `_resolve_field_display()` handles `owners_developers` table
- Used in admin permission scrubbing interface

#### `app/routes/projects.py`
- Likely uses legacy relationship models for project associations
- Needs verification

#### `app/routes/relationship_utils.py`
- Utility functions for managing legacy relationships
- Needs full audit

#### `app/routes/contact_log.py`
- May reference legacy entities for contact logging
- Needs verification

#### `app/routes/personnel.py`
- May link personnel to legacy company entities
- Needs verification

#### `app/routes/network.py` and `app/routes/network_view.py`
- Network diagram generation
- May visualize legacy relationships
- Needs verification

---

### 7. **Service Files**

#### `app/services/network_diagram.py`
- Generates network visualizations
- Likely uses legacy relationship tables
- Needs verification

#### `app/services/company_sync.py`
- Synchronization between legacy and new schema
- **File contains:** Backfill functions to sync legacy → unified schema
- **Status:** Transitional code, should remain until migration complete

---

### 8. **Utility Files**

#### `app/utils/validators.py`
- May validate legacy entity relationships
- Needs verification

---

### 9. **Migration/Backfill Scripts** (4 files)
Scripts to migrate legacy data to new schema:

| File | Purpose |
|------|---------|
| `scripts/backfill_companies.py` | Migrate legacy entities → companies table |
| `scripts/backfill_project_relationships.py` | Migrate project relationships → company_role_assignments |
| `scripts/backfill_all.py` | Master script to run all backfills |
| `scripts/validate_company_migration.py` | Validate migration completeness |

**Status:** These are transitional tools, should remain available but documented as migration aids.

---

### 10. **Test Files** (2+ files)
- `test_validators.py` - May test legacy entity validation
- `test_permissions.py` - May test legacy entity permissions
- Likely more tests exist

---

### 11. **Documentation Files**
- `VENDOR_CRUD_IMPLEMENTATION.md` - Documents legacy vendor CRUD
- `SCHEMA_IMPLEMENTATION.md` - May reference both schemas
- Need review for accuracy

---

## Navigation Status ✅

**Good News:** The main navigation in `app/templates/base.html` has been **successfully updated** to use the unified schema:
- Lines 43-46 use `url_for('companies.list_companies', role='vendor|developer|operator|constructor')`
- No direct links to legacy `/vendors`, `/owners`, etc. in main nav

---

## Data Flow Analysis

### Current Architecture:
```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
├─────────────────────────────────────────────────────────┤
│  NEW: /companies?role=vendor                            │
│  OLD: /vendors, /owners, /operators, /constructors      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Route Handlers                        │
├─────────────────────────────────────────────────────────┤
│  NEW: companies.py → Company model                      │
│  OLD: vendors.py → TechnologyVendor model               │
│       owners.py → OwnerDeveloper model                  │
│       operators.py → Operator model                     │
│       constructors.py → Constructor model               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Database Layer                        │
├─────────────────────────────────────────────────────────┤
│  NEW: companies                                          │
│       company_roles                                      │
│       company_role_assignments                          │
│                                                          │
│  OLD: technology_vendors                                │
│       owners_developers                                 │
│       operators                                         │
│       constructors                                      │
│       offtakers                                         │
│       (+ 8 relationship junction tables)                │
└─────────────────────────────────────────────────────────┘
```

### Problem:
**Two parallel systems exist** - users can access both, leading to:
1. Data inconsistency (which is authoritative?)
2. Confusion (two ways to do the same thing)
3. Maintenance burden (changes need to be made twice)

---

## Risk Assessment

### High Risk Items:
1. **Legacy routes still registered** - Users can still create/edit using old schema
2. **Admin permission scrubbing** - Uses legacy relationship types
3. **Project relationships** - May still create legacy relationship records
4. **Network diagrams** - May only show legacy relationships

### Medium Risk Items:
1. **Contact logging** - May reference legacy entities
2. **Personnel affiliations** - May link to legacy tables
3. **Validators** - May enforce legacy constraints
4. **Tests** - May validate legacy behavior

### Low Risk Items:
1. **Migration scripts** - Transitional, can remain
2. **Documentation** - Can be updated post-migration
3. **Main navigation** - Already updated ✅

---

## Recommended Migration Strategy

### Phase 1: Discovery & Analysis (CURRENT)
- ✅ Audit complete - this document

### Phase 2: Data Verification
1. Run `scripts/validate_company_migration.py` to check data consistency
2. Identify any legacy-only records not yet migrated
3. Run backfill scripts if needed

### Phase 3: Code Migration (Suggested Order)

#### Step 1: Update Project Relationships
- File: `app/routes/projects.py`
- Change: Use `company_role_assignments` instead of `project_vendor_relationships`, etc.
- **Critical:** Projects are central to the app

#### Step 2: Update Admin Permission Scrubbing
- File: `app/routes/admin.py`
- Update `RELATIONSHIP_CONFIG` to use new schema
- Update `_resolve_field_display()` for companies table

#### Step 3: Deprecate Legacy Routes
- Comment out blueprint registrations in `app/__init__.py`
- Add deprecation warnings to legacy routes
- OR: Make legacy routes read-only (prevent creates/edits)

#### Step 4: Update Remaining Services
- `app/services/network_diagram.py` - Use company_role_assignments
- `app/routes/contact_log.py` - Reference companies table
- `app/routes/personnel.py` - Use person_company_affiliations

#### Step 5: Remove Legacy Code (Final)
- Delete legacy route files
- Delete legacy form files
- Delete legacy template directories
- Delete legacy model files
- Update `app/models/__init__.py`

### Phase 4: Testing
1. Update test files to use new schema
2. Add integration tests for company_role_assignments
3. Test all project workflows end-to-end

### Phase 5: Documentation
1. Update `SCHEMA_IMPLEMENTATION.md`
2. Archive `VENDOR_CRUD_IMPLEMENTATION.md`
3. Document new company/role workflow

---

## Questions for Stakeholder

Before proceeding with code changes:

1. **Data Status:** Have all legacy records been migrated to the new schema? Should we run validation?

2. **Backwards Compatibility:** Do we need to support reading from legacy tables, or can we fully switch over?

3. **Migration Path:** Should we:
   - Make legacy routes read-only first?
   - Delete them immediately?
   - Keep them but redirect to new routes?

4. **Timeline:** Is this a complete switch-over, or do we need both systems running temporarily?

5. **Testing:** Do you have test data in both schemas we should preserve?

---

## File Count Summary

| Category | Count | Status |
|----------|-------|--------|
| Legacy Model Files | 5 | Active |
| Legacy Relationship Models | 8 | Active |
| Legacy Route Files | 5 | Active, Registered |
| Legacy Form Files | 5 | Active |
| Legacy Template Dirs | 5 | Active (~74 refs) |
| Migration Scripts | 4 | Transitional |
| Service Files w/ Legacy Refs | 2+ | Needs audit |
| Utility Files w/ Legacy Refs | 1+ | Needs audit |
| Test Files w/ Legacy Refs | 2+ | Needs audit |

**Total Affected Files:** ~40+ files

---

## Next Steps

**Immediate:**
1. ✅ Review this audit report
2. Answer stakeholder questions above
3. Run `scripts/validate_company_migration.py` to verify data migration status

**Once approved:**
1. Create detailed implementation plan for Phase 3
2. Begin with Step 1 (Project relationships)
3. Proceed methodically through each step with testing

**DO NOT proceed with code changes until strategy is confirmed.**
