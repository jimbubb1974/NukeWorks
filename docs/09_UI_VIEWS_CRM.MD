        <button onclick="showAddMemberModal()" class="btn btn-sm">+ Add Team Member</button>
      </div>
    </div>
  </section>
  
  <!-- Contact Tracking Section (All Users) -->
  <section class="crm-section">
    <h2>Contact Tracking <span class="badge">All Users</span></h2>
    
    <div class="contact-summary">
      <div class="last-contact">
        <h3>Last Contact</h3>
        {% if owner.last_contact_date %}
        <dl class="contact-details">
          <dt>Date:</dt>
          <dd>{{ owner.last_contact_date|format_date }}</dd>
          
          <dt>Type:</dt>
          <dd>{{ owner.last_contact_type }}</dd>
          
          <dt>By:</dt>
          <dd>{{ owner.last_contact_by_person.full_name if owner.last_contact_by_person }}</dd>
          
          <dt>Notes:</dt>
          <dd>{{ owner.last_contact_notes }}</dd>
        </dl>
        {% else %}
        <p class="empty-state">No contact recorded</p>
        {% endif %}
      </div>
      
      <div class="next-contact">
        <h3>Next Planned Contact</h3>
        {% if owner.next_planned_contact_date %}
        <dl class="contact-details">
          <dt>Date:</dt>
          <dd>{{ owner.next_planned_contact_date|format_date }}</dd>
          
          <dt>Type:</dt>
          <dd>{{ owner.next_planned_contact_type }}</dd>
          
          <dt>Assigned to:</dt>
          <dd>{{ owner.next_planned_contact_person.full_name if owner.next_planned_contact_person }}</dd>
        </dl>
        {% else %}
        <p class="empty-state">No contact planned</p>
        {% endif %}
      </div>
    </div>
  </section>
  
  <!-- Internal Assessment Section (NED Team Only) -->
  {% if current_user.is_ned_team or current_user.is_admin %}
  <section class="crm-section ned-team-only">
    <h2>Internal Assessment <span class="badge ned-team">NED Team Only</span></h2>
    
    <form id="assessment-form" onsubmit="saveAssessment(event)">
      <div class="form-row">
        <div class="form-group">
          <label>Client Priority:</label>
          <select name="client_priority">
            <option value="">Select...</option>
            <option value="High" {% if owner.client_priority == 'High' %}selected{% endif %}>High</option>
            <option value="Medium" {% if owner.client_priority == 'Medium' %}selected{% endif %}>Medium</option>
            <option value="Low" {% if owner.client_priority == 'Low' %}selected{% endif %}>Low</option>
            <option value="Strategic" {% if owner.client_priority == 'Strategic' %}selected{% endif %}>Strategic</option>
            <option value="Opportunistic" {% if owner.client_priority == 'Opportunistic' %}selected{% endif %}>Opportunistic</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Client Status:</label>
          <select name="client_status">
            <option value="">Select...</option>
            <option value="Active" {% if owner.client_status == 'Active' %}selected{% endif %}>Active</option>
            <option value="Warm" {% if owner.client_status == 'Warm' %}selected{% endif %}>Warm</option>
            <option value="Cold" {% if owner.client_status == 'Cold' %}selected{% endif %}>Cold</option>
            <option value="Prospective" {% if owner.client_status == 'Prospective' %}selected{% endif %}>Prospective</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Relationship Strength:</label>
          <select name="relationship_strength">
            <option value="">Select...</option>
            <option value="Strong" {% if owner.relationship_strength == 'Strong' %}selected{% endif %}>Strong</option>
            <option value="Good" {% if owner.relationship_strength == 'Good' %}selected{% endif %}>Good</option>
            <option value="Needs Attention" {% if owner.relationship_strength == 'Needs Attention' %}selected{% endif %}>Needs Attention</option>
            <option value="At Risk" {% if owner.relationship_strength == 'At Risk' %}selected{% endif %}>At Risk</option>
            <option value="New" {% if owner.relationship_strength == 'New' %}selected{% endif %}>New</option>
          </select>
        </div>
      </div>
      
      <div class="form-group">
        <label>Relationship Notes:</label>
        <textarea name="relationship_notes" rows="6">{{ owner.relationship_notes }}</textarea>
        <p class="field-help">Internal strategy notes and assessment</p>
      </div>
      
      <button type="submit" class="btn btn-primary">Save Assessment</button>
    </form>
  </section>
  
  <!-- Roundtable History Section (NED Team Only) -->
  <section class="crm-section ned-team-only">
    <h2>Roundtable History <span class="badge ned-team">NED Team Only</span></h2>
    
    {% if roundtable_history %}
      {% for entry in roundtable_history %}
      <div class="roundtable-entry {% if loop.first %}most-recent{% endif %}">
        <div class="entry-header" onclick="toggleEntry(this)">
          <h3>
            {% if loop.first %}▼{% else %}▶{% endif %}
            {{ entry.meeting_date|format_date }} 
            {% if loop.first %}<span class="badge">Most Recent</span>{% endif %}
          </h3>
        </div>
        
        <div class="entry-content" {% if not loop.first %}style="display:none"{% endif %}>
          <div class="discussion">
            <h4>Discussion:</h4>
            <p>{{ entry.discussion }}</p>
          </div>
          
          <div class="action-items">
            <h4>Action Items:</h4>
            <p>{{ entry.action_items }}</p>
          </div>
        </div>
      </div>
      {% endfor %}
    {% else %}
    <p class="empty-state">No roundtable history recorded</p>
    {% endif %}
    
    <a href="/owners/{{ owner.owner_id }}/roundtable/add" class="btn btn-secondary">Add New Roundtable Entry</a>
  </section>
  {% else %}
  <!-- Access Restricted Message for Non-NED Users -->
  <section class="crm-section access-restricted">
    <h2>Internal Assessment <span class="badge">NED Team Only</span></h2>
    <div class="access-restricted-message">
      <span class="icon">🔒</span>
      <p>This section is only visible to NED Team members.</p>
      <p>Contact your administrator for access.</p>
    </div>
  </section>
  
  <section class="crm-section access-restricted">
    <h2>Roundtable History <span class="badge">NED Team Only</span></h2>
    <div class="access-restricted-message">
      <span class="icon">🔒</span>
      <p>This section is only visible to NED Team members.</p>
    </div>
  </section>
  {% endif %}
  
  <!-- Contact History Section (All Users) -->
  <section class="crm-section">
    <div class="section-header">
      <h2>Contact History <span class="badge">All Users</span></h2>
      <div class="section-actions">
        <a href="/contact-log?owner_id={{ owner.owner_id }}" class="btn btn-sm btn-secondary">View All</a>
        <a href="/contact-log/add?owner_id={{ owner.owner_id }}" class="btn btn-sm btn-primary">Add Contact</a>
      </div>
    </div>
    
    <table class="contact-log-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Type</th>
          <th>By</th>
          <th>Summary</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for log in recent_contacts %}
        {% if not log.is_confidential or current_user.has_confidential_access or current_user.is_admin %}
        <tr>
          <td>{{ log.contact_date|format_date }}</td>
          <td>{{ log.contact_type }}</td>
          <td>{{ log.contacted_by_person.full_name }}</td>
          <td>
            {{ log.summary|truncate(80) }}
            {% if log.is_confidential %}<span class="badge confidential">🔒</span>{% endif %}
          </td>
          <td>
            <a href="/contact-log/{{ log.contact_id }}" class="btn-icon" title="View">👁️</a>
            <a href="/contact-log/{{ log.contact_id }}/edit" class="btn-icon" title="Edit">✏️</a>
          </td>
        </tr>
        {% endif %}
        {% endfor %}
        
        {% if hidden_contacts_count > 0 %}
        <tr class="hidden-info">
          <td colspan="5">
            <em>{{ hidden_contacts_count }} confidential contact log entries are hidden from your view</em>
          </td>
        </tr>
        {% endif %}
      </tbody>
    </table>
  </section>
</div>
```

### Backend Implementation

```python
@app.route('/owners/<int:owner_id>')
@login_required
def view_owner(owner_id):
    """View owner details with CRM tab"""
    owner = db.query(Owners_Developers).get_or_404(owner_id)
    
    # Get internal personnel for POC dropdowns
    internal_personnel = db.query(Personnel).filter_by(
        personnel_type='Internal',
        is_active=True
    ).order_by(Personnel.full_name).all()
    
    # Get team members
    team_members = get_team_members(owner_id)
    
    # Get roundtable history (NED Team only)
    roundtable_history = None
    if current_user.is_ned_team or current_user.is_admin:
        roundtable_history = db.query(Roundtable_History).filter_by(
            entity_type='Owner',
            entity_id=owner_id
        ).order_by(Roundtable_History.meeting_date.desc()).limit(3).all()
    
    # Get recent contacts (visible ones)
    recent_contacts = get_visible_contacts(current_user, owner_id, limit=10)
    hidden_contacts_count = count_hidden_contacts(current_user, owner_id)
    
    return render_template('owner_detail.html',
                         owner=owner,
                         internal_personnel=internal_personnel,
                         team_members=team_members,
                         roundtable_history=roundtable_history,
                         recent_contacts=recent_contacts,
                         hidden_contacts_count=hidden_contacts_count)
```

---

## CRM Dashboard

### Purpose
Overview of all client relationships, focusing on items needing attention (NED Team only)

### Layout

```
═══════════════════════════════════════════════════════════
CLIENT RELATIONSHIP DASHBOARD
═══════════════════════════════════════════════════════════

[My Clients] [All Clients] [By Team Member ▼]
Priority: [All ▼]  Status: [All ▼]  Sort: [Last Contact ▼]

🔴 CLIENTS NEEDING ATTENTION (3)
┌─────────────────────────────────────────────────────────┐
│ ClientCo A                            Priority: High     │
│   Primary POC: John Smith │ Team: Sarah L., Jane D.     │
│   Last Contact: 90 days ago ⚠️                           │
│   Relationship: Needs Attention                          │
│   Next Planned: None scheduled                           │
│   Action Items: 2 pending                                │
│   [View Details] [Log Contact] [Update]                 │
├─────────────────────────────────────────────────────────┤
│ ClientCo B                         Priority: Strategic   │
│   Primary POC: Jane Doe │ Team: John S.                 │
│   Last Contact: 45 days ago                              │
│   Relationship: Good                                     │
│   Next Planned: Dec 15 (In-person - Sarah Lee)          │
│   [View Details] [Log Contact] [Update]                 │
└─────────────────────────────────────────────────────────┘

HIGH PRIORITY CLIENTS (8)
┌─────────────────────────────────────────────────────────┐
│ Client      POC        Last      Rel.      Next    Actions│
│                        Contact                            │
├─────────────────────────────────────────────────────────┤
│ ClientCo A  John S.    90d ago   ⚠️        -        2    │
│ ClientCo C  Jane D.    14d ago   💪        Dec 20   1    │
│ ClientCo E  Sarah L.   30d ago   ✓         Jan 10   -    │
│ ClientCo G  John S.    7d ago    💪        -         3    │
└─────────────────────────────────────────────────────────┘

UPCOMING CONTACTS (5)
• Dec 15: ClientCo B - Site visit (Sarah Lee)
• Dec 20: ClientCo C - Proposal review (Jane Doe)
• Jan 10: ClientCo E - Quarterly check-in (John Smith)

FOLLOW-UP ACTIONS (4 pending)
• Dec 10: Follow up with ClientCo A on bid (John S.)
• Dec 12: Send white paper to ClientCo C (Jane D.)
• Dec 18: Review proposal with ClientCo E (Sarah L.)
```

### HTML Template

```html
<div class="crm-dashboard">
  <div class="page-header">
    <h1>Client Relationship Dashboard</h1>
    <span class="badge ned-team">NED Team Only</span>
  </div>
  
  <!-- View Filters -->
  <div class="dashboard-filters">
    <div class="view-tabs">
      <button class="view-tab {% if view == 'my' %}active{% endif %}" 
              onclick="setView('my')">My Clients</button>
      <button class="view-tab {% if view == 'all' %}active{% endif %}" 
              onclick="setView('all')">All Clients</button>
      <select class="view-select" onchange="filterByMember(this.value)">
        <option value="">By Team Member...</option>
        {% for person in team_members %}
        <option value="{{ person.personnel_id }}">{{ person.full_name }}</option>
        {% endfor %}
      </select>
    </div>
    
    <div class="filters">
      <select name="priority" onchange="applyFilters()">
        <option value="">All Priorities</option>
        <option value="High">High</option>
        <option value="Strategic">Strategic</option>
        <option value="Medium">Medium</option>
        <option value="Low">Low</option>
      </select>
      
      <select name="status" onchange="applyFilters()">
        <option value="">All Statuses</option>
        <option value="Active">Active</option>
        <option value="Warm">Warm</option>
        <option value="Cold">Cold</option>
        <option value="Prospective">Prospective</option>
      </select>
      
      <select name="sort" onchange="applyFilters()">
        <option value="last_contact">Sort: Last Contact</option>
        <option value="priority">Sort: Priority</option>
        <option value="name">Sort: Name</option>
        <option value="relationship">Sort: Relationship</option>
      </select>
    </div>
  </div>
  
  <!-- Clients Needing Attention -->
  {% if attention_clients %}
  <section class="dashboard-section alert-section">
    <h2>🔴 Clients Needing Attention ({{ attention_clients|length }})</h2>
    
    {% for client in attention_clients %}
    <div class="client-card attention">
      <div class="card-header">
        <h3>
          <a href="/owners/{{ client.owner_id }}">{{ client.company_name }}</a>
        </h3>
        <span class="badge priority-{{ client.client_priority|lower }}">
          Priority: {{ client.client_priority }}
        </span>
      </div>
      
      <div class="card-body">
        <div class="client-info">
          <strong>Primary POC:</strong> {{ client.primary_poc_person.full_name if client.primary_poc_person }}
          {% if client.team_members %}
          │ <strong>Team:</strong> {{ client.team_members|join(', ', attribute='full_name') }}
          {% endif %}
        </div>
        
        <div class="contact-status">
          <span class="last-contact warning">
            <strong>Last Contact:</strong> {{ client.days_since_contact }} days ago ⚠️
          </span>
        </div>
        
        <div class="relationship-status">
          <strong>Relationship:</strong> 
          <span class="badge rel-{{ client.relationship_strength|lower|replace(' ', '-') }}">
            {{ client.relationship_strength }}
          </span>
        </div>
        
        <div class="next-contact">
          <strong>Next Planned:</strong> 
          {% if client.next_planned_contact_date %}
          {{ client.next_planned_contact_date|format_date }} 
          ({{ client.next_planned_contact_type }} - {{ client.next_planned_contact_person.full_name }})
          {% else %}
          <span class="warning">None scheduled</span>
          {% endif %}
        </div>
        
        {% if client.pending_action_items > 0 %}
        <div class="action-items">
          <strong>Action Items:</strong> {{ client.pending_action_items }} pending
        </div>
        {% endif %}
      </div>
      
      <div class="card-actions">
        <a href="/owners/{{ client.owner_id }}" class="btn btn-sm btn-secondary">View Details</a>
        <a href="/contact-log/add?owner_id={{ client.owner_id }}" class="btn btn-sm btn-primary">Log Contact</a>
        <a href="/owners/{{ client.owner_id }}/crm" class="btn btn-sm btn-secondary">Update</a>
      </div>
    </div>
    {% endfor %}
  </section>
  {% endif %}
  
  <!-- High Priority Clients Table -->
  <section class="dashboard-section">
    <h2>High Priority Clients ({{ high_priority_clients|length }})</h2>
    
    <table class="crm-table">
      <thead>
        <tr>
          <th>Client</th>
          <th>POC</th>
          <th>Last Contact</th>
          <th>Relationship</th>
          <th>Next Contact</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for client in high_priority_clients %}
        <tr class="clickable-row" data-href="/owners/{{ client.owner_id }}">
          <td>
            <a href="/owners/{{ client.owner_id }}">{{ client.company_name }}</a>
          </td>
          <td>{{ client.primary_poc_person.full_name if client.primary_poc_person else '-' }}</td>
          <td>
            {{ client.days_since_contact }}d ago
            {% if client.days_since_contact > 60 %}<span class="warning">⚠️</span>{% endif %}
          </td>
          <td>
            <span class="rel-indicator rel-{{ client.relationship_strength|lower|replace(' ', '-') }}">
              {% if client.relationship_strength == 'Strong' %}💪
              {% elif client.relationship_strength == 'Good' %}✓
              {% elif client.relationship_strength == 'Needs Attention' %}⚠️
              {% elif client.relationship_strength == 'At Risk' %}🔴
              {% else %}○
              {% endif %}
            </span>
          </td>
          <td>
            {% if client.next_planned_contact_date %}
            {{ client.next_planned_contact_date|format_date_short }}
            {% else %}-{% endif %}
          </td>
          <td>
            {% if client.pending_action_items > 0 %}
            {{ client.pending_action_items }}
            {% else %}-{% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </section>
  
  <!-- Upcoming Contacts -->
  <section class="dashboard-section">
    <h2>Upcoming Contacts ({{ upcoming_contacts|length }})</h2>
    
    <ul class="upcoming-list">
      {% for contact in upcoming_contacts %}
      <li>
        <strong>{{ contact.date|format_date }}</strong>: 
        <a href="/owners/{{ contact.owner_id }}">{{ contact.owner_name }}</a> - 
        {{ contact.type }}
        ({{ contact.assigned_to_person.full_name }})
      </li>
      {% endfor %}
    </ul>
    
    {% if not upcoming_contacts %}
    <p class="empty-state">No upcoming contacts scheduled</p>
    {% endif %}
  </section>
  
  <!-- Follow-up Actions -->
  <section class="dashboard-section">
    <h2>Follow-up Actions ({{ followup_actions|length }} pending)</h2>
    
    <ul class="action-list">
      {% for action in followup_actions %}
      <li>
        <input type="checkbox" onchange="markActionComplete({{ action.id }})">
        <strong>{{ action.follow_up_date|format_date }}</strong>: 
        {{ action.summary }}
        ({{ action.assigned_to_person.full_name }})
      </li>
      {% endfor %}
    </ul>
    
    {% if not followup_actions %}
    <p class="empty-state">No pending follow-up actions</p>
    {% endif %}
  </section>
</div>
```

### Backend Implementation

```python
@app.route('/crm')
@login_required
@ned_team_required
def crm_dashboard():
    """CRM Dashboard (NED Team only)"""
    view = request.args.get('view', 'my')  # 'my' or 'all'
    priority_filter = request.args.get('priority', '')
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'last_contact')
    
    # Build query
    query = db.query(Owners_Developers)
    
    # Filter by user's clients if "my" view
    if view == 'my':
        query = query.filter(
            db.or_(
                Owners_Developers.primary_poc == get_current_personnel_id(current_user),
                Owners_Developers.secondary_poc == get_current_personnel_id(current_user)
            )
        )
    
    # Apply filters
    if priority_filter:
        query = query.filter_by(client_priority=priority_filter)
    if status_filter:
        query = query.filter_by(client_status=status_filter)
    
    # Get all clients
    clients = query.all()
    
    # Calculate additional metrics
    for client in clients:
        client.days_since_contact = calculate_days_since(client.last_contact_date)
        client.pending_action_items = count_pending_actions(client.owner_id)
    
    # Identify clients needing attention
    attention_clients = [c for c in clients if c.relationship_strength == 'Needs Attention' 
                        or c.days_since_contact > 60]
    
    # Get high priority clients
    high_priority_clients = [c for c in clients if c.client_priority in ['High', 'Strategic']]
    
    # Sort
    if sort_by == 'last_contact':
        high_priority_clients.sort(key=lambda c: c.days_since_contact, reverse=True)
    elif sort_by == 'priority':
        priority_order = {'Strategic': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        high_priority_clients.sort(key=lambda c: priority_order.get(c.client_priority, 999))
    
    # Get upcoming contacts
    upcoming_contacts = get_upcoming_contacts(clients)
    
    # Get follow-up actions
    followup_actions = get_pending_followup_actions(clients)
    
    # Get team members for filter
    team_members = db.query(Personnel).filter_by(personnel_type='Internal').all()
    
    return render_template('crm_dashboard.html',
                         view=view,
                         attention_clients=attention_clients,
                         high_priority_clients=high_priority_clients,
                         upcoming_contacts=upcoming_contacts,
                         followup_actions=followup_actions,
                         team_members=team_members)
```

---

## Roundtable Meeting View

### Purpose
Conduct monthly client roundtable meetings with structured note-taking

### Layout

```
═══════════════════════════════════════════════════════════
MONTHLY CLIENT ROUNDTABLE - December 2025
[🔒 NED Team Access Only]
═══════════════════════════════════════════════════════════

Quick Filters: [High Priority] [Needs Attention] [Generate Agenda]

CLIENTS TO DISCUSS (8 selected)
───────────────────────────────────────────────────────────

▼ ClientCo A                     Priority: High | POC: John S.
  
  Quick Facts:
  • Relationship: Needs Attention ⚠️
  • 2 Active Projects
  • Last Contact: 90 days ago
  • Team: John S. (primary), Sarah L., Jane D.
  
  Last Roundtable (Nov 2025):
  "Team agreed to increase engagement. Priority project is 
   Project Alpha. Need to strengthen relationship..."
  
  Previous Action Items:
  ✓ Schedule site visit by Dec 20 (Sarah) - Complete
  ⏳ Send white paper (John) - Pending
  
  📝 Today's Discussion (Dec 2025):
  [Text area for meeting notes]
  
  ✅ New Action Items:
  [Text area for action items]
  
  ☐ Mark as Discussed
  
  [View Full Details ▶]

▶ ClientCo C                  Priority: Strategic | POC: Jane D.
  [Collapsed - click to expand]

[Save All Discussions] [Export Summary] [Complete Meeting]
```

### HTML Template

```html
<div class="roundtable-meeting">
  <div class="page-header">
    <h1>Monthly Client Roundtable - {{ current_month|format_month_year }}</h1>
    <span class="badge ned-team">NED Team Only</span>
  </div>
  
  <div class="meeting-controls">
    <div class="month-nav">
      <a href="?month={{ prev_month }}" class="btn btn-sm">◀ Previous Month</a>
      <span class="current-month">{{ current_month|format_month_year }}</span>
      <a href="?month={{ next_month }}" class="btn btn-sm">Next Month ▶</a>
    </div>
    
    <div class="quick-filters">
      <button onclick="filterClients('high-priority')" class="btn btn-sm">High Priority</button>
      <button onclick="filterClients('needs-attention')" class="btn btn-sm">Needs Attention</button>
      <button onclick="generateAgenda()" class="btn btn-sm btn-secondary">Generate Agenda</button>
    </div>
  </div>
  
  <div class="clients-list">
    <h2>Clients to Discuss ({{ clients|length }} selected)</h2>
    
    {% for client in clients %}
    <div class="roundtable-client {% if client.discussed %}discussed{% endif %}" data-client-id="{{ client.owner_id }}">
      <div class="client-header" onclick="toggleClient(this)">
        <h3>
          {% if client.expanded %}▼{% else %}▶{% endif %}
          {{ client.company_name }}
        </h3>
        <div class="client-meta">
          <span class="badge priority-{{ client.client_priority|lower }}">
            Priority: {{ client.client_priority }}
          </span>
          <span class="poc">POC: {{ client.primary_poc_person.full_name if client.primary_poc_person }}</span>
        </div>
      </div>
      
      <div class="client-content" {% if not client.expanded %}style="display:none"{% endif %}>
        <div class="quick-facts">
          <h4>Quick Facts:</h4>
          <ul>
            <li>Relationship: 
              <span class="badge rel-{{ client.relationship_strength|lower|replace(' ', '-') }}">
                {{ client.relationship_strength }}
                {% if client.relationship_strength == 'Needs Attention' %}⚠️{% endif %}
              </span>
            </li>
            <li>{{ client.active_projects_count }} Active Projects</li>
            <li>Last Contact: {{ client.days_since_contact }} days ago</li>
            <li>Team: 
              {{ client.primary_poc_person.full_name if client.primary_poc_person }}
              {% if client.secondary_poc_person %}
              , {{ client.secondary_poc_person.full_name }}
              {% endif %}
              {% if client.team_members %}
              , {{ client.team_members|join(', ', attribute='full_name') }}
              {% endif %}
            </li>
          </ul>
        </div>
        
        {% if client.last_roundtable %}
        <div class="last-roundtable">
          <h4>Last Roundtable ({{ client.last_roundtable.meeting_date|format_month_year }}):</h4>
          <p class="discussion-excerpt">{{ client.last_roundtable.discussion|truncate(200) }}</p>
        </div>
        
        <div class="previous-actions">
          <h4>Previous Action Items:</h4>
          <ul>
            {% for action in client.previous_actions %}
            <li class="{% if action.complete %}complete{% else %}pending{% endif %}">
              {% if action.complete %}✓{% else %}⏳{% endif %}
              {{ action.text }}
              {% if not action.complete %}<span class="pending-label">- Pending</span>{% endif %}
            </li>
            {% endfor %}
          </ul>
        </div>
        {% endif %}
        
        <div class="todays-discussion">
          <h4>📝 Today's Discussion ({{ current_month|format_month_year }}):</h4>
          <textarea name="discussion_{{ client.owner_id }}" 
                    rows="6" 
                    placeholder="Enter discussion notes for this client...">{{ client.draft_discussion }}</textarea>
        </div>
        
        <div class="new-actions">
          <h4>✅ New Action Items:</h4>
          <textarea name="action_items_{{ client.owner_id }}" 
                    rows="4" 
                    placeholder="Enter action items (one per line)...">{{ client.draft_actions }}</textarea>
        </div>
        
        <div class="discussion-controls">
          <label>
            <input type="checkbox" 
                   name="discussed_{{ client.owner_id }}" 
                   {% if client.discussed %}checked{% endif %}>
            Mark as Discussed
          </label>
        </div>
        
        <div class="quick-actions">
          <a href="/owners/{{ client.owner_id }}" class="btn btn-sm btn-link" target="_blank">
            View Full Details ▶
          </a>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
  
  <div class="meeting-footer">
    <div class="meeting-summary">
      <h3>Meeting Summary</h3>
      <ul>
        <li>Clients Discussed: <strong id="discussed-count">0</strong> of {{ clients|length }}</li>
        <li>New Action Items: <strong id="action-count">0</strong></li>
        <li>Follow-ups Assigned: <strong id="followup-count">0</strong></li>
      </ul>
    </div>
    
    <div class="meeting-actions">
      <button onclick="saveDrafts()" class="btn btn-secondary">Save Drafts</button>
      <button onclick="exportSummary()" class="btn btn-secondary">Export Summary</button>
      <button onclick="completeMeeting()" class="btn btn-primary">Complete Meeting</button>
    </div>
  </div>
</div>

<script>
// Update counters as user types
document.querySelectorAll('textarea, input[type="checkbox"]').forEach(element => {
    element.addEventListener('change', updateMeetingSummary);
});

function updateMeetingSummary() {
    const discussedCount = document.querySelectorAll('input[name^="discussed_"]:checked').length;
    const actionCount = Array.from(document.querySelectorAll('textarea[name^="action_items_"]'))
        .filter(ta => ta.value.trim().length > 0).length;
    
    document.getElementById('discussed-count').textContent = discussedCount;
    document.getElementById('action-count').textContent = actionCount;
}

function toggleClient(header) {
    const content = header.nextElementSibling;
    const indicator = header.querySelector('h3');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        indicator.textContent = indicator.textContent.replace('▶', '▼');
    } else {
        content.style.display = 'none';
        indicator.textContent = indicator.textContent.replace('▼', '▶');
    }
}

function completeMeeting() {
    if (!confirm('Complete this roundtable meeting? This will save all discussions and action items.')) {
        return;
    }
    
    // Collect all form data
    const formData = new FormData();
    
    document.querySelectorAll('.roundtable-client').forEach(client => {
        const clientId = client.dataset.clientId;
        const discussion = document.querySelector(`textarea[name="discussion_${clientId}"]`).value;
        const actionItems = document.querySelector(`textarea[name="action_items_${clientId}"]`).value;
        const discussed = document.querySelector(`input[name="discussed_${clientId}"]`).checked;
        
        if (discussed || discussion.trim() || actionItems.trim()) {
            formData.append(`clients[${clientId}][discussion]`, discussion);
            formData.append(`clients[${clientId}][action_items]`, actionItems);
            formData.append(`clients[${clientId}][discussed]`, discussed);
        }
    });
    
    // Submit to backend
    fetch('/roundtable/complete', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Meeting completed successfully!');
            window.location.href = '/crm';
        } else {
            alert('Error: ' + data.message);
        }
    });
}
</script>
```

### Backend Implementation

```python
@app.route('/roundtable')
@login_required
@ned_team_required
def roundtable_meeting():
    """Roundtable meeting view"""
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    # Get clients for roundtable
    clients = db.query(Owners_Developers).filter(
        Owners_Developers.client_priority.in_(['High', 'Strategic'])
    ).all()
    
    # Also include clients needing attention
    attention_clients = db.query(Owners_Developers).filter_by(
        relationship_strength='Needs Attention'
    ).all()
    
    all_clients = list(set(clients + attention_clients))
    
    # Enhance client data
    for client in all_clients:
        client.days_since_contact = calculate_days_since(client.last_contact_date)
        client.active_projects_count = count_active_projects(client.owner_id)
        
        # Get last roundtable entry
        client.last_roundtable = db.query(Roundtable_History).filter_by(
            entity_type='Owner',
            entity_id=client.owner_id
        ).order_by(Roundtable_History.meeting_date.desc()).first()
        
        # Parse previous action items
        if client.last_roundtable and client.last_roundtable.action_items:
            client.previous_actions = parse_action_items(client.last_roundtable.action_items)
        else:
            client.previous_actions = []
        
        # Check if already discussed this month
        client.discussed = check_if_discussed(client.owner_id, month)
        client.expanded = not client.discussed  # Auto-expand undiscussed
    
    return render_template('roundtable_meeting.html',
                         clients=all_clients,
                         current_month=month)


@app.route('/roundtable/complete', methods=['POST'])
@login_required
@ned_team_required
def complete_roundtable():
    """Save roundtable meeting notes"""
    meeting_date = datetime.now().date()
    
    # Get roundtable history limit from settings
    history_limit = int(get_system_setting('roundtable_history_limit', 3))
    
    clients_data = request.form.getlist('clients')
    saved_count = 0
    
    for client_id, data in clients_data.items():
        discussion = data.get('discussion', '').strip()
        action_items = data.get('action_items', '').strip()
        discussed = data.get('discussed', False)
        
        if not (discussed or discussion or action_items):
            continue  # Skip if nothing to save
        
        # Create roundtable entry
        entry = Roundtable_History(
            entity_type='Owner',
            entity_id=client_id,
            meeting_date=meeting_date,
            discussion=discussion,
            action_items=action_items,
            created_by=current_user.user_id
        )
        db.add(entry)
        saved_count += 1
        
        # Maintain history limit - delete oldest if exceeded
        existing_entries = db.query(Roundtable_History).filter_by(
            entity_type='Owner',
            entity_id=client_id
        ).order_by(Roundtable_History.meeting_date.desc()).all()
        
        if len(existing_entries) >= history_limit:
            # Delete oldest entries beyond limit
            to_delete = existing_entries[history_limit-1:]  # -1 because we're adding one
            for old_entry in to_delete:
                db.delete(old_entry)
    
    db.commit()
    
    return jsonify({
        'success': True,
        'message': f'Saved notes for {saved_count} clients'
    })
```

---

## Add Contact Log Entry

### Purpose
Record a client interaction (phone call, meeting, email, etc.)

### Layout

```
┌─────────────────────────────────────────────────────────┐
│          ADD CONTACT LOG ENTRY                           │
│          ClientCo A                                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Contact Date:     [Dec 1, 2025 ▼]                       │
│ Contact Type:     [In-person visit ▼]                   │
│ Your Firm Rep:    [John Smith ▼]                        │
│ Client Contact:   [Bob Johnson, VP Operations]          │
│                                                          │
│ Summary:                                                 │
│ [Large text area for contact summary]                   │
│                                                          │
│ Follow-up Needed: [✓]                                   │
│   Follow-up Date: [Dec 15, 2025 ▼]                      │
│   Assign to:      [John Smith ▼]                        │
│                                                          │
│ 🔒 Mark this contact log as confidential [ ]            │
│    (Visible only to users with confidential access)     │
│                                                          │
│ [Cancel]  [Save]                                         │
└─────────────────────────────────────────────────────────┘
```

### HTML Template

```html
<div class="modal-overlay" id="add-contact-modal">
  <div class="modal-content">
    <div class="modal-header">
      <h2>Add Contact Log Entry</h2>
      <button class="close-btn" onclick="closeModal()">×</button>
    </div>
    
    <form id="contact-log-form" method="POST" action="/contact-log/add">
      <input type="hidden" name="entity_type" value="Owner">
      <input type="hidden" name="entity_id" value="{{ owner_id }}">
      
      <div class="form-group">
        <label for="contact_date">Contact Date *</label>
        <input type="date" 
               id="contact_date" 
               name="contact_date" 
               value="{{ today }}" 
               max="{{ today }}"
               required>
        <p class="field-help">Cannot be a future date</p>
      </div>
      
      <div class="form-group">
        <label for="contact_type">Contact Type *</label>
        <select id="contact_type" name="contact_type" required>
          <option value="">Select...</option>
          <option value="In-person">In-person visit</option>
          <option value="Phone">Phone call</option>
          <option value="Email">Email</option>
          <option value="Video">Video conference</option>
          <option value="Conference">Industry conference</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="contacted_by">Your Firm Representative *</label>
        <select id="contacted_by" name="contacted_by" required>
          <option value="">Select...</option>
          {% for person in internal_personnel %}
          <option value="{{ person.personnel_id }}" 
                  {% if person.personnel_id == current_user_personnel_id %}selected{% endif %}>
            {{ person.full_name }}
          </option>
          {% endfor %}
        </select>
      </div>
      
      <div class="form-group">
        <label for="contact_person">Client Contact</label>
        <input type="text" 
               id="contact_person" 
               name="contact_person_freetext" 
               placeholder="e.g., Bob Johnson, VP Operations">
        <p class="field-help">Name and title of person at client organization</p>
      </div>
      
      <div class="form-group">
        <label for="summary">Summary *</label>
        <textarea id="summary" 
                  name="summary" 
                  rows="6" 
                  required
                  placeholder="Describe the interaction, topics discussed, outcomes..."></textarea>
      </div>
      
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" 
                 id="follow_up_needed" 
                 name="follow_up_needed"
                 onchange="toggleFollowup(this)">
          Follow-up needed
        </label>
      </div>
      
      <div id="followup-fields" style="display: none;">
        <div class="form-group">
          <label for="follow_up_date">Follow-up Date</label>
          <input type="date" 
                 id="follow_up_date" 
                 name="follow_up_date" 
                 min="{{ today }}">
        </div>
        
        <div class="form-group">
          <label for="follow_up_assigned_to">Assign to</label>
          <select id="follow_up_assigned_to" name="follow_up_assigned_to">
            <option value="">Select...</option>
            {% for person in internal_personnel %}
            <option value="{{ person.personnel_id }}">{{ person.full_name }}</option>
            {% endfor %}
          </select>
        </div>
      </div>
      
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" 
                 id="is_confidential" 
                 name="is_confidential">
          🔒 Mark this contact log as confidential
        </label>
        <p class="field-help">Visible only to users with confidential access</p>
      </div>
      
      <div class="form-actions">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Contact Log</button>
      </div>
    </form>
  </div>
</div>

<script>
function toggleFollowup(checkbox) {
    const followupFields = document.getElementById('followup-fields');
    followupFields.style.display = checkbox.checked ? 'block' : 'none';
    
    // Make follow-up fields required if checked
    const followupDate = document.getElementById('follow_up_date');
    const followupAssigned = document.getElementById('follow_up_assigned_to');
    
    if (checkbox.checked) {
        followupDate.required = true;
        followupAssigned.required = true;
    } else {
        followupDate.required = false;
        followupAssigned.required = false;
    }
}
</script>
```

### Backend Implementation

```python
@app.route('/contact-log/add', methods=['GET', 'POST'])
@login_required
def add_contact_log():
    """Add contact log entry"""
    if request.method == 'POST':
        # Validate
        if not request.form.get('contact_date'):
            flash('Contact date is required', 'error')
            return redirect(request.referrer)
        
        # Ensure contact date is not in future
        contact_date = datetime.strptime(request.form.get('contact_date'), '%Y-%m-%d').date()
        if contact_date > datetime.now().date():
            flash('Contact date cannot be in the future', 'error')
            return redirect(request.referrer)
        
        # Create contact log entry
        log_entry = Contact_Log(
            entity_type='Owner',
            entity_id=request.form.get('entity_id'),
            contact_date=contact_date,
            contact_type=request.form.get('contact_type'),
            contacted_by=request.form.get('contacted_by'),
            contact_person_freetext=request.form.get('contact_person_freetext'),
            summary=request.form.get('summary'),
            is_confidential=request.form.get('is_confidential') == 'on',
            follow_up_needed=request.form.get('follow_up_needed') == 'on',
            follow_up_date=request.form.get('follow_up_date') if request.form.get('follow_up_needed') else None,
            follow_up_assigned_to=request.form.get('follow_up_assigned_to') if request.form.get('follow_up_needed') else None,
            created_by=current_user.user_id
        )
        db.add(log_entry)
        
        # Update owner's last_contact fields
        owner = db.query(Owners_Developers).get(request.form.get('entity_id'))
        owner.last_contact_date = contact_date
        owner.last_contact_type = request.form.get('contact_type')
        owner.last_contact_by = request.form.get('contacted_by')
        owner.last_contact_notes = request.form.get('summary')
        owner.modified_by = current_user.user_id
        owner.modified_date = datetime.now()
        
        db.commit()
        
        # Log audit entry
        log_audit_event(current_user.user_id, 'CREATE', 'Contact_Log', 
                       log_entry.contact_id, None, None, request.form.to_dict())
        
        flash('Contact log entry saved successfully', 'success')
        return redirect(url_for('view_owner', owner_id=request.form.get('entity_id')))
    
    # GET - show form
    owner_id = request.args.get('owner_id')
    internal_personnel = db.query(Personnel).filter_by(
        personnel_type='Internal',
        is_active=True
    ).order_by(Personnel.full_name).all()
    
    return render_template('add_contact_log.html',
                         owner_id=owner_id,
                         internal_personnel=internal_personnel,
                         today=datetime.now().date().isoformat())
```

---

## Add Roundtable Entry

### Purpose
Add a single roundtable discussion entry for a client (outside of meeting view)

### Layout

```
┌─────────────────────────────────────────────────────────┐
│    ADD ROUNDTABLE ENTRY                                  │
│    ClientCo A                                            │
│    [🔒 NED Team Only]                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Meeting Date:     [Dec 15, 2025 ▼]                      │
│                                                          │
│ Discussion:                                              │
│ [Large text area for roundtable discussion notes]       │
│                                                          │
│ Action Items:                                            │
│ [Large text area for action items]                      │
│                                                          │
│ Note: This entry will be visible only to NED Team       │
│ members. When you save, the oldest entry will be        │
│ archived if more than 3 exist.                          │
│                                                          │
│ [Cancel]  [Save]                                         │
└─────────────────────────────────────────────────────────┘
```

### HTML Template

```html
<div class="page-content">
  <div class="page-header">
    <h1>Add Roundtable Entry</h1>
    <span class="breadcrumb">
      <a href="/owners">Owners</a> / 
      <a href="/owners/{{ owner.owner_id }}">{{ owner.company_name }}</a> / 
      Add Roundtable Entry
    </span>
  </div>
  
  <div class="access-badge">
    <span class="badge ned-team">🔒 NED Team Only</span>
  </div>
  
  <form method="POST" action="/owners/{{ owner.owner_id }}/roundtable/add" class="roundtable-form">
    <div class="form-group">
      <label for="meeting_date">Meeting Date *</label>
      <input type="date" 
             id="meeting_date" 
             name="meeting_date" 
             value="{{ today }}" 
             required>
    </div>
    
    <div class="form-group">
      <label for="discussion">Discussion *</label>
      <textarea id="discussion" 
                name="discussion" 
                rows="10" 
                required
                placeholder="Enter the roundtable discussion notes for this client..."></textarea>
      <p class="field-help">What was discussed about this client during the roundtable meeting</p>
    </div>
    
    <div class="form-group">
      <label for="action_items">Action Items *</label>
      <textarea id="action_items" 
                name="action_items" 
                rows="6" 
                required
                placeholder="Enter action items (one per line)..."></textarea>
      <p class="field-help">Follow-up actions assigned during the meeting</p>
    </div>
    
    <div class="info-box">
      <strong>Note:</strong> This entry will be visible only to NED Team members. 
      {% set history_limit = get_system_setting('roundtable_history_limit', 3) %}
      The system keeps the last {{ history_limit }} roundtable entries per client. 
      If more than {{ history_limit }} entries exist, the oldest will be permanently deleted.
    </div>
    
    <div class="form-actions">
      <a href="/owners/{{ owner.owner_id }}" class="btn btn-secondary">Cancel</a>
      <button type="submit" class="btn btn-primary">Save Roundtable Entry</button>
    </div>
  </form>
</div>
```

### Backend Implementation

```python
@app.route('/owners/<int:owner_id>/roundtable/add', methods=['GET', 'POST'])
@login_required
@ned_team_required
def add_roundtable_entry(owner_id):
    """Add roundtable entry for owner"""
    owner = db.query(Owners_Developers).get_or_404(owner_id)
    
    if request.method == 'POST':
        # Create entry
        entry = Roundtable_History(
            entity_type='Owner',
            entity_id=owner_id,
            meeting_date=request.form.get('meeting_date'),
            discussion=request.form.get('discussion'),
            action_items=request.form.get('action_items'),
            created_by=current_user.user_id
        )
        db.add(entry)
        db.commit()
        
        # Maintain history limit
        history_limit = int(get_system_setting('roundtable_history_limit', 3))
        maintain_roundtable_history_limit('Owner', owner_id, history_limit)
        
        flash('Roundtable entry saved successfully', 'success')
        return redirect(url_for('view_owner', owner_id=owner_id))
    
    # GET - show form
    return render_template('add_roundtable_entry.html',
                         owner=owner,
                         today=datetime.now().date().isoformat())


def maintain_roundtable_history_limit(entity_type, entity_id, limit):
    """Delete oldest entries if limit exceeded"""
    entries = db.query(Roundtable_History).filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(Roundtable_History.meeting_date.desc()).all()
    
    if len(entries) > limit:
        # Delete oldest entries
        to_delete = entries[limit:]
        for entry in to_delete:
            db.delete(entry)
        db.commit()
```

---

## Summary

### CRM Features Overview

1. ✅ **Contact Tracking** - Log all client interactions (all users)
2. ✅ **Team Assignment** - Assign POCs and team members
3. ✅ **Internal Assessments** - Track relationship strength, priority, status (NED Team)
4. ✅ **Roundtable Meetings** - Monthly structured discussions (NED Team)
5. ✅ **CRM Dashboard** - Overview of client relationships (NED Team)
6. ✅ **Follow-up Tracking** - Track pending actions and scheduled contacts

### Access Control Summary

**All Users Can:**
- View contact tracking summary
- View and add contact log entries
- See upcoming planned contacts
- Assign team members

**NED Team Can:**
- View and edit internal assessments
- View and add roundtable discussion notes
- Access CRM dashboard
- Conduct roundtable meetings
- See relationship strength/priority/status

### Next Steps

1. Review `10_UI_VIEWS_ADMIN.md` for admin interfaces
2. Review `11_NETWORK_DIAGRAM.md` for relationship visualization
3. Review `12_REPORTS.md` for PDF report generation
4. Implement CRM features with proper NED Team access controls

---

**Document End**# 09_UI_VIEWS_CRM.md - CRM User Interface Views

**Document Version:** 1.0  
**Last Updated:** December 4, 2025

**Related Documents:**
- `02_DATABASE_SCHEMA.md` - Owners_Developers, Contact_Log, Roundtable_History tables
- `05_PERMISSION_SYSTEM.md` - NED Team access control
- `08_UI_VIEWS_CORE.md` - Core UI patterns

---

## Overview

This document specifies the CRM (Client Relationship Management) user interface components for tracking interactions with clients (Owners/Developers).

**Key Features:**
- Contact tracking (visible to all users)
- Internal client assessments (NED Team only)
- Roundtable meeting management (NED Team only)
- Client relationship dashboard (NED Team only)

**Access Control:**
- **Contact tracking**: All users can view and add
- **Internal assessments & roundtable notes**: NED Team only

---

## Table of Contents

1. [Owner Detail - CRM Tab](#owner-detail-crm-tab)
2. [CRM Dashboard](#crm-dashboard)
3. [Roundtable Meeting View](#roundtable-meeting-view)
4. [Add Contact Log Entry](#add-contact-log-entry)
5. [Add Roundtable Entry](#add-roundtable-entry)

---

## Owner Detail - CRM Tab

### Purpose
Enhanced owner/developer detail view with CRM features integrated

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ ClientCo A                                  [Edit] [Del] │
├─────────────────────────────────────────────────────────┤
│ [Overview] [Projects] [Relationships] [→CRM] [Personnel] │
└─────────────────────────────────────────────────────────┘

CLIENT RELATIONSHIP MANAGEMENT
───────────────────────────────────────────────────────────

TEAM ASSIGNMENT
  Primary POC:          [John Smith ▼]
  Secondary POC:        [Sarah Lee ▼]
  Team Members:         [Jane Doe] [Remove]
                        [+ Add Team Member]

CONTACT TRACKING (Visible to All)
───────────────────────────────────────────────────────────
  Last Contact:
    Date:               Sep 5, 2025
    Type:               Phone call
    By:                 John Smith
    Notes:              Discussed upcoming project bid...

  Next Planned Contact:
    Date:               Dec 20, 2025
    Type:               In-person visit
    Assigned to:        Sarah Lee
    Purpose:            Site visit and project review

INTERNAL ASSESSMENT (NED Team Only)
───────────────────────────────────────────────────────────
  Client Priority:      [High ▼]
  Client Status:        [Active ▼]
  Relationship:         [Needs Attention ▼]

  Relationship Notes:   [Large text area]

ROUNDTABLE HISTORY (NED Team Only)
───────────────────────────────────────────────────────────
  ▼ November 2025 (Most Recent)
    Discussion: [Content]
    Action Items: [Content]

  ▼ October 2025
    Discussion: [Content]
    Action Items: [Content]

  [Add New Roundtable Entry]

CONTACT HISTORY (Visible to All)              [View All] [Add]
───────────────────────────────────────────────────────────
Date       Type        By          Summary
────────────────────────────────────────────────────────────
Sep 5      Phone       John S.     Discussed Project bid
Aug 12     In-person   Sarah L.    Site visit           🔒
Jul 30     Email       Jane D.     Sent proposal

[🔒 = Confidential entry]
```

### HTML Template

```html
<div class="crm-tab">
  <!-- Team Assignment Section -->
  <section class="crm-section">
    <h2>Team Assignment</h2>
    <div class="team-assignment">
      <div class="form-group">
        <label>Primary POC:</label>
        <select name="primary_poc" onchange="updatePOC(this)">
          <option value="">Select...</option>
          {% for person in internal_personnel %}
          <option value="{{ person.personnel_id }}" 
                  {% if owner.primary_poc == person.personnel_id %}selected{% endif %}>
            {{ person.full_name }}
          </option>
          {% endfor %}
        </select>
      </div>
      
      <div class="form-group">
        <label>Secondary POC:</label>
        <select name="secondary_poc" onchange="updatePOC(this)">
          <option value="">Select...</option>
          {% for person in internal_personnel %}
          <option value="{{ person.personnel_id }}" 
                  {% if owner.secondary_poc == person.personnel_id %}selected{% endif %}>
            {{ person.full_name }}
          </option>
          {% endfor %}
        </select>
      </div>
      
      <div class="team-members">
        <label>Team Members:</label>
        <div class="members-list">
          {% for member in team_members %}
          <span class="team-member-tag">
            {{ member.full_name }}
            <button onclick="removeMember({{ member.personnel_id }})" class="remove-btn">×</button>
          </span>
          {% endfor %}
        </div>
        <button onclick="show