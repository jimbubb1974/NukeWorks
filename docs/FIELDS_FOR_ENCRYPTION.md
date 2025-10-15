# Fields Requiring Encryption - Analysis

## Overview

This document identifies all fields across models that should be encrypted based on data sensitivity and user access requirements.

---

## Encryption Strategy

### Key Types:
- **'confidential'** - Financial and competitive business data (requires `has_confidential_access=True`)
- **'ned_team'** - Internal team notes and relationship data (requires `is_ned_team=True`)

---

## Fields to Encrypt

### 1. Project Model (`app/models/project.py`)

**Encrypt with 'confidential' key:**
- `capex` (Float) - Capital expenditure
- `opex` (Float) - Operating expenditure
- `fuel_cost` (Float) - Fuel costs
- `lcoe` (Float) - Levelized cost of energy

**Keep as plain text:**
- All other fields (project_name, location, status, dates, etc.)

**Rationale**: Financial data is commercially sensitive and competitive intelligence.

---

### 2. Company Model (`app/models/company.py`)

**Currently no fields need encryption**
- Basic company information (name, type, website, country) is public
- `notes` field could contain sensitive data, but is general purpose

**Future consideration**: If specific financial data is added to Company model

---

### 3. ClientProfile Model (`app/models/company.py`)

**Encrypt with 'ned_team' key:**
- `relationship_strength` (Text) - Internal assessment of relationship quality
- `relationship_notes` (Text) - Internal notes about the client
- `client_priority` (Text) - Internal prioritization
- `client_status` (Text) - Internal status tracking

**Keep as plain text:**
- `last_contact_date`, `last_contact_type`, `last_contact_by`
- `next_planned_contact_date`, `next_planned_contact_type`, `next_planned_contact_assigned_to`

**Rationale**: Relationship assessments and internal notes are NED Team strategic information.

---

### 4. RoundtableHistory Model (`app/models/roundtable.py`)

**Encrypt with 'ned_team' key:**
- `discussion` (Text) - Meeting discussion notes
- `action_items` (Text) - Action items from meeting
- `next_steps` (Text) - Next steps for client
- `client_near_term_focus` (Text) - What client is focusing on
- `mpr_work_targets` (Text) - MPR's internal goals for client

**Keep as plain text:**
- `entity_type`, `entity_id` (needed for queries)
- `created_by`, `created_timestamp` (audit trail)

**Rationale**: All roundtable content is internal NED Team strategic planning.

---

### 5. CompanyRoleAssignment Model (`app/models/company.py`)

**Encrypt with 'confidential' key (if is_confidential=True):**
- `notes` (Text) - Only encrypt if the assignment is marked confidential

**Keep as plain text:**
- All other fields (company_id, role_id, context, dates, is_confidential flag)

**Rationale**: Some role assignments may be confidential (e.g., upcoming contracts not yet public).

**Implementation**: Conditional encryption based on `is_confidential` flag.

---

### 6. InternalExternalLink Model (`app/models/company.py`)

**Encrypt with 'ned_team' key:**
- `relationship_strength` (Text) - Internal assessment
- `notes` (Text) - Internal notes about relationship

**Keep as plain text:**
- `relationship_type` (for filtering/queries)
- Foreign keys and IDs

**Rationale**: Internal relationship assessments are NED Team strategic information.

---

## Summary Table

| Model | Field | Encryption Key | Current Type | New Type | Reason |
|-------|-------|---------------|--------------|----------|--------|
| **Project** | capex | confidential | Float | LargeBinary | Financial data |
| **Project** | opex | confidential | Float | LargeBinary | Financial data |
| **Project** | fuel_cost | confidential | Float | LargeBinary | Financial data |
| **Project** | lcoe | confidential | Float | LargeBinary | Financial data |
| **ClientProfile** | relationship_strength | ned_team | Text | LargeBinary | Internal assessment |
| **ClientProfile** | relationship_notes | ned_team | Text | LargeBinary | Internal notes |
| **ClientProfile** | client_priority | ned_team | Text | LargeBinary | Internal prioritization |
| **ClientProfile** | client_status | ned_team | Text | LargeBinary | Internal status |
| **RoundtableHistory** | discussion | ned_team | Text | LargeBinary | Meeting notes |
| **RoundtableHistory** | action_items | ned_team | Text | LargeBinary | Action items |
| **RoundtableHistory** | next_steps | ned_team | Text | LargeBinary | Internal planning |
| **RoundtableHistory** | client_near_term_focus | ned_team | Text | LargeBinary | Client intel |
| **RoundtableHistory** | mpr_work_targets | ned_team | Text | LargeBinary | Internal strategy |
| **CompanyRoleAssignment** | notes | confidential* | Text | LargeBinary | Conditionally encrypted |
| **InternalExternalLink** | relationship_strength | ned_team | Text | LargeBinary | Internal assessment |
| **InternalExternalLink** | notes | ned_team | Text | LargeBinary | Internal notes |

**Total**: 17 fields across 5 models

*Conditional encryption based on `is_confidential` flag

---

## Implementation Approach

### Phase 3a: Add Encrypted Columns (Non-Breaking)

Add new encrypted columns alongside existing ones:

```sql
-- Projects
ALTER TABLE projects ADD COLUMN capex_encrypted BLOB;
ALTER TABLE projects ADD COLUMN opex_encrypted BLOB;
ALTER TABLE projects ADD COLUMN fuel_cost_encrypted BLOB;
ALTER TABLE projects ADD COLUMN lcoe_encrypted BLOB;

-- ClientProfile
ALTER TABLE client_profiles ADD COLUMN relationship_strength_encrypted BLOB;
ALTER TABLE client_profiles ADD COLUMN relationship_notes_encrypted BLOB;
ALTER TABLE client_profiles ADD COLUMN client_priority_encrypted BLOB;
ALTER TABLE client_profiles ADD COLUMN client_status_encrypted BLOB;

-- RoundtableHistory
ALTER TABLE roundtable_history ADD COLUMN discussion_encrypted BLOB;
ALTER TABLE roundtable_history ADD COLUMN action_items_encrypted BLOB;
ALTER TABLE roundtable_history ADD COLUMN next_steps_encrypted BLOB;
ALTER TABLE roundtable_history ADD COLUMN client_near_term_focus_encrypted BLOB;
ALTER TABLE roundtable_history ADD COLUMN mpr_work_targets_encrypted BLOB;

-- CompanyRoleAssignment
ALTER TABLE company_role_assignments ADD COLUMN notes_encrypted BLOB;

-- InternalExternalLink
ALTER TABLE internal_external_links ADD COLUMN relationship_strength_encrypted BLOB;
ALTER TABLE internal_external_links ADD COLUMN notes_encrypted BLOB;
```

### Phase 3b: Migrate Data

Run migration script that:
1. Reads plain text values
2. Encrypts with appropriate key
3. Stores in `*_encrypted` columns
4. Validates encryption worked

### Phase 3c: Update Models

Update SQLAlchemy models to use `EncryptedField` properties:

```python
# Example: Project model
class Project(Base, TimestampMixin):
    # Encrypted columns (database storage)
    _capex_encrypted = Column('capex_encrypted', LargeBinary)
    _opex_encrypted = Column('opex_encrypted', LargeBinary)
    _fuel_cost_encrypted = Column('fuel_cost_encrypted', LargeBinary)
    _lcoe_encrypted = Column('lcoe_encrypted', LargeBinary)

    # Properties with automatic encryption/decryption
    capex = EncryptedField('_capex_encrypted', 'confidential')
    opex = EncryptedField('_opex_encrypted', 'confidential')
    fuel_cost = EncryptedField('_fuel_cost_encrypted', 'confidential')
    lcoe = EncryptedField('_lcoe_encrypted', 'confidential')
```

### Phase 3d: Deprecate Old Columns (Future)

After validation period:
1. Drop old plain text columns
2. Rename encrypted columns to original names (optional)

---

## Migration Safety

### Rollback Plan

1. Keep old columns during migration
2. Populate new columns without deleting old data
3. Validate encrypted data can be decrypted
4. Only after validation, consider dropping old columns

### Testing Checklist

- [ ] All encrypted values can be decrypted
- [ ] Joe (standard user) sees `[Confidential]` for financial data
- [ ] Sally (confidential access) sees actual financial values
- [ ] NED team members see roundtable notes
- [ ] Non-NED team members see `[NED Team Only]` for roundtable
- [ ] DB Browser shows encrypted gibberish for all encrypted fields
- [ ] Existing queries still work
- [ ] Forms can save encrypted data
- [ ] Reports handle encrypted fields correctly

---

## Notes

### Why Not Encrypt More Fields?

**Project Names, Locations**: Needed for queries, filtering, and public display
**Company Names**: Public information, needed for search
**Dates**: Needed for timeline views and filtering
**Foreign Keys**: Required for relationships and joins
**Audit Fields**: Required for compliance and debugging

### Float to LargeBinary Conversion

Financial fields (capex, opex, etc.) are currently `Float`. When encrypting:
1. Convert Float → String (e.g., `5000000.0` → `"5000000.0"`)
2. Encrypt String → Bytes
3. Store Bytes in LargeBinary column
4. On read: Decrypt Bytes → String → Float

This preserves exact values without floating point precision issues.

---

## Next Steps

1. Create database migration SQL (Phase 3d)
2. Update Project model with encrypted fields
3. Update ClientProfile model with encrypted fields
4. Update RoundtableHistory model with encrypted fields
5. Update CompanyRoleAssignment model with encrypted fields
6. Update InternalExternalLink model with encrypted fields
7. Create data migration script
8. Test all encrypted models
