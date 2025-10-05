# Company & Relationship Model Refactor Plan

## Goals
- Consolidate role-specific company tables (`technology_vendors`, `constructors`, `operators`, `owners_developers`, `clients`, etc.) into a unified `companies` table.
- Represent company roles and contexts via `company_roles` and `company_role_assignments` (supports multi-role, project-scoped participation).
- Model enriched CRM data for MPR clients through a `client_profiles` extension with internal relationship tracking.
- Replace polymorphic personnel links with normalized `person_company_affiliations` and explicit internal↔external relationship mappings.
- Deliver a staged migration path that keeps the application operable while features are refactored.

## High-Level Architecture
```
Company (company_id, name, type_flags, headquarters, ...)
  ├─ ClientProfile (company_id PK/FK, relationship_strength, ...)
  ├─ CompanyRoleAssignment (assignment_id, company_id, role_id, context_type, context_id, start/end, notes)
  ├─ CompanyIdentifiers (optional; external ids)
CompanyRole (role_id, code, label, description)
Person (existing `personnel` table evolved)
  ├─ PersonCompanyAffiliation (affiliation_id, person_id, company_id, title, is_primary, dates)
  ├─ InternalExternalLink (link_id, internal_person_id, external_person_id, company_id, relationship_type, strength, notes)

Project relationships (many-to-many) now target CompanyRoleAssignment rows or simply company_id + role filters (TBD in detailed design).
```

## Migration Stages
1. **Schema Introduction**
   - Add new tables: `companies`, `company_roles`, `company_role_assignments`, `client_profiles`, `person_company_affiliations`, `internal_external_links`.
   - Backfill static role catalog.
   - Create SQLAlchemy models + Alembic migration(s).
   - Implement data access helpers (e.g., `CompanyService`).

2. **Data Backfill**
   - Extract existing company data into `companies` and populate baseline role assignments.
   - Map CRM fields from `owners_developers` and `clients` into `client_profiles`.
   - Backfill personnel affiliations from current `organization_type` / `client_relationships`.
   - Keep legacy tables in place for now; maintain sync triggers or one-time copy plus read compatibility layer.

3. **Application Refactor**
   - Introduce repository/service layer that reads from new schema while fall-backing to legacy tables during transition.
   - Update vendor/owner/client CRUD routes sequentially to use `Company` abstractions.
   - Replace personnel relationship views with affiliation-driven queries.
   - Adjust reporting/network views to consume unified model.

4. **Decommission Legacy Tables**
   - After all routes/services rely on new structures, write migration to drop or archive old tables and update docs/tests accordingly.

## Risk Mitigation
- Work feature-by-feature on the branch; keep master deployable.
- Add temporary views or SQLAlchemy models that map legacy tables into the new structure, easing UI updates.
- Ensure comprehensive testing (unit + integration) for new services before swapping UI endpoints.
- Maintain backup snapshots before destructive migrations.

## Immediate Next Steps
1. Implement new SQLAlchemy models + Alembic migration for unified schema (no data movement yet).
2. Create seed/utility functions for role catalog management.
3. Draft data backfill script outline.
```
app/models/company.py
app/models/personnel.py (extensions)
app/models/company_role.py
```
