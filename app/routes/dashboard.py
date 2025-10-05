"""
Dashboard routes
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import TechnologyVendor, Project, OwnerDeveloper
from app import db_session

bp = Blueprint('dashboard', __name__, url_prefix='/')


@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Main dashboard"""
    # Get summary statistics
    vendor_count = db_session.query(TechnologyVendor).count()
    project_count = db_session.query(Project).count()
    owner_count = db_session.query(OwnerDeveloper).count()

    # Get recent projects
    recent_projects = db_session.query(Project).order_by(
        Project.modified_date.desc()
    ).limit(10).all()

    return render_template('dashboard.html',
                         vendor_count=vendor_count,
                         project_count=project_count,
                         owner_count=owner_count,
                         recent_projects=recent_projects)
