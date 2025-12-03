"""
CRM routes (contact tracking, roundtable history)
NED Team only - for roundtable meetings and client management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func, or_, and_, case
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, date

from app.models import (
    RoundtableHistory,
    ContactLog,
    Personnel,
    Company,
    ClientProfile
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
    # Get filter and sort parameters
    priority_filter = request.args.get('priority', '')
    status_filter = request.args.get('status', '')
    poc_filter = request.args.get('poc', '')
    sort_by = request.args.get('sort_by', 'company_name')
    sort_order = request.args.get('sort_order', 'asc')

    # Get MPR clients from Company model (all MPR clients, with or without ClientProfile)
    query = db_session.query(Company).filter(
        Company.is_mpr_client == True
    )

    # Apply filters using ClientProfile (left join to include companies without profiles)
    if status_filter:
        # Join ClientProfile for status filtering (status is not encrypted)
        query = query.outerjoin(ClientProfile)
        query = query.filter(ClientProfile.client_status == status_filter)
    # NOTE: priority_filter is applied in Python after fetching (since client_priority is encrypted)

    if poc_filter:
        # Filter by MPR POC through PersonCompanyAffiliation
        from app.models import PersonCompanyAffiliation
        query = query.join(PersonCompanyAffiliation).filter(
            PersonCompanyAffiliation.personnel_id == int(poc_filter)
        )

    # Always fetch with default company_name ordering from database
    # We'll apply priority sorting in Python if needed (since client_priority is encrypted)
    query = query.order_by(Company.company_name.asc())

    # Get all MPR companies (with optional profiles)
    mpr_companies = query.all()
    
    # DEBUG: Log what data was retrieved
    import time
    print(f"\n{'='*60}")
    print(f"[DB READ] CRM Dashboard - Loading companies")
    print(f"[DB READ] User: {current_user.username}")
    print(f"[DB READ] Timestamp: {time.time()}")
    print(f"[DB READ] Total companies: {len(mpr_companies)}")
    if mpr_companies:
        print(f"[DB READ] Sample company modified dates:")
        for company in mpr_companies[:3]:  # Show first 3
            print(f"[DB READ]   {company.company_name}: modified={company.modified_date}")
            if company.client_profile:
                print(f"[DB READ]     Profile modified={company.client_profile.modified_date}")
    print(f"{'='*60}\n")

    # Apply Python-based sorting for priority or apply priority filter
    if sort_by == 'priority' or priority_filter:
        # Define priority order mapping
        priority_order = {
            'Strategic': 1,
            'High': 2,
            'Medium': 3,
            'Low': 4,
            'Opportunistic': 5,
        }

        if sort_by == 'priority':
            # Sort by priority (encrypted field - must be done in Python)
            def priority_sort_key(company):
                profile = company.client_profile
                if profile and profile.client_priority:
                    return (priority_order.get(profile.client_priority, 6), company.company_name)
                return (6, company.company_name)  # No profile = appears last

            mpr_companies.sort(key=priority_sort_key, reverse=(sort_order == 'desc'))

        # Apply priority filter (in Python since it's encrypted)
        if priority_filter:
            mpr_companies = [c for c in mpr_companies
                           if c.client_profile and c.client_profile.client_priority == priority_filter]

    elif sort_by == 'company_name':
        # Sort by company name (already done in database query)
        if sort_order == 'desc':
            mpr_companies.sort(key=lambda c: c.company_name, reverse=True)

    # DEBUG: Log sorting information
    print(f"\n[CRM Dashboard Debug]")
    print(f"  sort_by={sort_by}, sort_order={sort_order}, priority_filter={priority_filter}")
    print(f"  Total companies returned: {len(mpr_companies)}")
    if mpr_companies:
        print(f"  First 3 companies:")
        for i, company in enumerate(mpr_companies[:3]):
            profile = company.client_profile
            priority = profile.client_priority if profile else "No profile"
            print(f"    {i+1}. {company.company_name}: {priority}")
    print()

    # Get detailed data for each company
    companies_with_details = []
    for company in mpr_companies:
        # Get external personnel for this company
        from app.models import ExternalPersonnel, PersonnelRelationship, InternalPersonnel
        external_personnel = db_session.query(ExternalPersonnel).filter_by(
            company_id=company.company_id
        ).order_by(ExternalPersonnel.full_name).all()
        
        # Get MPR connections for each external personnel
        personnel_with_connections = []
        for person in external_personnel:
            relationships = db_session.query(PersonnelRelationship).filter_by(
                external_personnel_id=person.personnel_id
            ).options(joinedload(PersonnelRelationship.internal_personnel)).all()
            
            mpr_connections = []
            for rel in relationships:
                mpr_connections.append({
                    'personnel': rel.internal_personnel,
                    'relationship_type': rel.relationship_type,
                    'is_primary': rel.relationship_type == 'Primary Contact' if rel.relationship_type else False
                })
            
            personnel_with_connections.append({
                'person': person,
                'mpr_connections': mpr_connections
            })
        
        # Get recent roundtable entries for this company
        recent_roundtables = db_session.query(RoundtableHistory).filter(
            RoundtableHistory.entity_type == 'Company',
            RoundtableHistory.entity_id == company.company_id
        ).order_by(RoundtableHistory.created_timestamp.desc()).limit(3).all()
        
        companies_with_details.append({
            'company': company,
            'personnel_with_connections': personnel_with_connections,
            'recent_roundtables': recent_roundtables
        })

    # Get MPR personnel for filter dropdown
    mpr_personnel = db_session.query(Personnel).filter(
        Personnel.personnel_type == 'Internal',
        Personnel.is_active == True
    ).order_by(Personnel.full_name).all()

    # Get recent roundtable entries (last 10) - now for Company entities
    recent_roundtables = db_session.query(RoundtableHistory).filter(
        RoundtableHistory.entity_type == 'Company'
    ).order_by(RoundtableHistory.created_timestamp.desc()).limit(10).all()

    # Get company objects for roundtable entries
    roundtable_companies = {}
    for rt in recent_roundtables:
        company = db_session.get(Company, rt.entity_id)
        if company:
            roundtable_companies[rt.entity_id] = company

    # Calculate stats using ClientProfile data
    all_profiles = db_session.query(ClientProfile).join(Company).filter(
        Company.is_mpr_client == True
    ).all()
    
    stats = {
        'total_clients': len(mpr_companies),
        'mpr_companies': len(mpr_companies),
        'high_priority': len([p for p in all_profiles if p.client_priority in ['High', 'Strategic']]),
        'active': len([p for p in all_profiles if p.client_status == 'Active']),
    }

    return render_template(
        'crm/dashboard.html',
        mpr_companies=mpr_companies,
        companies_with_details=companies_with_details,
        mpr_personnel=mpr_personnel,
        recent_roundtables=recent_roundtables,
        roundtable_companies=roundtable_companies,
        stats=stats,
        priority_filter=priority_filter,
        status_filter=status_filter,
        poc_filter=poc_filter,
        sort_by=sort_by,
        sort_order=sort_order
    )


@bp.route('/roundtable')
@login_required
@ned_team_required
def roundtable_meeting():
    """
    Roundtable meeting interface

    Features:
    - List all MPR clients for discussion
    - Show previous roundtable notes
    - Quick add/edit roundtable entries
    """
    # Get all MPR clients ordered by priority
    companies = db_session.query(Company).filter(
        Company.is_mpr_client == True
    ).outerjoin(ClientProfile).order_by(
        # Custom priority order: Strategic > High > Medium > Low > Opportunistic
        case(
            (ClientProfile.client_priority == 'Strategic', 1),
            (ClientProfile.client_priority == 'High', 2),
            (ClientProfile.client_priority == 'Medium', 3),
            (ClientProfile.client_priority == 'Low', 4),
            (ClientProfile.client_priority == 'Opportunistic', 5),
            else_=6
        ).asc(),
        Company.company_name
    ).all()

    # Get latest roundtable entry for each company
    latest_roundtables = {}
    for company in companies:
        latest = db_session.query(RoundtableHistory).filter(
            RoundtableHistory.entity_type == 'Company',
            RoundtableHistory.entity_id == company.company_id
        ).order_by(RoundtableHistory.created_timestamp.desc()).first()

        if latest:
            latest_roundtables[company.company_id] = latest

    return render_template(
        'crm/roundtable.html',
        companies=companies,
        latest_roundtables=latest_roundtables,
        today=date.today()
    )


@bp.route('/roundtable/<int:company_id>', methods=['GET', 'POST'])
@login_required
@ned_team_required
def add_roundtable_entry(company_id):
    """
    Add/edit roundtable entry for a company

    Features:
    - Show previous entries
    - Add new structured entry
    - Fields: next_steps, client_near_term_focus, mpr_work_targets, discussion
    """
    company = db_session.get(Company, company_id)
    if not company:
        flash('Company not found', 'error')
        abort(404)

    form = RoundtableHistoryForm()

    if form.validate_on_submit():
        try:
            # Create new roundtable entry (timestamp automatically set)
            entry = RoundtableHistory(
                entity_type='Company',
                entity_id=company.company_id,
                next_steps=form.next_steps.data,
                client_near_term_focus=form.client_near_term_focus.data,
                mpr_work_targets=form.mpr_work_targets.data,
                discussion=form.discussion.data,
                created_by=current_user.user_id
            )

            db_session.add(entry)
            db_session.commit()

            flash(f'Roundtable entry saved successfully', 'success')
            return redirect(url_for('crm.add_roundtable_entry', company_id=company.company_id))

        except Exception as e:
            db_session.rollback()
            flash(f'Error adding roundtable entry: {str(e)}', 'error')

    # Get previous entries (last 3)
    # Order by created_timestamp DESC to get the most recently created entries
    previous_entries = db_session.query(RoundtableHistory).filter(
        RoundtableHistory.entity_type == 'Company',
        RoundtableHistory.entity_id == company_id
    ).order_by(
        RoundtableHistory.created_timestamp.desc()
    ).limit(3).all()

    # Get the most recent entry for pre-population
    most_recent_entry = previous_entries[0] if previous_entries else None

    # Pre-fill form with most recent entry data (if exists and form not submitted)
    if not form.is_submitted() and most_recent_entry:
        form.next_steps.data = most_recent_entry.next_steps
        form.client_near_term_focus.data = most_recent_entry.client_near_term_focus
        form.mpr_work_targets.data = most_recent_entry.mpr_work_targets
        form.discussion.data = most_recent_entry.discussion

    # Get external personnel for this company with their MPR relationships
    from app.models import ExternalPersonnel, PersonnelRelationship, InternalPersonnel
    
    try:
        external_personnel = db_session.query(ExternalPersonnel).filter_by(
            company_id=company.company_id,
            is_active=True
        ).order_by(ExternalPersonnel.full_name).all()
        
        # Build a dict mapping external personnel to their MPR connections
        personnel_mpr_map = {}
        for person in external_personnel:
            relationships = db_session.query(PersonnelRelationship).filter_by(
                external_personnel_id=person.personnel_id
            ).join(InternalPersonnel).all()
            
            mpr_connections = [rel.internal_personnel.full_name for rel in relationships if rel.internal_personnel]
            personnel_mpr_map[person.personnel_id] = mpr_connections
    except Exception as e:
        # Fallback in case of error
        print(f"Error loading personnel relationships: {e}")
        external_personnel = []
        personnel_mpr_map = {}

    return render_template(
        'crm/roundtable_form.html',
        form=form,
        company=company,
        previous_entries=previous_entries,
        most_recent_entry=most_recent_entry,
        external_personnel=external_personnel,
        personnel_mpr_map=personnel_mpr_map
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
