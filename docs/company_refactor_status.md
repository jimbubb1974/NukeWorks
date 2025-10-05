# Company Schema Refactor Status

## Background & Goals
- **Legacy Structure**: Company contexts were modeled with independent tables and modules (`technology_vendors.py`, `owners.py`, `operators.py`, `constructors.py`, `offtakers.py`, `client.py`, etc.), each with dedicated CRUD flows and relationship join tables.
- **Problem**: The fractured schema made it difficult to represent organizations that play multiple roles (e.g., Holtec as vendor/operator/developer), share data across modules, and maintain consistent CRM/analytics views.
- **Objective**: Converge on a unified `companies` table with role assignments, richer CRM/client profiles, normalized personnel affiliations, and centralized reporting, while keeping existing screens functional during the transition.

## Completed Work
- **Unified Schema Artifacts**
  - Added `Company`, `CompanyRole`, `CompanyRoleAssignment`, `ClientProfile`, `PersonCompanyAffiliation`, and `InternalExternalLink` ORM models plus migration `005_company_unification.sql`.
  - Implemented `app/services/company_sync.py` and `company_query.py` to mirror vendors, owners, clients, operators, constructors, and off-takers into the unified schema.
  - Hardened sync helpers to reuse existing `companies` rows when names collide (idempotent backfills).

- **CRUD Integration**
  - Vendor/Owner/Client/Operator/Constructor/Off-taker create & edit flows now sync to the new schema.
  - List/detail templates surface unified company IDs so users can verify linkage.
  - Added full constructors module (forms, routes, templates) wired to the unified model.

- **Backfill & Reporting**
  - `scripts/backfill_companies.py` populates the unified tables from legacy data (dev run: vendors 13, owners 24, clients 1, operators 4, constructors 5, off-takers 6).
  - `scripts/companies_report.py` summarizes company counts by role.

- **Navigation & Views**
  - Added `/companies` list view with role filtering and back-links to legacy pages.
  - Updated network diagram service to build nodes/edges from unified company assignments and link to the new detail pages.

- **Test Harness**
  - `conftest.py` spins up a test app/session; pytest suite runs successfully (19 tests) though legacy warnings remain.

- **Personnel Affiliations**
  - Added `sync_personnel_affiliation()` to migrate `PersonnelEntityRelationship` → `PersonCompanyAffiliation`.
  - Updated personnel relationship creation in owners, vendors, and projects routes to sync to unified schema.
  - Created `scripts/backfill_personnel_affiliations.py` to migrate existing personnel-entity relationships.

- **Project Relationships**
  - Added sync functions for all project relationship types (vendor, constructor, operator, owner, offtaker) to create `CompanyRoleAssignment` records with context_type='Project'.
  - Updated project relationship CRUD flows in `app/routes/projects.py` to sync on create.
  - Created `scripts/backfill_project_relationships.py` to migrate existing project relationships.
  - Network diagram already uses unified company assignments via `assignment_index`.

- **Analytical Views**
  - Updated main dashboard (`app/routes/dashboard.py`) to query company counts from unified schema using role-based filtering.
  - Created `app/services/company_analytics.py` with helper functions for unified schema analytics:
    - `get_company_counts_by_role()` - Company counts by role
    - `get_companies_by_role()` - List companies by role
    - `get_companies_for_project()` - All companies on a project
    - `get_project_participation_summary()` - Project participation statistics
  - Project summary reports (`app/reports/project_summary.py`) continue to work with legacy relationships (no changes needed).
  - Network table view (`app/routes/network_view.py`) identified as future candidate for unified schema migration (complex, deferred).

- **Migration Tooling**
  - Created comprehensive backfill and validation tooling:
    - `scripts/backfill_all.py` - Master script runs all backfills in correct order with progress reporting
    - `scripts/validate_company_migration.py` - Validates migration integrity, checks coverage, detects duplicates
    - `scripts/resolve_duplicate_companies.py` - Interactive utility to identify and merge duplicate companies
    - `scripts/README.md` - Complete documentation for all migration scripts
  - All scripts support `--dry-run` mode and multiple environments (dev/staging/production)
  - Migration is idempotent and safe to run multiple times

- **Migration Documentation**
  - Created `docs/MIGRATION_PLAN.md` with step-by-step production migration procedures
  - Includes pre-migration checklist, rollback plans, success criteria, and troubleshooting guide
  - Documented common issues and resolution strategies

## Outstanding Work

- **Production Backfill Rollout**
  - Execute migration plan against staging environment
  - Validate staging results and monitor for 24-48 hours
  - Execute migration plan against production environment
  - See `docs/MIGRATION_PLAN.md` for detailed procedures

- **Optional Future Enhancements**
  - Migrate network table view (`app/routes/network_view.py`) to query unified schema (complex, currently deferred)
  - Address deprecation warnings (UTC timestamps, reportlab)
  - Post-migration cleanup: drop legacy tables after 3-6 months of stability

- **Post-Migration Monitoring** (After Production Rollout)
  - Monitor application logs for errors
  - Collect user feedback on data accuracy
  - Track performance metrics (dashboard load times, report generation)
  - Resolve any duplicates flagged by validation tool
