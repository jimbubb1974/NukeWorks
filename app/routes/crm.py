"""
CRM routes (contact tracking, roundtable history)
NED Team only - for roundtable meetings and client management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func, or_, and_
from datetime import datetime, timedelta, date

from app.models import (
    Client,
    RoundtableHistory,
    ContactLog,
    Personnel
)
from app.forms.roundtable import RoundtableHistoryForm
from app import db_session
from app.utils.permissions import ned_team_required

bp = Blueprint('crm', __name__, url_prefix='/crm')


@bp.route('/dashboard')
@login_required
@ned_team_required
def dashboard():
    """
    CRM dashboard (NED Team only)

    Features:
    - Filter by priority, status, MPR POC
    - Quick stats
    - Recent roundtable entries
    """
    # Get filter parameters
    priority_filter = request.args.get('priority', '')
    status_filter = request.args.get('status', '')
    poc_filter = request.args.get('poc', '')

    # Base query
    query = db_session.query(Client)

    # Apply filters
    if priority_filter:
        query = query.filter(Client.client_priority == priority_filter)
    if status_filter:
        query = query.filter(Client.client_status == status_filter)
    if poc_filter:
        query = query.filter(
            or_(
                Client.mpr_primary_poc == int(poc_filter),
                Client.mpr_secondary_poc == int(poc_filter)
            )
        )

    # Get all clients
    all_clients = query.order_by(Client.client_name).all()

    # Get MPR personnel for filter dropdown
    mpr_personnel = db_session.query(Personnel).filter(
        Personnel.personnel_type == 'Internal',
        Personnel.is_active == True
    ).order_by(Personnel.full_name).all()

    # Get recent roundtable entries (last 10)
    recent_roundtables = db_session.query(RoundtableHistory).filter(
        RoundtableHistory.entity_type == 'Client'
    ).order_by(RoundtableHistory.meeting_date.desc()).limit(10).all()

    # Get client objects for roundtable entries
    roundtable_clients = {}
    for rt in recent_roundtables:
        client = db_session.get(Client, rt.entity_id)
        if client:
            roundtable_clients[rt.entity_id] = client

    # Calculate stats
    stats = {
        'total_clients': len(all_clients),
        'high_priority': len([c for c in all_clients if c.client_priority in ['High', 'Strategic']]),
        'active': len([c for c in all_clients if c.client_status == 'Active']),
    }

    return render_template(
        'crm/dashboard.html',
        clients=all_clients,
        mpr_personnel=mpr_personnel,
        recent_roundtables=recent_roundtables,
        roundtable_clients=roundtable_clients,
        stats=stats,
        priority_filter=priority_filter,
        status_filter=status_filter,
        poc_filter=poc_filter
    )


@bp.route('/roundtable')
@login_required
@ned_team_required
def roundtable_meeting():
    """
    Roundtable meeting interface

    Features:
    - List all clients for discussion
    - Show previous roundtable notes
    - Quick add/edit roundtable entries
    """
    # Get all active clients ordered by priority
    clients = db_session.query(Client).filter(
        or_(
            Client.client_status == 'Active',
            Client.client_status == 'Warm',
            Client.client_priority.in_(['High', 'Strategic'])
        )
    ).order_by(
        # Strategic and High priority first
        Client.client_priority.desc(),
        Client.client_name
    ).all()

    # Get latest roundtable entry for each client
    latest_roundtables = {}
    for client in clients:
        latest = db_session.query(RoundtableHistory).filter(
            RoundtableHistory.entity_type == 'Client',
            RoundtableHistory.entity_id == client.client_id
        ).order_by(RoundtableHistory.meeting_date.desc()).first()

        if latest:
            latest_roundtables[client.client_id] = latest

    return render_template(
        'crm/roundtable.html',
        clients=clients,
        latest_roundtables=latest_roundtables,
        today=date.today()
    )


@bp.route('/roundtable/<int:client_id>', methods=['GET', 'POST'])
@login_required
@ned_team_required
def add_roundtable_entry(client_id):
    """
    Add/edit roundtable entry for a client

    Features:
    - Show previous entries
    - Add new structured entry
    - Fields: next_steps, client_near_term_focus, mpr_work_targets, discussion
    """
    from app.models import Client

    client = db_session.get(Client, client_id)
    if not client:
        flash('Client not found', 'error')
        abort(404)

    form = RoundtableHistoryForm()

    if form.validate_on_submit():
        try:
            # Create new roundtable entry
            entry = RoundtableHistory(
                entity_type='Client',
                entity_id=client.client_id,
                meeting_date=form.meeting_date.data,
                next_steps=form.next_steps.data,
                client_near_term_focus=form.client_near_term_focus.data,
                mpr_work_targets=form.mpr_work_targets.data,
                discussion=form.discussion.data,
                created_by=current_user.user_id,
                created_date=date.today()
            )

            db_session.add(entry)
            db_session.commit()

            flash(f'Roundtable entry added for {client.client_name}', 'success')
            return redirect(url_for('crm.roundtable_meeting'))

        except Exception as e:
            db_session.rollback()
            flash(f'Error adding roundtable entry: {str(e)}', 'error')

    # Get previous entries (last 3)
    previous_entries = db_session.query(RoundtableHistory).filter(
        RoundtableHistory.entity_type == 'Client',
        RoundtableHistory.entity_id == client_id
    ).order_by(RoundtableHistory.meeting_date.desc()).limit(3).all()

    # Pre-fill meeting date with today
    if not form.meeting_date.data:
        form.meeting_date.data = date.today()

    return render_template(
        'crm/roundtable_form.html',
        form=form,
        client=client,
        previous_entries=previous_entries
    )


@bp.route('/clients-by-poc/<int:personnel_id>')
@login_required
@ned_team_required
def clients_by_poc(personnel_id):
    """
    Show all clients for a specific MPR POC

    Features:
    - List clients where person is primary or secondary POC
    - Show contact status
    - Link to client details
    """
    person = db_session.get(Personnel, personnel_id)
    if not person:
        flash('Personnel not found', 'error')
        abort(404)

    # Get clients where this person is POC
    clients = db_session.query(Client).filter(
        or_(
            Client.mpr_primary_poc == personnel_id,
            Client.mpr_secondary_poc == personnel_id
        )
    ).order_by(Client.client_name).all()

    # Add role information
    clients_with_role = []
    for client in clients:
        clients_with_role.append({
            'client': client,
            'role': 'Primary' if client.mpr_primary_poc == personnel_id else 'Secondary'
        })

    return render_template(
        'crm/clients_by_poc.html',
        person=person,
        clients=clients_with_role
    )
