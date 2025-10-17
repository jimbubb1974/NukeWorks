# NukeWorks - Master Specification

**Application Name:** NukeWorks  
**Version:** 1.0  
**Last Updated:** December 4, 2025  
**Status:** Final for Development

---

## Executive Summary

NukeWorks is a multi-user web-based database application for managing nuclear project data, technology vendors, stakeholders, and client relationships with granular confidentiality controls.

**Key Features:**
- Multi-user SQLite database on network drive
- Two-tier permission system (Confidential Access + NED Team)
- Client Relationship Management (CRM) for tracking interactions
- Network diagram visualization of relationships
- PDF report generation with confidentiality filtering
- Automated backup/snapshot system
- Database migration system for schema evolution

**Target Users:** 20-50 team members (1-2 concurrent typical)  
**Deployment:** Standalone Windows .exe per user

---

## Document Structure

This specification is organized into modular documents for efficient agent processing. Each document is self-contained but references others when necessary.

### Core Documents (Always Start Here)
- **`00_MASTER_SPECIFICATION.md`** (this document) - Overview and navigation
- **`01_ARCHITECTURE.md`** - System architecture, tech stack, deployment model

### Data Layer Documents
- **`02_DATABASE_SCHEMA.md`** ⭐ - Core entity tables with SQL definitions
- **`03_DATABASE_RELATIONSHIPS.md`** - Junction tables and relationships
- **`04_DATA_DICTIONARY.md`** - Field definitions, enums, validation rules

### Business Logic Documents
- **`05_PERMISSION_SYSTEM.md`** - Two-tier confidentiality and access control
- **`06_BUSINESS_RULES.md`** - Data validation, workflows, constraints
- **`07_MIGRATION_SYSTEM.md`** - Schema evolution and migration patterns

### User Interface Documents
- **`08_UI_VIEWS_CORE.md`** - Dashboard, entity lists, detail views
- **`09_UI_VIEWS_CRM.md`** - CRM dashboard, roundtable meetings, contact tracking
- **`10_UI_VIEWS_ADMIN.md`** - User management, system settings, permissions
- **`11_NETWORK_DIAGRAM.md`** - Visualization specifications and interactions

### Feature Documents
- **`12_REPORTS.md`** - Three PDF reports with layouts and specifications
- **`13_IMPORT_EXPORT.md`** - Excel/CSV import/export functionality
- **`14_AUDIT_SNAPSHOTS.md`** - Audit logging and backup systems
- **`15_SETUP_WIZARD.md`** - Initial setup and configuration wizard

### Implementation Documents
- **`16_API_ENDPOINTS.md`** - Internal API routes and responses
- **`17_TESTING_REQUIREMENTS.md`** - Unit, integration, and E2E tests
- **`18_ERROR_HANDLING.md`** - Error codes, messages, recovery strategies
- **`19_SECURITY.md`** - Authentication, validation, security best practices

### Reference Documents
- **`20_GLOSSARY.md`** - Terms and definitions
- **`21_TROUBLESHOOTING.md`** - Common issues and solutions
- **`22_IMPLEMENTATION_CHECKLIST.md`** - Step-by-step development guide

### Additional Documentation (October 2025)

**Company Unification & Migration**
- **`COMPANY_UNIFICATION.md`** - Unified company schema migration (WORK IN PROGRESS)
- **`docs/MIGRATION_PLAN.md`** - Production migration procedures

**Encryption Implementation**
- **`ENCRYPTION_IMPLEMENTATION_STATUS.md`** ⭐ - Current encryption status by phase
- **`ENCRYPTION_IMPLEMENTATION_PLAN.md`** - Detailed field analysis and implementation roadmap

**Implementation Guides**
- **`AUTH_IMPLEMENTATION.md`** - User authentication system
- **`PERMISSION_SYSTEM_IMPLEMENTATION.md`** - Permission system implementation
- **`VALIDATION_SYSTEM_IMPLEMENTATION.md`** - Comprehensive validation with 50+ tests
- **`VENDOR_CRUD_IMPLEMENTATION.md`** - Complete CRUD pattern reference
- **`CRM_CLIENTS_IMPLEMENTATION.md`** - CRM client management implementation

---

## Quick Start for Coding Agents

### Recommended Reading Order

**For Initial Context (Read First):**
1. This document (00_MASTER_SPECIFICATION.md)
2. `01_ARCHITECTURE.md` - Understand system design
3. `02_DATABASE_SCHEMA.md` - Understand data model

**For Specific Development Tasks:**
- Building database → Load: `02`, `03`, `04`
- Building authentication → Load: `02`, `05`, `19`
- Building UI → Load: `02`, `05`, `08`, `09`, `10`
- Building reports → Load: `02`, `05`, `12`
- Writing tests → Load: `17`

### Agent Task Examples

**Task: "Create the database schema"**
```
Required Documents:
- 02_DATABASE_SCHEMA.md (all core tables)
- 03_DATABASE_RELATIONSHIPS.md (junction tables)
- 04_DATA_DICTIONARY.md (field constraints)

Expected Output:
- SQL schema creation scripts
- SQLAlchemy models (or similar ORM)
- Initial migration file
```

**Task: "Implement the permission system"**
```
Required Documents:
- 02_DATABASE_SCHEMA.md (Users, Confidential_Field_Flags tables)
- 05_PERMISSION_SYSTEM.md (permission logic)
- 19_SECURITY.md (security considerations)

Expected Output:
- Permission checking functions
- User authentication middleware
- Access control decorators
```

**Task: "Build the CRM dashboard"**
```
Required Documents:
- 02_DATABASE_SCHEMA.md (Owners_Developers, Contact_Log, Roundtable_History)
- 05_PERMISSION_SYSTEM.md (NED Team access)
- 09_UI_VIEWS_CRM.md (UI specifications)

Expected Output:
- CRM dashboard template
- Contact logging functionality
- Roundtable history management
```

**Task: "Generate Project Summary Report"**
```
Required Documents:
- 02_DATABASE_SCHEMA.md (Projects table)
- 05_PERMISSION_SYSTEM.md (confidentiality filtering)
- 12_REPORTS.md (report layout and structure)

Expected Output:
- PDF generation function
- Report template
- Confidentiality filtering logic
```

---

## Technology Stack Summary

**Backend:**
- Python 3.9+
- Flask (web framework)
- SQLite 3 (database)
- SQLAlchemy (ORM recommended)

**Frontend:**
- HTML5, CSS3, JavaScript
- Vis.js or Cytoscape.js (network diagram)

**Reports:**
- ReportLab or WeasyPrint (PDF generation)
- openpyxl or xlsxwriter (Excel export)

**Packaging:**
- PyInstaller (create standalone .exe)

**See `01_ARCHITECTURE.md` for complete details**

---

## Critical Architecture Decisions

### Database
- **File-based SQLite** on Windows network drive
- **WAL mode** enabled for better concurrent access
- **Optimistic locking** for conflict detection
- Maximum supported size: 1GB

### Deployment
- Each user runs **local Flask server** (localhost:5000)
- Application auto-launches browser
- All users connect to **same shared database file**

### Permissions
- **Two-tier system:**
  - Tier 1: Confidential Access (business data)
  - Tier 2: NED Team (internal strategy notes)
- **Independent permissions** - users can have either, both, or neither

### Concurrency
- **Optimistic locking** - detect conflicts at save time
- **Timestamp-based** conflict detection
- **Automatic retry** for database locks (up to 5 attempts)

---

## Implementation Priorities

### Phase 1: MVP (Must Have)
✅ Core entity CRUD operations  
✅ User authentication  
✅ Basic permission system (Tier 1)  
✅ Entity list and detail views  
✅ Field-level confidentiality  
✅ Basic network diagram  
✅ Project Summary Report  
✅ Manual snapshots  
✅ Initial setup wizard  

### Phase 2: Enhanced (Should Have)
✅ NED Team access (Tier 2)  
✅ CRM features (contact tracking, roundtable notes)  
✅ All three PDF reports  
✅ Interactive network diagram  
✅ Automated snapshots  
✅ Excel/CSV import  
✅ Migration system  
✅ Admin permission scrubbing  

### Phase 3: Encryption & Polish (In Progress)
✅ Per-field encryption for financial data (Project model - LIVE)
⏳ Per-field encryption for CRM notes (pending Phases 3b-3e)
⚪ Advanced search
⚪ Performance optimization
⚪ Enhanced network layouts
⚪ Batch operations
⚪ Mobile-responsive improvements

### Phase 4: Company Unification (In Progress)
✅ Unified company schema created (Companies, CompanyRoles, CompanyRoleAssignments)
✅ Backfill scripts prepared and tested in dev/staging
✅ CRUD operations sync to unified schema
⏳ Production migration (awaiting rollout approval)
⏳ Legacy table cleanup (3-6 months post-migration)

---

## Key Entities Overview

**Core Business Entities:**
- **Technology_Vendors** - Nuclear technology companies
- **Products** - Specific reactor designs
- **Owners_Developers** - Utilities and project developers
- **Projects** - Specific nuclear projects/sites
- **Constructors** - Construction companies
- **Operators** - Facility operators
- **Personnel** - People (internal and external)

**Relationship Types:**
- Vendor ↔ Supplier (component providers)
- Owner ↔ Vendor (MOUs, agreements, contracts)
- Project → Vendor, Constructor, Operator, Owner
- Vendor → Preferred Constructor
- Personnel → Any entity (work relationships)

**Support Tables:**
- **Users** - Application users with permissions
- **Contact_Log** - Client interaction history
- **Roundtable_History** - Internal meeting notes (NED Team only)
- **Audit_Log** - All data modifications
- **Database_Snapshots** - Backup metadata

**See `02_DATABASE_SCHEMA.md` for complete table definitions**

---

## Permission Levels Summary

**Regular User:**
- View public data only
- Cannot see confidential fields
- Cannot see confidential relationships
- Cannot access CRM internal notes

**User with Confidential Access:**
- View public + confidential business data
- See CAPEX, OPEX, confidential relationships
- Still cannot access CRM internal notes

**NED Team Member:**
- View CRM internal notes (client assessments, roundtable discussions)
- May or may not have Confidential Access (independent)

**Administrator:**
- Full access to everything
- User management
- System settings
- Snapshot management

**See `05_PERMISSION_SYSTEM.md` for detailed logic**

---

## Development Timeline Estimate

**Conservative: 20-29 weeks (5-7 months)**
- Core functionality: 8-12 weeks
- Enhanced features: 6-8 weeks
- Testing: 4-6 weeks
- Documentation: 2-3 weeks

**Aggressive: 13-19 weeks (3-5 months)**
- Core functionality: 6-8 weeks
- Enhanced features: 4-6 weeks
- Testing: 2-3 weeks
- Documentation: 1-2 weeks

**See `22_IMPLEMENTATION_CHECKLIST.md` for detailed sequence**

---

## Success Criteria

### Functional Requirements
✅ All CRUD operations working  
✅ Confidential data properly hidden  
✅ NED Team content restricted  
✅ All three reports generate correctly  
✅ Network diagram displays relationships  
✅ CRM tracks contacts and meetings  
✅ Audit log captures changes  
✅ Snapshots create and restore  
✅ Migrations apply successfully  
✅ Multiple concurrent users supported  

### Quality Requirements
✅ App starts in <10 seconds  
✅ UI responds in <2 seconds  
✅ No data corruption  
✅ Test coverage >80%  
✅ Zero critical security vulnerabilities  
✅ Graceful error handling  

---

## Common Development Questions

**Q: Where do I start?**
A: Read `01_ARCHITECTURE.md`, then build the database schema using `02_DATABASE_SCHEMA.md` and `03_DATABASE_RELATIONSHIPS.md`.

**Q: How do I handle permissions?**
A: Follow the logic in `05_PERMISSION_SYSTEM.md`. Use helper functions `can_view_field()`, `can_view_relationship()`, and `can_view_ned_content()`.

**Q: What about testing?**
A: See `17_TESTING_REQUIREMENTS.md` for unit, integration, and E2E test requirements. Aim for >80% coverage.

**Q: How do I package the application?**
A: Use PyInstaller. Configuration details in `01_ARCHITECTURE.md` section 17.3.

**Q: What if the database schema needs to change?**
A: Use the migration system described in `07_MIGRATION_SYSTEM.md`. Never modify the schema directly.

**Q: How do I handle errors?**
A: See `18_ERROR_HANDLING.md` for error codes and recovery strategies.

---

## Contact & Support

**Project Owner:** [Your Organization]  
**Technical Lead:** [Name]  
**Documentation Maintainer:** [Name]

**For Questions:**
- Review appropriate specification document
- Check `21_TROUBLESHOOTING.md` for common issues
- Check `20_GLOSSARY.md` for terminology

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Dec 4, 2025 | Initial specification | [Author] |

---

## Next Steps for Agents

1. **Read** `01_ARCHITECTURE.md` for system overview
2. **Study** `02_DATABASE_SCHEMA.md` to understand data model
3. **Review** `22_IMPLEMENTATION_CHECKLIST.md` for build sequence
4. **Begin** with database schema implementation
5. **Test** continuously as you build

**Good luck building NukeWorks!**