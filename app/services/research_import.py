"""
Research import service.

Parses an AI research agent response, diffs it against current DB state,
and writes staged ResearchQueueItem rows for human review.

NOTE: This module is intentionally minimal for Phase 1. It validates the
incoming JSON structure and stages items but does not yet apply field-level
diffs or handle relationship imports. Those are completed after the first
real test run against the prompt so the parser can be tuned to actual output.
"""
import json
from datetime import datetime


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

REQUIRED_TOP_KEYS = {'metadata', 'entities'}
REQUIRED_COMPANY_KEYS = {'db_id', 'slug', 'company_name', 'sources'}
REQUIRED_PROJECT_KEYS = {'db_id', 'slug', 'project_name', 'sources'}

VALID_COMPANY_TYPES = {
    'IOU', 'COOP', 'Public Power', 'IPP', 'Vendor',
    'Constructor', 'Operator', 'Offtaker', 'Developer', 'Government', 'Other',
}
VALID_COMPANY_ROLES = {'vendor', 'owner_developer', 'constructor', 'operator', 'offtaker'}
VALID_PROJECT_STATUS = {
    'Planning', 'Design', 'Licensing', 'Construction',
    'Operating', 'On Hold', 'Cancelled', 'Decommissioned',
}
VALID_LICENSING_APPROACH = {
    'Part 50', 'Part 52', 'Research Reactor', 'NRC Pre-application', 'CNSC', 'Other',
}
VALID_PROJECT_HEALTH = {
    'On Track', 'Delayed', 'At Risk', 'Stalled', 'Cancelled', 'Operating',
}
VALID_FIRM_INVOLVEMENT = {
    'Lead Consultant', 'Supporting Consultant', 'Proposal Phase', 'Monitoring', 'None',
}
VALID_RELATIONSHIP_TYPES = {
    'MOU', 'Letter_of_Intent', 'Development_Agreement', 'Delivery_Contract',
    'Framework_Agreement', 'Supply_Agreement', 'Preferred_Constructor',
    'Equity_Investment', 'Joint_Venture', 'Other',
}

# Normalisation maps for common agent enum drift
_COMPANY_TYPE_NORM = {
    'investor-owned utility': 'IOU',
    'investor owned utility': 'IOU',
    'cooperative': 'COOP',
    'electric cooperative': 'COOP',
    'independent power producer': 'IPP',
    'technology vendor': 'Vendor',
    'epc': 'Constructor',
    'engineering': 'Constructor',
    'national laboratory': 'Government',
    'national lab': 'Government',
}
_PROJECT_STATUS_NORM = {
    'under construction': 'Construction',
    'in construction': 'Construction',
    'in planning': 'Planning',
    'pre-licensing': 'Licensing',
    'pre-application': 'Licensing',
    'operational': 'Operating',
    'in operation': 'Operating',
    'in service': 'Operating',
    'on hold': 'On Hold',
    'suspended': 'On Hold',
    'terminated': 'Cancelled',
}
_PROJECT_HEALTH_NORM = {
    'on-track': 'On Track',
    'on track': 'On Track',
    'at-risk': 'At Risk',
    'at risk': 'At Risk',
}


def _normalise_enum(value, valid_set, norm_map=None):
    """Return a valid enum value or None if unrecognised."""
    if value is None:
        return None
    if value in valid_set:
        return value
    lowered = value.lower().strip()
    if norm_map and lowered in norm_map:
        candidate = norm_map[lowered]
        if candidate in valid_set:
            return candidate
    # Try case-insensitive match
    for v in valid_set:
        if v.lower() == lowered:
            return v
    return None  # unrecognised — will be stored as-is with a warning note


def validate_structure(payload: dict) -> list[str]:
    """
    Validate top-level JSON structure.
    Returns a list of error strings (empty = valid).
    """
    errors = []
    missing = REQUIRED_TOP_KEYS - set(payload.keys())
    if missing:
        errors.append(f'Missing required top-level keys: {missing}')
        return errors  # can't continue without entities

    entities = payload.get('entities', {})
    if not isinstance(entities, dict):
        errors.append('"entities" must be an object.')
        return errors

    for company in entities.get('companies', []):
        missing = REQUIRED_COMPANY_KEYS - set(company.keys())
        if missing:
            name = company.get('company_name', '<unknown>')
            errors.append(f'Company "{name}" missing required keys: {missing}')

    for project in entities.get('projects', []):
        missing = REQUIRED_PROJECT_KEYS - set(project.keys())
        if missing:
            name = project.get('project_name', '<unknown>')
            errors.append(f'Project "{name}" missing required keys: {missing}')

    return errors


# ---------------------------------------------------------------------------
# Main staging function
# ---------------------------------------------------------------------------

def parse_and_stage(payload: dict, run_id: int, db_session) -> int:
    """
    Parse one AI response file and write ResearchQueueItem rows.

    Returns the number of items staged.
    Raises ValueError if the payload fails structural validation.
    """
    errors = validate_structure(payload)
    if errors:
        raise ValueError('Response failed validation: ' + '; '.join(errors[:3]))

    from app.models import ResearchQueueItem, Company, Project

    staged = 0

    entities = payload.get('entities', {})

    # --- Stage company items ---
    for raw in entities.get('companies', []):
        item = _stage_company(raw, run_id, db_session)
        if item:
            db_session.add(item)
            staged += 1

    # --- Stage project items ---
    for raw in entities.get('projects', []):
        item = _stage_project(raw, run_id, db_session)
        if item:
            db_session.add(item)
            staged += 1

    # --- Stage relationship items ---
    relationships = payload.get('relationships', {})
    for raw in relationships.get('project_company', []):
        item = _stage_relationship(raw, 'project_company', run_id)
        if item:
            db_session.add(item)
            staged += 1

    for raw in relationships.get('company_company', []):
        item = _stage_relationship(raw, 'company_company', run_id)
        if item:
            db_session.add(item)
            staged += 1

    return staged


# ---------------------------------------------------------------------------
# Per-entity staging helpers
# ---------------------------------------------------------------------------

def _stage_company(raw: dict, run_id: int, db_session) -> 'ResearchQueueItem | None':
    from app.models import ResearchQueueItem, Company

    company_name = raw.get('company_name', '').strip()
    if not company_name:
        return None

    # Normalise enum fields before storing
    raw_normalised = dict(raw)
    raw_normalised['company_type'] = _normalise_enum(
        raw.get('company_type'), VALID_COMPANY_TYPES, _COMPANY_TYPE_NORM
    )
    roles = raw.get('roles') or []
    raw_normalised['roles'] = [
        r for r in (_normalise_enum(r, VALID_COMPANY_ROLES) for r in roles)
        if r is not None
    ]

    # Match to existing DB record
    existing = _match_company(raw, db_session)

    if existing is None:
        return ResearchQueueItem(
            run_id=run_id,
            entity_type='company',
            entity_db_id=None,
            entity_name=company_name,
            change_type='new',
            proposed_data=json.dumps(raw_normalised),
            current_data=None,
            changed_fields=None,
            source_urls=json.dumps(raw.get('sources') or []),
            status='pending',
        )

    current_snap = _company_snapshot(existing)
    changed = _diff_fields(raw_normalised, current_snap,
                           ['company_name', 'company_type', 'website',
                            'headquarters_country', 'notes'])

    if not changed:
        return None  # nothing new — don't clutter the queue

    change_type = 'conflict' if _any_nonempty(current_snap, changed) else 'update'

    return ResearchQueueItem(
        run_id=run_id,
        entity_type='company',
        entity_db_id=existing.company_id,
        entity_name=company_name,
        change_type=change_type,
        proposed_data=json.dumps(raw_normalised),
        current_data=json.dumps(current_snap),
        changed_fields=json.dumps(changed),
        source_urls=json.dumps(raw.get('sources') or []),
        status='pending',
    )


def _stage_project(raw: dict, run_id: int, db_session) -> 'ResearchQueueItem | None':
    from app.models import ResearchQueueItem, Project

    project_name = raw.get('project_name', '').strip()
    if not project_name:
        return None

    raw_normalised = dict(raw)
    raw_normalised['project_status'] = _normalise_enum(
        raw.get('project_status'), VALID_PROJECT_STATUS, _PROJECT_STATUS_NORM
    )
    raw_normalised['licensing_approach'] = _normalise_enum(
        raw.get('licensing_approach'), VALID_LICENSING_APPROACH
    )
    raw_normalised['project_health'] = _normalise_enum(
        raw.get('project_health'), VALID_PROJECT_HEALTH, _PROJECT_HEALTH_NORM
    )
    raw_normalised['firm_involvement'] = _normalise_enum(
        raw.get('firm_involvement'), VALID_FIRM_INVOLVEMENT
    )

    existing = _match_project(raw, db_session)

    if existing is None:
        return ResearchQueueItem(
            run_id=run_id,
            entity_type='project',
            entity_db_id=None,
            entity_name=project_name,
            change_type='new',
            proposed_data=json.dumps(raw_normalised),
            current_data=None,
            changed_fields=None,
            source_urls=json.dumps(raw.get('sources') or []),
            status='pending',
        )

    current_snap = _project_snapshot(existing)
    changed = _diff_fields(raw_normalised, current_snap,
                           ['project_name', 'location', 'project_status',
                            'licensing_approach', 'configuration', 'project_schedule',
                            'target_cod', 'cod', 'project_health', 'firm_involvement',
                            'notes'])

    if not changed:
        return None

    change_type = 'conflict' if _any_nonempty(current_snap, changed) else 'update'

    return ResearchQueueItem(
        run_id=run_id,
        entity_type='project',
        entity_db_id=existing.project_id,
        entity_name=project_name,
        change_type=change_type,
        proposed_data=json.dumps(raw_normalised),
        current_data=json.dumps(current_snap),
        changed_fields=json.dumps(changed),
        source_urls=json.dumps(raw.get('sources') or []),
        status='pending',
    )


def _stage_relationship(raw: dict, rel_type: str, run_id: int) -> 'ResearchQueueItem | None':
    from app.models import ResearchQueueItem

    key = raw.get('relationship_key', '')
    if not key:
        return None

    if rel_type == 'project_company':
        name = f"{raw.get('project_slug', '?')} ← {raw.get('role', '?')} → {raw.get('company_slug', '?')}"
    else:
        name = f"{raw.get('company_a_slug', '?')} ↔ {raw.get('company_b_slug', '?')}"

    return ResearchQueueItem(
        run_id=run_id,
        entity_type=f'relationship:{rel_type}',
        entity_db_id=None,
        entity_name=name,
        change_type='new',
        proposed_data=json.dumps(raw),
        current_data=None,
        changed_fields=None,
        source_urls=json.dumps(raw.get('sources') or []),
        status='pending',
    )


# ---------------------------------------------------------------------------
# Apply accepted item to main DB
# ---------------------------------------------------------------------------

def apply_queue_item(item, db_session, applied_by_user_id: int, fields_to_apply=None):
    """
    Write an accepted ResearchQueueItem into the main database.
    For 'new' items, creates a new record using all proposed fields.
    For 'update'/'conflict' items, fields_to_apply is a {field: value} dict
    containing only the fields the user selected (with optional custom values).
    If fields_to_apply is None for an update/conflict, all changed fields are written.
    Relationship items are stored for audit but not auto-applied.
    """
    from app.models import Company, Project

    proposed = item.get_proposed()

    if item.entity_type == 'company':
        if item.entity_db_id:
            record = db_session.query(Company).get(item.entity_db_id)
            if record:
                if fields_to_apply is not None:
                    _apply_specific_fields(
                        record, fields_to_apply,
                        {'company_name', 'company_type', 'website', 'headquarters_country', 'notes'},
                        applied_by_user_id,
                    )
                else:
                    _apply_company_fields(record, proposed, applied_by_user_id)
        else:
            record = Company(
                company_name=proposed.get('company_name', 'Unknown'),
                company_type=proposed.get('company_type'),
                website=proposed.get('website'),
                headquarters_country=proposed.get('headquarters_country'),
                notes=proposed.get('notes'),
                is_internal=False,
                created_by=applied_by_user_id,
            )
            db_session.add(record)

    elif item.entity_type == 'project':
        if item.entity_db_id:
            record = db_session.query(Project).get(item.entity_db_id)
            if record:
                if fields_to_apply is not None:
                    _apply_specific_fields(
                        record, fields_to_apply,
                        {'project_name', 'location', 'project_status', 'licensing_approach',
                         'configuration', 'project_schedule', 'project_health',
                         'firm_involvement', 'notes'},
                        applied_by_user_id,
                    )
                else:
                    _apply_project_fields(record, proposed, applied_by_user_id)
        else:
            record = Project(
                project_name=proposed.get('project_name', 'Unknown'),
                location=proposed.get('location'),
                project_status=proposed.get('project_status'),
                licensing_approach=proposed.get('licensing_approach'),
                configuration=proposed.get('configuration'),
                project_schedule=proposed.get('project_schedule'),
                project_health=proposed.get('project_health'),
                firm_involvement=proposed.get('firm_involvement'),
                notes=proposed.get('notes'),
                created_by=applied_by_user_id,
            )
            db_session.add(record)

    # Relationship items: no auto-apply in v1 — mark as accepted for audit trail only


# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------

def _normalise_name(s: str) -> str:
    """Aggressive normalisation for entity name matching and name-field diffing.

    Strips parenthetical aliases, common legal suffixes, and punctuation, then
    lowercases and collapses whitespace.  Used for both entity lookup and
    determining whether a name field has genuinely changed.

    Examples that become equal:
      "Kairos Power LLC"        == "Kairos Power, LLC"
      "Meta Platforms, Inc."    == "Meta Platforms (Facebook)"
      "NuScale Power, LLC"      == "NuScale Power LLC"
    """
    import re
    s = s.strip().lower()
    s = re.sub(r'\([^)]*\)', ' ', s)   # remove parenthetical aliases
    s = re.sub(r'[,.\[\]\-–—]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # Strip trailing legal-entity suffixes so "Corp" vs "Inc" doesn't matter
    s = re.sub(
        r'\b(inc|llc|llp|ltd|corp|corporation|co|company|group|holdings|plc|sa|ag|gmbh)\s*$',
        '', s,
    ).strip()
    return s


def _acronym_match(name_a: str, name_b: str) -> bool:
    """True if name_a has a parenthetical acronym whose initials spell out name_b's words.

    Example: "Amazon (AWS)" matches "Amazon Web Services, Inc."
      - acronym "AWS" → initials of ["amazon","web","services"] = "aws" ✓
    """
    import re
    m = re.search(r'\(([A-Z]{2,8})\)', name_a)
    if not m:
        return False
    acronym = m.group(1).lower()
    _skip = {'inc', 'llc', 'llp', 'ltd', 'corp', 'corporation', 'co',
             'the', 'and', 'of', 'for', 'a', 'an'}
    words = re.sub(r'[,.()\[\]\-–—]', ' ', name_b).lower().split()
    significant = [w for w in words if w not in _skip]
    if not significant:
        return False
    return ''.join(w[0] for w in significant) == acronym


def _names_equivalent(a: str, b: str) -> bool:
    """True if two entity names should be treated as the same for conflict detection."""
    if not a and not b:
        return True
    if not a or not b:
        return False
    return (
        _normalise_name(a) == _normalise_name(b)
        or _acronym_match(a, b)
        or _acronym_match(b, a)
    )


def _match_company(raw: dict, db_session):
    from app.models import Company
    db_id = raw.get('db_id')
    if db_id and isinstance(db_id, int):
        return db_session.query(Company).get(db_id)
    name_raw = raw.get('company_name', '').strip()
    companies = db_session.query(Company).filter(Company.is_internal == False).all()
    # Pass 1: exact case-insensitive match
    for c in companies:
        if c.company_name.strip().lower() == name_raw.lower():
            return c
    # Pass 2: normalised match (strips punctuation/legal suffixes)
    norm = _normalise_name(name_raw)
    for c in companies:
        if _normalise_name(c.company_name) == norm:
            return c
    # Pass 3: acronym match e.g. "Amazon (AWS)" == "Amazon Web Services, Inc."
    for c in companies:
        if _acronym_match(name_raw, c.company_name) or _acronym_match(c.company_name, name_raw):
            return c
    return None


def _match_project(raw: dict, db_session):
    from app.models import Project
    db_id = raw.get('db_id')
    if db_id and isinstance(db_id, int):
        return db_session.query(Project).get(db_id)
    name_raw = raw.get('project_name', '').strip()
    projects = db_session.query(Project).all()
    # Pass 1: exact case-insensitive match
    for p in projects:
        if p.project_name.strip().lower() == name_raw.lower():
            return p
    # Pass 2: normalised match
    norm = _normalise_name(name_raw)
    for p in projects:
        if _normalise_name(p.project_name) == norm:
            return p
    # Pass 3: acronym match
    for p in projects:
        if _acronym_match(name_raw, p.project_name) or _acronym_match(p.project_name, name_raw):
            return p
    return None


# ---------------------------------------------------------------------------
# Snapshot / diff helpers
# ---------------------------------------------------------------------------

def _company_snapshot(c) -> dict:
    return {
        'company_name': c.company_name,
        'company_type': c.company_type,
        'website': c.website,
        'headquarters_country': c.headquarters_country,
        'notes': c.notes,
    }


def _project_snapshot(p) -> dict:
    from app.services.research_export import _date_str
    return {
        'project_name': p.project_name,
        'location': p.location,
        'project_status': p.project_status,
        'licensing_approach': p.licensing_approach,
        'configuration': p.configuration,
        'project_schedule': p.project_schedule,
        'target_cod': _date_str(p.target_cod),
        'cod': _date_str(p.cod),
        'project_health': p.project_health,
        'firm_involvement': p.firm_involvement,
        'notes': p.notes,
    }


_NAME_FIELDS = {'company_name', 'project_name'}


def _diff_fields(proposed: dict, current: dict, fields: list) -> list:
    """Return list of field names where proposed differs from current."""
    changed = []
    for f in fields:
        p_val = proposed.get(f)
        c_val = current.get(f)
        if f in _NAME_FIELDS:
            # Use full equivalence check: normalised names + acronym matching
            if not _names_equivalent(p_val or '', c_val or ''):
                changed.append(f)
        elif _normalise_val(p_val) != _normalise_val(c_val):
            changed.append(f)
    return changed


def _normalise_val(v):
    if v is None or v == '':
        return None
    if isinstance(v, str):
        return v.strip()
    return v


def _any_nonempty(current: dict, changed_fields: list) -> bool:
    """True if any of the changed fields has a non-null current value (potential conflict)."""
    return any(current.get(f) not in (None, '') for f in changed_fields)


def _apply_specific_fields(record, fields_to_apply: dict, allowed: set, user_id: int):
    for field, value in fields_to_apply.items():
        if field in allowed:
            setattr(record, field, value)
    record.modified_by = user_id


def _apply_company_fields(record, proposed: dict, user_id: int):
    for field in ['company_name', 'company_type', 'website', 'headquarters_country', 'notes']:
        val = proposed.get(field)
        if val is not None:
            setattr(record, field, val)
    record.modified_by = user_id


def _apply_project_fields(record, proposed: dict, user_id: int):
    for field in ['project_name', 'location', 'project_status', 'licensing_approach',
                  'configuration', 'project_schedule', 'project_health',
                  'firm_involvement', 'notes']:
        val = proposed.get(field)
        if val is not None:
            setattr(record, field, val)
    record.modified_by = user_id
