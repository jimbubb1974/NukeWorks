"""
Dashboard routes
"""
import os
from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import (
    Company,
    CompanyRoleAssignment,
    ContactLog,
    ConfidentialFieldFlag,
    ExternalPersonnel,
    Project,
)
from app import db_session
from app.utils import db_helpers

bp = Blueprint('dashboard', __name__, url_prefix='/')


def _latest_timestamp(*timestamps):
    values = [value for value in timestamps if value is not None]
    return max(values) if values else None


@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Main dashboard."""
    active_db_path = session.get('selected_db_path')
    active_db_name = None
    if active_db_path:
        active_db_name = db_helpers.get_db_display_name(active_db_path) or os.path.basename(active_db_path)

    company_count = db_session.query(func.count(Company.company_id)).scalar() or 0
    project_count = db_session.query(func.count(Project.project_id)).scalar() or 0
    external_contact_count = (
        db_session.query(func.count(ExternalPersonnel.personnel_id))
        .filter(ExternalPersonnel.is_active == True)  # noqa: E712
        .scalar()
        or 0
    )
    mpr_client_count = (
        db_session.query(func.count(Company.company_id))
        .filter(Company.is_mpr_client == True)  # noqa: E712
        .scalar()
        or 0
    )

    project_relationship_count = (
        db_session.query(func.count(CompanyRoleAssignment.assignment_id))
        .filter(CompanyRoleAssignment.context_type == 'Project')
        .scalar()
        or 0
    )
    linked_project_ids = (
        db_session.query(CompanyRoleAssignment.context_id)
        .filter(CompanyRoleAssignment.context_type == 'Project')
        .distinct()
        .subquery()
    )
    projects_without_connections = (
        db_session.query(func.count(Project.project_id))
        .filter(~Project.project_id.in_(linked_project_ids))
        .scalar()
        or 0
    )

    confidential_relationship_count = (
        db_session.query(func.count(CompanyRoleAssignment.assignment_id))
        .filter(
            CompanyRoleAssignment.context_type == 'Project',
            CompanyRoleAssignment.is_confidential == True,  # noqa: E712
        )
        .scalar()
        or 0
    )
    confidential_contact_log_count = (
        db_session.query(func.count(ContactLog.contact_id))
        .filter(ContactLog.is_confidential == True)  # noqa: E712
        .scalar()
        or 0
    )
    confidential_flagged_field_count = (
        db_session.query(func.count(ConfidentialFieldFlag.flag_id))
        .filter(ConfidentialFieldFlag.is_confidential == True)  # noqa: E712
        .scalar()
        or 0
    )

    last_edit_timestamp = _latest_timestamp(
        db_session.query(func.max(Company.modified_date)).scalar(),
        db_session.query(func.max(Project.modified_date)).scalar(),
        db_session.query(func.max(ExternalPersonnel.modified_date)).scalar(),
        db_session.query(func.max(CompanyRoleAssignment.modified_date)).scalar(),
        db_session.query(func.max(ContactLog.modified_date)).scalar(),
    )

    dashboard_metrics = {
        'company_count': company_count,
        'project_count': project_count,
        'external_contact_count': external_contact_count,
        'mpr_client_count': mpr_client_count,
        'project_relationship_count': project_relationship_count,
        'projects_without_connections': projects_without_connections,
        'confidential_relationship_count': confidential_relationship_count,
        'confidential_contact_log_count': confidential_contact_log_count,
        'confidential_flagged_field_count': confidential_flagged_field_count,
        'active_db_path': active_db_path,
        'active_db_name': active_db_name,
        'environment_name': os.environ.get('FLASK_ENV', 'development'),
        'last_edit_timestamp': last_edit_timestamp,
    }

    return render_template('dashboard.html', metrics=dashboard_metrics)
