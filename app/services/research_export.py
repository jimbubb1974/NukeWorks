"""
Research export service.

Builds non-confidential DB snapshots for delivery to an AI research agent.
The exported JSON is designed to be safe to send to external services:
  - No encrypted fields (financials)
  - No CRM / NED-team internal assessments
  - No is_mpr_client or is_internal flags
  - No confidential relationships
"""
import json
import re
from datetime import datetime, date
from pathlib import Path


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def derive_slug(name: str) -> str:
    """Convert an entity name to a stable kebab-case slug."""
    s = name.lower()
    s = re.sub(r'[^a-z0-9\s-]', '', s)   # strip non-alphanumeric (keep spaces/hyphens)
    s = re.sub(r'[\s]+', '-', s.strip())   # spaces → hyphens
    s = re.sub(r'-{2,}', '-', s)           # collapse repeated hyphens
    return s


# ---------------------------------------------------------------------------
# Stats (used to show preview before export)
# ---------------------------------------------------------------------------

def get_export_stats(db_session, company_ids=None):
    """
    Return counts of exportable entities for the given scope.

    Args:
        db_session: SQLAlchemy session
        company_ids: list of company_id ints to restrict scope, or None for all

    Returns:
        dict with keys: companies, projects, relationships
    """
    from app.models import Company, Project, CompanyRoleAssignment

    q = db_session.query(Company).filter(Company.is_internal == False)
    if company_ids:
        q = q.filter(Company.company_id.in_(company_ids))
    company_count = q.count()

    # Projects linked to those companies via non-confidential role assignments
    cra_q = (
        db_session.query(CompanyRoleAssignment)
        .filter(
            CompanyRoleAssignment.context_type == 'Project',
            CompanyRoleAssignment.is_confidential == False,
        )
    )
    if company_ids:
        cra_q = cra_q.filter(CompanyRoleAssignment.company_id.in_(company_ids))

    linked_project_ids = {r.context_id for r in cra_q.all() if r.context_id}
    project_count = len(linked_project_ids)
    relationship_count = cra_q.count()

    return {
        'companies': company_count,
        'projects': project_count,
        'relationships': relationship_count,
    }


def recommended_chunk_count(stats, chunk_size=20):
    """Return recommended number of chunks given entity counts and chunk size."""
    n = stats['companies']
    if n == 0:
        return 1
    import math
    return math.ceil(n / chunk_size)


# ---------------------------------------------------------------------------
# Core export builder
# ---------------------------------------------------------------------------

def build_export_chunks(db_session, company_ids=None, chunk_size=20):
    """
    Build export chunk dicts ready to be serialised to JSON files.

    Args:
        db_session: SQLAlchemy session
        company_ids: list of company_id ints, or None for all external companies
        chunk_size: number of companies per chunk

    Returns:
        list of dicts, each representing one chunk file's content
    """
    from app.models import Company, Project, CompanyRoleAssignment, CompanyRole, ConfidentialFieldFlag

    # Load the research prompt text to embed in each chunk
    prompt_path = Path(__file__).parent.parent.parent / 'docs' / 'research_prompt.txt'
    try:
        instructions = prompt_path.read_text(encoding='utf-8')
    except Exception:
        instructions = (
            "Research the entities in existing_data and return updated information "
            "as a JSON object matching the NukeWorks research output spec."
        )

    # Fetch all exportable companies, sorted by name
    q = db_session.query(Company).filter(Company.is_internal == False)
    if company_ids:
        q = q.filter(Company.company_id.in_(company_ids))
    companies = q.order_by(Company.company_name).all()

    if not companies:
        return []

    # Build a lookup of confidentially-flagged notes fields per company
    conf_company_notes = _confidential_notes_set(db_session, 'companies', [c.company_id for c in companies])

    # Build role code lookup: role_id → role_code
    role_lookup = {r.role_id: r.role_code for r in db_session.query(CompanyRole).all()}

    # Load all non-confidential project-context role assignments for these companies
    company_id_set = {c.company_id for c in companies}
    all_assignments = (
        db_session.query(CompanyRoleAssignment)
        .filter(
            CompanyRoleAssignment.company_id.in_(company_id_set),
            CompanyRoleAssignment.is_confidential == False,
        )
        .all()
    )

    # Separate general (non-project) roles from project relationships
    general_roles_by_company = {}   # company_id → set of role_codes
    project_assignments = []        # list of assignments with context_type='Project'

    for a in all_assignments:
        role_code = role_lookup.get(a.role_id, '')
        if a.context_type == 'Project' and a.context_id:
            project_assignments.append(a)
        else:
            general_roles_by_company.setdefault(a.company_id, set()).add(role_code)

    # Load projects referenced by project assignments
    project_ids = {a.context_id for a in project_assignments}
    projects_by_id = {}
    if project_ids:
        conf_project_notes = _confidential_notes_set(db_session, 'projects', list(project_ids))
        for p in db_session.query(Project).filter(Project.project_id.in_(project_ids)).all():
            projects_by_id[p.project_id] = (p, p.project_id in conf_project_notes)
    else:
        conf_project_notes = set()

    # Index project assignments by company_id
    proj_assignments_by_company = {}
    for a in project_assignments:
        proj_assignments_by_company.setdefault(a.company_id, []).append(a)

    # Divide companies into chunks
    chunks = []
    total_chunks = max(1, -(-len(companies) // chunk_size))  # ceiling division
    exported_at = datetime.utcnow().isoformat() + 'Z'

    for chunk_idx in range(total_chunks):
        batch = companies[chunk_idx * chunk_size:(chunk_idx + 1) * chunk_size]
        batch_company_ids = {c.company_id for c in batch}

        # Serialise companies in this batch
        export_companies = []
        for c in batch:
            roles = sorted(general_roles_by_company.get(c.company_id, set()))
            notes = c.notes if c.company_id not in conf_company_notes else None
            export_companies.append({
                'db_id': c.company_id,
                'slug': derive_slug(c.company_name),
                'company_name': c.company_name,
                'company_type': c.company_type,
                'website': c.website,
                'headquarters_country': c.headquarters_country,
                'roles': roles,
                'notes': notes,
            })

        # Collect projects and relationships for this batch
        batch_assignments = [
            a for a in project_assignments
            if a.company_id in batch_company_ids
        ]
        batch_project_ids = {a.context_id for a in batch_assignments}

        export_projects = []
        seen_project_ids = set()
        for pid in batch_project_ids:
            if pid in projects_by_id and pid not in seen_project_ids:
                p, notes_confidential = projects_by_id[pid]
                seen_project_ids.add(pid)
                export_projects.append(_serialise_project(p, notes_confidential))

        export_relationships = []
        for a in batch_assignments:
            if a.context_id not in projects_by_id:
                continue
            p, _ = projects_by_id[a.context_id]
            company = next((c for c in batch if c.company_id == a.company_id), None)
            if not company:
                continue
            role_code = role_lookup.get(a.role_id, 'unknown')
            p_slug = derive_slug(p.project_name)
            c_slug = derive_slug(company.company_name)
            export_relationships.append({
                'relationship_type': 'project_company',
                'relationship_key': f'{p_slug}-{role_code}-{c_slug}',
                'project_db_id': p.project_id,
                'project_slug': p_slug,
                'company_db_id': company.company_id,
                'company_slug': c_slug,
                'role': role_code,
            })

        chunks.append({
            'metadata': {
                'exported_at': exported_at,
                'chunk': chunk_idx + 1,
                'total_chunks': total_chunks,
                'scope': 'selected' if company_ids else 'all',
                'chunk_company_count': len(batch),
            },
            'instructions': instructions,
            'existing_data': {
                'companies': export_companies,
                'projects': export_projects,
                'relationships': export_relationships,
            },
        })

    return chunks


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _serialise_project(p, notes_confidential: bool) -> dict:
    """Serialise a Project to export dict, stripping confidential fields."""
    return {
        'db_id': p.project_id,
        'slug': derive_slug(p.project_name),
        'project_name': p.project_name,
        'location': p.location,
        'project_status': p.project_status,
        'licensing_approach': p.licensing_approach,
        'configuration': p.configuration,
        'project_schedule': p.project_schedule,
        'target_cod': _date_str(p.target_cod),
        'project_health': p.project_health,
        'notes': p.notes if not notes_confidential else None,
    }


def _date_str(d) -> str | None:
    if d is None:
        return None
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


def _confidential_notes_set(db_session, table_name: str, record_ids: list) -> set:
    """
    Return the set of record_ids where the 'notes' field is flagged confidential.
    """
    if not record_ids:
        return set()
    from app.models import ConfidentialFieldFlag
    flags = (
        db_session.query(ConfidentialFieldFlag)
        .filter(
            ConfidentialFieldFlag.table_name == table_name,
            ConfidentialFieldFlag.field_name == 'notes',
            ConfidentialFieldFlag.record_id.in_(record_ids),
            ConfidentialFieldFlag.is_confidential == True,
        )
        .all()
    )
    return {f.record_id for f in flags}
