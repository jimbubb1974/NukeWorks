"""
Dashboard routes
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Company, CompanyRole, CompanyRoleAssignment, Project
from app import db_session

bp = Blueprint('dashboard', __name__, url_prefix='/')


@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Main dashboard"""
    # Get summary statistics from unified schema

    # Count companies by role
    vendor_role = db_session.query(CompanyRole).filter(CompanyRole.role_code == 'vendor').first()
    owner_role = db_session.query(CompanyRole).filter(CompanyRole.role_code == 'developer').first()

    vendor_count = 0
    owner_count = 0

    if vendor_role:
        vendor_count = db_session.query(func.count(func.distinct(CompanyRoleAssignment.company_id))).filter(
            CompanyRoleAssignment.role_id == vendor_role.role_id
        ).scalar() or 0

    if owner_role:
        owner_count = db_session.query(func.count(func.distinct(CompanyRoleAssignment.company_id))).filter(
            CompanyRoleAssignment.role_id == owner_role.role_id
        ).scalar() or 0

    project_count = db_session.query(Project).count()

    # Get recent projects
    recent_projects = db_session.query(Project).order_by(
        Project.modified_date.desc()
    ).limit(10).all()

    return render_template('dashboard.html',
                         vendor_count=vendor_count,
                         project_count=project_count,
                         owner_count=owner_count,
                         recent_projects=recent_projects)
