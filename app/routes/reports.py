"""Report generation routes"""
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, abort
from flask_login import login_required, current_user

from app import db_session
from app.models import Project
from app.reports import ProjectSummaryReport

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.route('/')
@login_required
def index():
    """Report selection page"""
    projects = db_session.query(Project).order_by(Project.project_name).all()
    return render_template('reports/index.html', projects=projects)


@bp.route('/project-summary/pdf')
@login_required
def project_summary_pdf():
    project_id = request.args.get('project_id', type=int)
    if not project_id:
        flash('Select a project to generate the summary report.', 'warning')
        return redirect(url_for('reports.index'))

    project = db_session.get(Project, project_id)
    if not project:
        abort(404)

    include_confidential = request.args.get('confidential') == '1'
    if include_confidential and not (current_user.is_admin or current_user.has_confidential_access):
        flash('You do not have permission to include confidential data. Generating public report instead.', 'warning')
        include_confidential = False

    report = ProjectSummaryReport(
        project,
        user=current_user,
        include_confidential=include_confidential,
        generated_by=current_user.full_name or current_user.username,
        generated_date=datetime.utcnow()
    )

    pdf_bytes = report.build()
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=project_summary_{project_id}.pdf'
    return response
