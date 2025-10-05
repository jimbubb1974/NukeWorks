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
    """Main dashboard - simplified placeholder"""
    return render_template('dashboard.html')
