# 08_UI_VIEWS_CORE.md - Core User Interface Views

**Document Version:** 1.0  
**Last Updated:** December 4, 2025

**Related Documents:**
- `02_DATABASE_SCHEMA.md` - Data structures
- `05_PERMISSION_SYSTEM.md` - Access control and display logic
- `09_UI_VIEWS_CRM.md` - CRM-specific views
- `10_UI_VIEWS_ADMIN.md` - Admin-specific views

---

## Overview

This document specifies the core user interface views that all users interact with:
- Application structure and navigation
- Dashboard (home page)
- Entity list views (for all entity types)
- Entity detail views
- Edit/create forms
- Search functionality

**Technology:** HTML5, CSS3, JavaScript (ES6+), responsive design

---

## Table of Contents

1. [Application Structure](#application-structure)
2. [Dashboard](#dashboard)
3. [Entity List Views](#entity-list-views)
4. [Entity Detail Views](#entity-detail-views)
5. [Edit and Create Forms](#edit-and-create-forms)
6. [Search Functionality](#search-functionality)
7. [Common UI Patterns](#common-ui-patterns)
8. [Responsive Design](#responsive-design)

---

## Application Structure

### Main Layout

```
┌─────────────────────────────────────────────────────────┐
│ [NukeWorks Logo]  Dashboard | Vendors | Products | ...  │
│                                                          │
│ [User: John Smith ▼]  [Search...]  [Help]  [Logout]     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│                    [Main Content Area]                   │
│                                                          │
│                                                          │
│                                                          │
│                                                          │
│                                                          │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ Footer: NukeWorks v1.0 | © 2025 [Company]               │
└─────────────────────────────────────────────────────────┘
```

### Navigation Bar

**Primary Navigation (Always Visible):**
- Dashboard
- Vendors (dropdown: All Vendors, Products)
- Owners
- Projects
- Constructors
- Operators
- Personnel
- Reports
- Admin (if user is admin)

**Secondary Navigation (Right Side):**
- User menu (dropdown)
  - Profile
  - Settings
  - Help
  - Logout
- Global search field
- Help icon

### User Menu Dropdown

```
[User: John Smith ▼]
├── My Profile
├── Change Password
├── Settings
├── Help & Documentation
├── About NukeWorks
└── Logout
```

### Navigation Implementation

**HTML Structure:**
```html
<nav class="main-nav">
  <div class="nav-left">
    <a href="/" class="logo">
      <img src="/static/logo.png" alt="NukeWorks">
    </a>
    <ul class="nav-menu">
      <li><a href="/dashboard">Dashboard</a></li>
      <li class="dropdown">
        <a href="/vendors">Vendors ▼</a>
        <ul class="dropdown-menu">
          <li><a href="/vendors">All Vendors</a></li>
          <li><a href="/products">Products</a></li>
        </ul>
      </li>
      <li><a href="/owners">Owners</a></li>
      <li><a href="/projects">Projects</a></li>
      <li><a href="/constructors">Constructors</a></li>
      <li><a href="/operators">Operators</a></li>
      <li><a href="/personnel">Personnel</a></li>
      <li><a href="/reports">Reports</a></li>
      {% if current_user.is_admin %}
      <li><a href="/admin">Admin</a></li>
      {% endif %}
    </ul>
  </div>
  
  <div class="nav-right">
    <input type="search" placeholder="Search..." class="global-search">
    <div class="user-menu dropdown">
      <a href="#" class="user-button">
        {{ current_user.full_name }} ▼
      </a>
      <ul class="dropdown-menu">
        <li><a href="/profile">My Profile</a></li>
        <li><a href="/change-password">Change Password</a></li>
        <li><a href="/help">Help</a></li>
        <li><a href="/logout">Logout</a></li>
      </ul>
    </div>
  </div>
</nav>
```

---

## Dashboard

### Purpose
Central hub showing summary statistics, recent activity, and quick actions.

### Layout

```
═══════════════════════════════════════════════════════════
DASHBOARD
═══════════════════════════════════════════════════════════

SUMMARY STATISTICS
┌─────────────────────────────────────────────────────────┐
│  Total Projects: 45      Active: 32      Complete: 13   │
│  Technology Vendors: 18  Owners: 27      Constructors: 15│
└─────────────────────────────────────────────────────────┘

RECENT ACTIVITY (Last 30 Days)
┌─────────────────────────────────────────────────────────┐
│  Dec 3: Jane Doe updated Project Alpha - CAPEX          │
│  Dec 2: John Smith created new vendor TechCorp X        │
│  Dec 1: Sarah Lee added relationship: Owner A ↔ Vendor B│
│  Nov 30: Bob Wilson updated Owner C - Contact info      │
│  Nov 29: Mary Jones created Project Beta                │
│  [View All Activity →]                                   │
└─────────────────────────────────────────────────────────┘

QUICK ACTIONS
┌─────────────────────────────────────────────────────────┐
│  [+ Add Project]  [+ Add Vendor]  [+ Add Owner]         │
│  [View Network Map]  [Generate Report]                  │
└─────────────────────────────────────────────────────────┘

CLIENT RELATIONSHIP SUMMARY (NED Team Only)
┌─────────────────────────────────────────────────────────┐
│  Clients Needing Attention: 3                            │
│  Upcoming Contacts: 5                                    │
│  Pending Action Items: 8                                 │
│  [View CRM Dashboard →]                                  │
└─────────────────────────────────────────────────────────┘
```

### Components

**1. Summary Statistics Cards:**
```html
<div class="dashboard-stats">
  <div class="stat-card">
    <h3>Projects</h3>
    <div class="stat-number">45</div>
    <div class="stat-breakdown">
      <span class="active">32 Active</span>
      <span class="complete">13 Complete</span>
    </div>
  </div>
  
  <div class="stat-card">
    <h3>Technology Vendors</h3>
    <div class="stat-number">18</div>
  </div>
  
  <div class="stat-card">
    <h3>Owners/Developers</h3>
    <div class="stat-number">27</div>
  </div>
  
  <div class="stat-card">
    <h3>Constructors</h3>
    <div class="stat-number">15</div>
  </div>
</div>
```

**2. Recent Activity Feed:**
```html
<div class="activity-feed">
  <h2>Recent Activity <span class="timeframe">(Last 30 Days)</span></h2>
  <ul class="activity-list">
    <li class="activity-item">
      <span class="activity-date">Dec 3</span>
      <span class="activity-user">Jane Doe</span>
      <span class="activity-action">updated</span>
      <a href="/projects/45">Project Alpha</a>
      <span class="activity-detail">- CAPEX</span>
    </li>
    <!-- More items -->
  </ul>
  <a href="/activity" class="view-all">View All Activity →</a>
</div>
```

**3. Quick Actions:**
```html
<div class="quick-actions">
  <h2>Quick Actions</h2>
  <div class="action-buttons">
    <a href="/projects/new" class="btn btn-primary">
      <span class="icon">+</span> Add Project
    </a>
    <a href="/vendors/new" class="btn btn-primary">
      <span class="icon">+</span> Add Vendor
    </a>
    <a href="/owners/new" class="btn btn-primary">
      <span class="icon">+</span> Add Owner
    </a>
    <a href="/network" class="btn btn-secondary">
      <span class="icon">🗺️</span> View Network Map
    </a>
    <a href="/reports" class="btn btn-secondary">
      <span class="icon">📄</span> Generate Report
    </a>
  </div>
</div>
```

**4. CRM Summary (Conditional - NED Team Only):**
```html
{% if current_user.is_ned_team or current_user.is_admin %}
<div class="crm-summary">
  <h2>Client Relationship Summary <span class="badge">NED Team</span></h2>
  <div class="crm-stats">
    <div class="crm-alert">
      <span class="alert-icon">🔴</span>
      <span class="alert-number">3</span>
      <span class="alert-label">Clients Needing Attention</span>
    </div>
    <div class="crm-item">
      <span class="number">5</span>
      <span class="label">Upcoming Contacts</span>
    </div>
    <div class="crm-item">
      <span class="number">8</span>
      <span class="label">Pending Action Items</span>
    </div>
  </div>
  <a href="/crm" class="btn btn-link">View CRM Dashboard →</a>
</div>
{% endif %}
```

### Data Retrieval

```python
@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard view"""
    # Get summary statistics
    stats = {
        'total_projects': db.query(Projects).count(),
        'active_projects': db.query(Projects).filter_by(project_status='Active').count(),
        'complete_projects': db.query(Projects).filter_by(project_status='Operating').count(),
        'total_vendors': db.query(Technology_Vendors).count(),
        'total_owners': db.query(Owners_Developers).count(),
        'total_constructors': db.query(Constructors).count(),
    }
    
    # Get recent activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_activity = db.query(Audit_Log).filter(
        Audit_Log.timestamp >= thirty_days_ago
    ).order_by(Audit_Log.timestamp.desc()).limit(10).all()
    
    # Get CRM summary if NED Team
    crm_summary = None
    if current_user.is_ned_team or current_user.is_admin:
        crm_summary = get_crm_summary()
    
    return render_template('dashboard.html',
                         stats=stats,
                         recent_activity=recent_activity,
                         crm_summary=crm_summary)
```

---

## Entity List Views

### Purpose
Display paginated, searchable, filterable lists of entities (vendors, projects, owners, etc.)

### Generic List Pattern

**Applies to:**
- Technology Vendors
- Products
- Owners/Developers
- Operators
- Constructors
- Projects
- Personnel

### Layout Template

```
═══════════════════════════════════════════════════════════
[ENTITY TYPE PLURAL] (e.g., TECHNOLOGY VENDORS)
═══════════════════════════════════════════════════════════

[+ Add New] [Import from Excel] [Export to Excel]

Search: [_________] 🔍  Filters: [All ▼]  Sort: [Name ▼]

┌─────────────────────────────────────────────────────────┐
│ Column 1      Column 2      Column 3      Modified      │
├─────────────────────────────────────────────────────────┤
│ Item 1        Data          Data          2 days ago    │
│ Item 2        Data          Data 🔒       5 days ago    │
│ Item 3        Data          Data          1 week ago    │
│ Item 4        Data          Data 🔒       2 weeks ago   │
│ ...                                                      │
└─────────────────────────────────────────────────────────┘

Showing 1-25 of 128  [◀ Previous] [Next ▶]

Note: 🔒 indicates confidential data or relationships
```

### Example: Technology Vendors List

```html
<div class="page-header">
  <h1>Technology Vendors</h1>
  <div class="header-actions">
    <a href="/vendors/new" class="btn btn-primary">+ Add New Vendor</a>
    <a href="/vendors/import" class="btn btn-secondary">Import from Excel</a>
    <a href="/vendors/export" class="btn btn-secondary">Export to Excel</a>
  </div>
</div>

<div class="list-controls">
  <div class="search-box">
    <input type="search" 
           id="entity-search" 
           placeholder="Search vendors..." 
           value="{{ request.args.get('search', '') }}">
    <button class="btn-search">🔍</button>
  </div>
  
  <div class="filters">
    <select name="filter" class="filter-select">
      <option value="">All Vendors</option>
      <option value="has_products">With Products</option>
      <option value="has_projects">With Projects</option>
    </select>
  </div>
  
  <div class="sort">
    <label>Sort by:</label>
    <select name="sort" class="sort-select">
      <option value="name">Name</option>
      <option value="created_date">Date Created</option>
      <option value="modified_date">Recently Modified</option>
    </select>
  </div>
</div>

<table class="entity-table">
  <thead>
    <tr>
      <th>Vendor Name</th>
      <th>Products</th>
      <th>Relationships</th>
      <th>Modified</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {% for vendor in vendors %}
    <tr class="entity-row" onclick="window.location='/vendors/{{ vendor.vendor_id }}'">
      <td>
        <a href="/vendors/{{ vendor.vendor_id }}">{{ vendor.vendor_name }}</a>
      </td>
      <td>{{ vendor.products|length }}</td>
      <td>
        {{ vendor.visible_relationships_count }}
        {% if vendor.hidden_relationships_count > 0 %}
          ({{ vendor.hidden_relationships_count }}🔒)
        {% endif %}
      </td>
      <td>{{ vendor.modified_date|timeago }}</td>
      <td class="actions">
        <a href="/vendors/{{ vendor.vendor_id }}/edit" class="btn-icon" title="Edit">✏️</a>
        <a href="/vendors/{{ vendor.vendor_id }}/delete" class="btn-icon" title="Delete">🗑️</a>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<div class="pagination">
  <div class="pagination-info">
    Showing {{ start }}-{{ end }} of {{ total }}
  </div>
  <div class="pagination-controls">
    {% if page > 1 %}
    <a href="?page={{ page - 1 }}" class="btn btn-sm">◀ Previous</a>
    {% endif %}
    
    <span class="page-numbers">
      {% for p in page_range %}
        {% if p == page %}
          <span class="current-page">{{ p }}</span>
        {% else %}
          <a href="?page={{ p }}">{{ p }}</a>
        {% endif %}
      {% endfor %}
    </span>
    
    {% if page < total_pages %}
    <a href="?page={{ page + 1 }}" class="btn btn-sm">Next ▶</a>
    {% endif %}
  </div>
</div>
```

### Backend Implementation

```python
@app.route('/vendors')
@login_required
def list_vendors():
    """List all vendors with pagination, search, and filters"""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', '')
    sort_by = request.args.get('sort', 'name')
    
    # Build query
    query = db.query(Technology_Vendors)
    
    # Apply search
    if search:
        query = query.filter(Technology_Vendors.vendor_name.ilike(f'%{search}%'))
    
    # Apply filters
    if filter_type == 'has_products':
        query = query.join(Products).group_by(Technology_Vendors.vendor_id)
    
    # Apply sorting
    if sort_by == 'name':
        query = query.order_by(Technology_Vendors.vendor_name)
    elif sort_by == 'created_date':
        query = query.order_by(Technology_Vendors.created_date.desc())
    elif sort_by == 'modified_date':
        query = query.order_by(Technology_Vendors.modified_date.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page)
    vendors = pagination.items
    
    # Calculate relationship counts (respecting confidentiality)
    for vendor in vendors:
        vendor.visible_relationships_count = count_visible_relationships(current_user, vendor)
        vendor.hidden_relationships_count = count_hidden_relationships(current_user, vendor)
    
    return render_template('vendors_list.html',
                         vendors=vendors,
                         pagination=pagination,
                         search=search,
                         filter_type=filter_type,
                         sort_by=sort_by)
```

### Variations by Entity Type

**Projects List - Additional Columns:**
- Location
- Status
- Owner/Developer
- Technology Vendor
- COD (Commercial Operation Date)

**Personnel List - Additional Columns:**
- Role
- Type (Internal/External)
- Organization
- Active Status

**Products List - Additional Columns:**
- Vendor
- Reactor Type
- Capacity (MW)
- Design Status

---

## Entity Detail Views

### Purpose
Display complete information about a single entity with tabs for different aspects

### Layout Template

```
┌─────────────────────────────────────────────────────────┐
│ [Entity Name]                          [Edit] [Delete]   │
├─────────────────────────────────────────────────────────┤
│ [Overview] [Tab2] [Tab3] [Tab4] [History]               │
└─────────────────────────────────────────────────────────┘

[Tab Content Area]

[Audit History Section - Collapsible]
```

### Example: Technology Vendor Detail

```html
<div class="page-header">
  <h1>{{ vendor.vendor_name }}</h1>
  <div class="header-actions">
    <a href="/vendors/{{ vendor.vendor_id }}/edit" class="btn btn-primary">Edit</a>
    <a href="/vendors/{{ vendor.vendor_id }}/delete" class="btn btn-danger">Delete</a>
  </div>
</div>

<div class="tabs">
  <ul class="tab-nav">
    <li class="active"><a href="#overview">Overview</a></li>
    <li><a href="#products">Products ({{ vendor.products|length }})</a></li>
    <li><a href="#relationships">Relationships ({{ visible_relationships|length }})</a></li>
    <li><a href="#personnel">Personnel ({{ vendor.personnel|length }})</a></li>
    <li><a href="#history">History</a></li>
  </ul>
  
  <div class="tab-content">
    <!-- Overview Tab -->
    <div id="overview" class="tab-pane active">
      <section class="detail-section">
        <h2>Vendor Information</h2>
        <dl class="detail-list">
          <dt>Vendor Name:</dt>
          <dd>{{ vendor.vendor_name }}</dd>
          
          <dt>Created:</dt>
          <dd>{{ vendor.created_date|format_date }} by {{ vendor.created_by_user.full_name }}</dd>
          
          <dt>Last Modified:</dt>
          <dd>
            {% if vendor.modified_date %}
              {{ vendor.modified_date|format_date }} by {{ vendor.modified_by_user.full_name }}
            {% else %}
              Never
            {% endif %}
          </dd>
        </dl>
      </section>
      
      <section class="detail-section">
        <h2>Notes</h2>
        <div class="notes-content">
          {{ vendor.notes|safe|default('No notes') }}
        </div>
      </section>
    </div>
    
    <!-- Products Tab -->
    <div id="products" class="tab-pane">
      <section class="detail-section">
        <div class="section-header">
          <h2>Products</h2>
          <a href="/products/new?vendor_id={{ vendor.vendor_id }}" class="btn btn-sm">+ Add Product</a>
        </div>
        
        <table class="simple-table">
          <thead>
            <tr>
              <th>Product Name</th>
              <th>Reactor Type</th>
              <th>Capacity (MW)</th>
              <th>Design Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {% for product in vendor.products %}
            <tr>
              <td><a href="/products/{{ product.product_id }}">{{ product.product_name }}</a></td>
              <td>{{ product.reactor_type }}</td>
              <td>{{ product.thermal_capacity }}</td>
              <td>{{ product.design_status }}</td>
              <td>
                <a href="/products/{{ product.product_id }}/edit" class="btn-icon">✏️</a>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </section>
    </div>
    
    <!-- Relationships Tab -->
    <div id="relationships" class="tab-pane">
      <section class="detail-section">
        <h2>Owners/Developers ({{ owner_relationships|length }})</h2>
        <ul class="relationship-list">
          {% for rel in owner_relationships %}
          <li>
            <a href="/owners/{{ rel.owner.owner_id }}">{{ rel.owner.company_name }}</a>
            - {{ rel.relationship_type }}
            {% if rel.is_confidential %}<span class="badge confidential">🔒 Confidential</span>{% endif %}
            {% if rel.notes %}<p class="rel-notes">{{ rel.notes }}</p>{% endif %}
          </li>
          {% endfor %}
        </ul>
        <a href="/vendors/{{ vendor.vendor_id }}/add-relationship" class="btn btn-sm">+ Add Relationship</a>
      </section>
      
      {% if hidden_relationships_count > 0 %}
      <div class="info-message">
        <strong>{{ hidden_relationships_count }}</strong> confidential relationships are hidden from your view.
      </div>
      {% endif %}
    </div>
    
    <!-- Personnel Tab -->
    <div id="personnel" class="tab-pane">
      <section class="detail-section">
        <div class="section-header">
          <h2>Key Personnel</h2>
          <a href="/personnel/new?vendor_id={{ vendor.vendor_id }}" class="btn btn-sm">+ Add Person</a>
        </div>
        
        <table class="simple-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Role</th>
              <th>Contact</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {% for person in vendor.personnel %}
            <tr>
              <td><a href="/personnel/{{ person.personnel_id }}">{{ person.full_name }}</a></td>
              <td>{{ person.role }}</td>
              <td>{{ person.email }}</td>
              <td>
                <a href="/personnel/{{ person.personnel_id }}/edit" class="btn-icon">✏️</a>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </section>
    </div>
    
    <!-- History Tab -->
    <div id="history" class="tab-pane">
      <section class="detail-section">
        <h2>Audit History</h2>
        <p class="section-description">Last 20 changes to this vendor</p>
        
        <table class="audit-table">
          <thead>
            <tr>
              <th>Date/Time</th>
              <th>User</th>
              <th>Action</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {% for log in audit_history %}
            <tr>
              <td>{{ log.timestamp|format_datetime }}</td>
              <td>{{ log.user.full_name }}</td>
              <td><span class="badge {{ log.action|lower }}">{{ log.action }}</span></td>
              <td>
                {% if log.field_name %}
                  Changed <strong>{{ log.field_name }}</strong>
                  from "{{ log.old_value }}" to "{{ log.new_value }}"
                {% else %}
                  {{ log.notes }}
                {% endif %}
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </section>
    </div>
  </div>
</div>
```

### Backend Implementation

```python
@app.route('/vendors/<int:vendor_id>')
@login_required
def view_vendor(vendor_id):
    """View vendor details"""
    vendor = db.query(Technology_Vendors).get_or_404(vendor_id)
    
    # Get visible relationships
    owner_relationships = get_visible_owner_vendor_relationships(current_user, vendor_id)
    hidden_relationships_count = count_hidden_relationships(current_user, vendor)
    
    # Get audit history
    audit_history = db.query(Audit_Log).filter_by(
        table_name='Technology_Vendors',
        record_id=vendor_id
    ).order_by(Audit_Log.timestamp.desc()).limit(20).all()
    
    return render_template('vendor_detail.html',
                         vendor=vendor,
                         owner_relationships=owner_relationships,
                         hidden_relationships_count=hidden_relationships_count,
                         audit_history=audit_history)
```

---

## Edit and Create Forms

### Purpose
Forms for creating new entities or editing existing ones, with confidentiality marking

### Generic Form Pattern

```
═══════════════════════════════════════════════════════════
[CREATE/EDIT] [ENTITY TYPE]
═══════════════════════════════════════════════════════════

[Form Fields]

[Save Button] [Cancel Button]
```

### Example: Edit Project Form

```html
<div class="page-header">
  <h1>{% if project %}Edit{% else %}Create{% endif %} Project</h1>
</div>

<form method="POST" action="{{ url_for('save_project', project_id=project.project_id if project else None) }}" class="entity-form">
  {{ form.csrf_token }}
  
  <section class="form-section">
    <h2>Project Information</h2>
    
    <div class="form-group">
      <label for="project_name">Project Name *</label>
      <input type="text" 
             id="project_name" 
             name="project_name" 
             value="{{ project.project_name if project }}" 
             required>
    </div>
    
    <div class="form-group">
      <label for="location">Location</label>
      <input type="text" 
             id="location" 
             name="location" 
             value="{{ project.location if project }}">
    </div>
    
    <div class="form-group">
      <label for="project_status">Project Status</label>
      <select id="project_status" name="project_status">
        <option value="">Select status...</option>
        <option value="Planning" {% if project and project.project_status == 'Planning' %}selected{% endif %}>Planning</option>
        <option value="Design" {% if project and project.project_status == 'Design' %}selected{% endif %}>Design</option>
        <option value="Licensing" {% if project and project.project_status == 'Licensing' %}selected{% endif %}>Licensing</option>
        <option value="Construction" {% if project and project.project_status == 'Construction' %}selected{% endif %}>Construction</option>
        <option value="Operating" {% if project and project.project_status == 'Operating' %}selected{% endif %}>Operating</option>
      </select>
    </div>
  </section>
  
  <section class="form-section">
    <h2>Financial Data</h2>
    <p class="section-help">Mark fields as confidential to restrict access</p>
    
    <div class="form-group confidential-field">
      <label for="fuel_cost">Fuel Cost ($)</label>
      <input type="number" 
             id="fuel_cost" 
             name="fuel_cost" 
             value="{{ project.fuel_cost if project }}">
      <label class="confidential-toggle">
        <input type="checkbox" 
               name="fuel_cost_confidential" 
               {% if is_field_confidential(project, 'fuel_cost') %}checked{% endif %}>
        🔒 Mark as Confidential
      </label>
    </div>
    
    <div class="form-group confidential-field">
      <label for="lcoe">LCOE ($/MWh)</label>
      <input type="number" 
             id="lcoe" 
             name="lcoe" 
             value="{{ project.lcoe if project }}">
      <label class="confidential-toggle">
        <input type="checkbox" 
               name="lcoe_confidential" 
               {% if is_field_confidential(project, 'lcoe') %}checked{% endif %}>
        🔒 Mark as Confidential
      </label>
    </div>
  </section>
  
  <section class="form-section">
    <h2>Schedule & MPR</h2>
    
    <div class="form-group">
      <label for="cod">Commercial Operation Date</label>
      <input type="date" 
             id="cod" 
             name="cod" 
             value="{{ project.cod if project }}">
    </div>
    
    <div class="form-group">
      <label for="mpr_project_id">MPR Project ID</label>
      <input type="text" 
             id="mpr_project_id" 
             name="mpr_project_id" 
             value="{{ project.mpr_project_id if project }}"
             placeholder="e.g., MPR-2024-001">
      <p class="field-help">Reference to external MPR project files</p>
    </div>
  </section>
  
  <section class="form-section">
    <h2>Notes</h2>
    
    <div class="form-group">
      <label for="notes">Project Notes</label>
      <textarea id="notes" 
                name="notes" 
                rows="6">{{ project.notes if project }}</textarea>
    </div>
  </section>
  
  <div class="form-actions">
    <button type="submit" class="btn btn-primary">Save Project</button>
    <a href="{{ url_for('view_project', project_id=project.project_id) if project else url_for('list_projects') }}" 
       class="btn btn-secondary">Cancel</a>
  </div>
</form>
```

### Backend - Save Form

```python
@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
def edit_project(project_id=None):
    """Create or edit project"""
    if project_id:
        project = db.query(Projects).get_or_404(project_id)
    else:
        project = None
    
    if request.method == 'POST':
        # Get form data
        data = {
            'project_name': request.form.get('project_name'),
            'location': request.form.get('location'),
            'project_status': request.form.get('project_status'),
            'capex': request.form.get('capex'),
            'opex': request.form.get('opex'),
            'fuel_cost': request.form.get('fuel_cost'),
            'lcoe': request.form.get('lcoe'),
            'cod': request.form.get('cod'),
            'mpr_project_id': request.form.get('mpr_project_id'),
            'notes': request.form.get('notes'),
        }
        
        # Validate
        if not data['project_name']:
            flash('Project name is required', 'error')
            return render_template('project_form.html', project=project)
        
        # Create or update
        if project:
            # Update existing
            for key, value in data.items():
                setattr(project, key, value)
            project.modified_by = current_user.user_id
            project.modified_date = datetime.now()
            action = 'UPDATE'
        else:
            # Create new
            project = Projects(**data)
            project.created_by = current_user.user_id
            db.add(project)
            action = 'CREATE'
        
        db.commit()
        
        # Handle confidentiality flags
        confidential_fields = ['capex', 'opex', 'fuel_cost', 'lcoe']
        for field in confidential_fields:
            is_confidential = request.form.get(f'{field}_confidential') == 'on'
            update_field_confidentiality('Projects', project.project_id, field, 
                                       is_confidential, current_user.user_id)
        
        # Log audit entry
        log_audit_event(current_user.user_id, action, 'Projects', 
                       project.project_id, None, None, data)
        
        flash('Project saved successfully', 'success')
        return redirect(url_for('view_project', project_id=project.project_id))
    
    # GET request - show form
    return render_template('project_form.html', project=project)
```

### Form Validation

**Client-Side (JavaScript):**
```javascript
document.querySelector('.entity-form').addEventListener('submit', function(e) {
    // Required field validation
    const requiredFields = this.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });
    
    if (!isValid) {
        e.preventDefault();
        alert('Please fill in all required fields');
    }
    
    // Number validation
    const numberFields = this.querySelectorAll('input[type="number"]');
    numberFields.forEach(field => {
        if (field.value && parseFloat(field.value) < 0) {
            field.classList.add('error');
            isValid = false;
            e.preventDefault();
            alert('Negative values are not allowed for ' + field.labels[0].textContent);
        }
    });
});
```

---

## Search Functionality

### Global Search

**Location:** Header navigation (always visible)

**Functionality:**
- Search across all entity types
- Real-time suggestions (optional)
- Respects confidentiality

**Implementation:**

```html
<div class="global-search">
  <form action="/search" method="GET">
    <input type="search" 
           name="q" 
           placeholder="Search..." 
           autocomplete="off"
           id="global-search-input">
    <button type="submit" class="btn-search">🔍</button>
  </form>
  
  <!-- Optional: Autocomplete suggestions -->
  <div id="search-suggestions" class="search-suggestions" style="display: none;">
    <ul class="suggestions-list">
      <!-- Populated via JavaScript -->
    </ul>
  </div>
</div>
```

### Search Results Page

```
═══════════════════════════════════════════════════════════
SEARCH RESULTS FOR: "nuclear power"
═══════════════════════════════════════════════════════════

Found 23 results

PROJECTS (8 results)
┌─────────────────────────────────────────────────────────┐
│ Project Alpha                                            │
│ Location: Tennessee, USA | Status: Active                │
│ ...excerpts from description highlighting search term... │
└─────────────────────────────────────────────────────────┘

TECHNOLOGY VENDORS (5 results)
┌─────────────────────────────────────────────────────────┐
│ NuScale Power                                            │
│ Notes: Leading small modular reactor developer...        │
└─────────────────────────────────────────────────────────┘

OWNERS/DEVELOPERS (10 results)
...
```

**Backend:**

```python
@app.route('/search')
@login_required
def search():
    """Global search across all entities"""
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search_results.html', query='', results={})
    
    results = {
        'projects': search_projects(query, current_user),
        'vendors': search_vendors(query, current_user),
        'owners': search_owners(query, current_user),
        'constructors': search_constructors(query, current_user),
        'operators': search_operators(query, current_user),
        'personnel': search_personnel(query, current_user),
    }
    
    total_results = sum(len(r) for r in results.values())
    
    return render_template('search_results.html', 
                         query=query, 
                         results=results,
                         total_results=total_results)

def search_projects(query, user):
    """Search projects, respecting confidentiality"""
    projects = db.query(Projects).filter(
        db.or_(
            Projects.project_name.ilike(f'%{query}%'),
            Projects.location.ilike(f'%{query}%'),
            Projects.notes.ilike(f'%{query}%')
        )
    ).all()
    
    # Filter out projects with confidential data user can't see
    # (or mark which fields are hidden)
    return [filter_confidential_fields(user, p) for p in projects]
```

---

## Common UI Patterns

### Confidentiality Indicators

**Field Display:**
```html
<!-- Public field -->
<dt>CAPEX:</dt>
<dd>$50,000,000</dd>

<!-- Confidential field (no access) -->
<dt>CAPEX:</dt>
<dd class="confidential-restricted">
  <span class="lock-icon">🔒</span>
  [Confidential - Access Restricted]
</dd>

<!-- Confidential field (with access) -->
<dt>CAPEX:</dt>
<dd>
  $50,000,000
  <span class="badge confidential">🔒 Confidential</span>
</dd>
```

**Relationship Count:**
```html
<div class="relationship-count">
  <strong>5</strong> visible relationships
  {% if hidden_count > 0 %}
  <span class="hidden-count">
    ({{ hidden_count }} confidential - hidden)
  </span>
  {% endif %}
</div>
```

### NED Team Badges

```html
<!-- Section header for NED Team content -->
<h2>
  Internal Assessment
  <span class="badge ned-team">NED Team Only</span>
</h2>

<!-- Access restricted message -->
<div class="access-restricted ned-team">
  <span class="icon">🔒</span>
  <p>This section is only visible to NED Team members.</p>
  <p>Contact your administrator for access.</p>
</div>
```

### Action Buttons

```html
<!-- Primary actions -->
<button type="submit" class="btn btn-primary">Save</button>
<button type="button" class="btn btn-secondary">Cancel</button>

<!-- Icon buttons -->
<a href="/edit" class="btn-icon" title="Edit">✏️</a>
<a href="/delete" class="btn-icon btn-danger" title="Delete">🗑️</a>

<!-- Add buttons -->
<a href="/new" class="btn btn-success">
  <span class="icon">+</span> Add New
</a>
```

### Loading States

```html
<!-- Loading spinner -->
<div class="loading-spinner">
  <div class="spinner"></div>
  <p>Loading...</p>
</div>

<!-- Skeleton loader (for tables) -->
<tr class="skeleton-row">
  <td><div class="skeleton-text"></div></td>
  <td><div class="skeleton-text short"></div></td>
  <td><div class="skeleton-text"></div></td>
</tr>
```

### Empty States

```html
<!-- No results -->
<div class="empty-state">
  <div class="empty-icon">📂</div>
  <h3>No projects found</h3>
  <p>Get started by creating your first project.</p>
  <a href="/projects/new" class="btn btn-primary">+ Add Project</a>
</div>

<!-- No search results -->
<div class="empty-state">
  <div class="empty-icon">🔍</div>
  <h3>No results for "{{ query }}"</h3>
  <p>Try a different search term or browse all items.</p>
  <a href="/projects" class="btn btn-secondary">View All Projects</a>
</div>
```

### Flash Messages

```html
<!-- Success message -->
<div class="flash-message success">
  <span class="icon">✓</span>
  <span class="message">Project saved successfully!</span>
  <button class="close">×</button>
</div>

<!-- Error message -->
<div class="flash-message error">
  <span class="icon">✗</span>
  <span class="message">Error: Project name is required.</span>
  <button class="close">×</button>
</div>

<!-- Info message -->
<div class="flash-message info">
  <span class="icon">ℹ</span>
  <span class="message">Some relationships are hidden due to confidentiality.</span>
  <button class="close">×</button>
</div>
```

### Confirmation Dialogs

```html
<!-- Delete confirmation -->
<div class="modal" id="delete-confirm">
  <div class="modal-content">
    <h3>Confirm Deletion</h3>
    <p>Are you sure you want to delete <strong>{{ entity_name }}</strong>?</p>
    <p class="warning">This action cannot be undone.</p>
    <div class="modal-actions">
      <button class="btn btn-danger" onclick="confirmDelete()">Delete</button>
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  </div>
</div>
```

---

## Responsive Design

### Breakpoints

```css
/* Mobile first approach */

/* Extra small devices (phones, less than 576px) */
/* Default styles */

/* Small devices (landscape phones, 576px and up) */
@media (min-width: 576px) { }

/* Medium devices (tablets, 768px and up) */
@media (min-width: 768px) { }

/* Large devices (desktops, 992px and up) */
@media (min-width: 992px) { }

/* Extra large devices (large desktops, 1200px and up) */
@media (min-width: 1200px) { }
```

### Mobile Adaptations

**Navigation on Mobile:**
```html
<!-- Hamburger menu for mobile -->
<nav class="main-nav">
  <div class="nav-mobile">
    <a href="/" class="logo">NukeWorks</a>
    <button class="hamburger" onclick="toggleMenu()">☰</button>
  </div>
  
  <ul class="nav-menu" id="nav-menu">
    <!-- Menu items -->
  </ul>
</nav>

<style>
@media (max-width: 768px) {
  .nav-menu {
    display: none;
    flex-direction: column;
    width: 100%;
  }
  
  .nav-menu.active {
    display: flex;
  }
  
  .hamburger {
    display: block;
  }
}

@media (min-width: 769px) {
  .hamburger {
    display: none;
  }
  
  .nav-menu {
    display: flex;
    flex-direction: row;
  }
}
</style>
```

**Tables on Mobile:**
```html
<!-- Responsive table wrapper -->
<div class="table-responsive">
  <table class="entity-table">
    <!-- Table content -->
  </table>
</div>

<style>
@media (max-width: 768px) {
  .table-responsive {
    overflow-x: auto;
  }
  
  /* Alternative: Card layout for mobile */
  .entity-table {
    display: block;
  }
  
  .entity-table thead {
    display: none;
  }
  
  .entity-table tbody,
  .entity-table tr,
  .entity-table td {
    display: block;
  }
  
  .entity-table tr {
    margin-bottom: 1rem;
    border: 1px solid #ddd;
    padding: 0.5rem;
  }
  
  .entity-table td:before {
    content: attr(data-label);
    font-weight: bold;
    display: inline-block;
    width: 120px;
  }
}
</style>
```

**Forms on Mobile:**
```css
@media (max-width: 768px) {
  .form-group {
    margin-bottom: 1rem;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 0.25rem;
  }
  
  .form-group input,
  .form-group select,
  .form-group textarea {
    width: 100%;
  }
  
  .form-actions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .form-actions .btn {
    width: 100%;
  }
}
```

---

## Accessibility

### ARIA Labels

```html
<!-- Navigation -->
<nav class="main-nav" role="navigation" aria-label="Main navigation">
  <!-- Nav items -->
</nav>

<!-- Search -->
<input type="search" 
       aria-label="Search all entities"
       placeholder="Search...">

<!-- Buttons -->
<button aria-label="Edit project">✏️</button>
<button aria-label="Delete project">🗑️</button>

<!-- Status indicators -->
<span class="badge" role="status" aria-live="polite">Active</span>
```

### Keyboard Navigation

```javascript
// Ensure all interactive elements are keyboard accessible
document.querySelectorAll('.entity-row').forEach(row => {
    row.setAttribute('tabindex', '0');
    row.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            window.location = this.dataset.href;
        }
    });
});

// Trap focus in modals
function trapFocus(modal) {
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    modal.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey && document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    });
}
```

### Color Contrast

```css
/* Ensure sufficient contrast ratios (WCAG AA: 4.5:1 for normal text) */

:root {
    --color-text: #212529;           /* Dark gray on white: 16.1:1 */
    --color-text-muted: #6c757d;     /* Medium gray: 4.54:1 */
    --color-link: #0056b3;           /* Blue: 7.3:1 */
    --color-success: #155724;        /* Dark green: 8.6:1 */
    --color-danger: #721c24;         /* Dark red: 10.4:1 */
    --color-warning: #856404;        /* Dark yellow: 7.5:1 */
}
```

---

## JavaScript Enhancements

### Tab Navigation

```javascript
// Tab switching
document.querySelectorAll('.tab-nav a').forEach(tab => {
    tab.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Remove active class from all tabs
        document.querySelectorAll('.tab-nav li').forEach(li => {
            li.classList.remove('active');
        });
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        
        // Add active class to clicked tab
        this.parentElement.classList.add('active');
        const targetId = this.getAttribute('href').substring(1);
        document.getElementById(targetId).classList.add('active');
    });
});
```

### Auto-save Draft (Optional)

```javascript
// Save form data to localStorage periodically
let formData = {};
const form = document.querySelector('.entity-form');

form.querySelectorAll('input, textarea, select').forEach(field => {
    field.addEventListener('change', function() {
        formData[this.name] = this.value;
        localStorage.setItem('draft_' + form.dataset.entityType, JSON.stringify(formData));
    });
});

// Restore draft on page load
window.addEventListener('load', function() {
    const draft = localStorage.getItem('draft_' + form.dataset.entityType);
    if (draft) {
        const data = JSON.parse(draft);
        Object.keys(data).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) field.value = data[key];
        });
    }
});

// Clear draft on successful save
form.addEventListener('submit', function() {
    localStorage.removeItem('draft_' + form.dataset.entityType);
});
```

### Confirm Navigation on Unsaved Changes

```javascript
let formModified = false;

document.querySelector('.entity-form').addEventListener('change', function() {
    formModified = true;
});

window.addEventListener('beforeunload', function(e) {
    if (formModified) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    }
});

document.querySelector('.entity-form').addEventListener('submit', function() {
    formModified = false;
});
```

---

## CSS Framework Considerations

**Option 1: Custom CSS**
- Full control over styling
- Smaller file size
- No framework dependencies

**Option 2: Bootstrap 5**
- Rapid development
- Well-tested components
- Responsive by default
- Accessibility built-in

**Option 3: Tailwind CSS**
- Utility-first approach
- Highly customizable
- Smaller production builds

**Recommendation:** Use Bootstrap 5 for MVP to accelerate development, can refactor to custom CSS later if needed.

---

## Performance Considerations

### Lazy Loading

```javascript
// Lazy load images
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});
```

### Debounce Search Input

```javascript
// Debounce search to avoid excessive queries
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const searchInput = document.getElementById('global-search-input');
const debouncedSearch = debounce(function(query) {
    // Perform search
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => updateSearchSuggestions(data));
}, 300);

searchInput.addEventListener('input', function(e) {
    debouncedSearch(e.target.value);
});
```

---

## Summary

### Core UI Components

1. ✅ **Navigation** - Main menu, user menu, breadcrumbs
2. ✅ **Dashboard** - Stats, activity feed, quick actions
3. ✅ **Entity Lists** - Paginated, searchable, filterable tables
4. ✅ **Entity Details** - Tabbed views with all information
5. ✅ **Forms** - Create/edit with validation and confidentiality marking
6. ✅ **Search** - Global search across all entities

### Key Patterns

- Confidentiality indicators (🔒)
- NED Team badges
- Empty states
- Loading states
- Flash messages
- Confirmation dialogs

### Next Steps

1. Review `09_UI_VIEWS_CRM.md` for CRM-specific interfaces
2. Review `10_UI_VIEWS_ADMIN.md` for admin interfaces
3. Review `11_NETWORK_DIAGRAM.md` for visualization
4. Implement using chosen CSS framework

---

**Document End** for="capex">CAPEX ($)</label>
      <input type="number" 
             id="capex" 
             name="capex" 
             value="{{ project.capex if project }}">
      <label class="confidential-toggle">
        <input type="checkbox" 
               name="capex_confidential" 
               {% if is_field_confidential(project, 'capex') %}checked{% endif %}>
        🔒 Mark as Confidential
      </label>
    </div>
    
    <div class="form-group confidential-field">
      <label for="opex">OPEX ($)</label>
      <input type="number" 
             id="opex" 
             name="opex" 
             value="{{ project.opex if project }}">
      <label class="confidential-toggle">
        <input type="checkbox" 
               name="opex_confidential" 
               {% if is_field_confidential(project, 'opex') %}checked{% endif %}>
        🔒 Mark as Confidential
      </label>
    </div>
    
    <div class="form-group confidential-field">
      <label