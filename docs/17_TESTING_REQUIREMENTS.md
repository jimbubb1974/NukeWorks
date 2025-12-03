# 17_TESTING_REQUIREMENTS.md - Testing Specifications

**Document Version:** 1.0  
**Last Updated:** December 4, 2025

**Related Documents:**
- `02_DATABASE_SCHEMA.md` - Data structures to test
- `05_PERMISSION_SYSTEM.md` - Permission logic to test
- `06_BUSINESS_RULES.md` - Business rules to verify

---

## Overview

NukeWorks requires comprehensive testing to ensure data integrity, security, and correct functionality across all features.

**Test Coverage Goal:** >80%

---

## Table of Contents

1. [Unit Testing](#unit-testing)
2. [Integration Testing](#integration-testing)
3. [End-to-End Testing](#end-to-end-testing)
4. [Security Testing](#security-testing)
5. [Performance Testing](#performance-testing)
6. [Test Data](#test-data)

---

## Unit Testing

### Database Operations

**Test: CRUD Operations**
```python
def test_create_vendor():
    """Test vendor creation"""
    vendor = Technology_Vendors(
        vendor_name="Test Vendor",
        notes="Test notes"
    )
    db.add(vendor)
    db.commit()
    
    assert vendor.vendor_id is not None
    assert vendor.vendor_name == "Test Vendor"

def test_update_vendor():
    """Test vendor update"""
    vendor = create_test_vendor()
    vendor.vendor_name = "Updated Name"
    db.commit()
    
    retrieved = db.query(Technology_Vendors).get(vendor.vendor_id)
    assert retrieved.vendor_name == "Updated Name"

def test_delete_vendor():
    """Test vendor deletion"""
    vendor = create_test_vendor()
    vendor_id = vendor.vendor_id
    
    db.delete(vendor)
    db.commit()
    
    assert db.query(Technology_Vendors).get(vendor_id) is None
```

### Permission Logic

**Test: Field-Level Confidentiality**
```python
def test_confidential_field_access():
    """Test field-level permission checking"""
    # Setup
    user_no_access = create_test_user(has_confidential_access=False)
    user_with_access = create_test_user(has_confidential_access=True)
    project = create_test_project(capex=50000000)
    mark_field_confidential('Projects', project.project_id, 'capex')
    
    # Test
    assert not can_view_field(user_no_access, 'Projects', project.project_id, 'capex')
    assert can_view_field(user_with_access, 'Projects', project.project_id, 'capex')
    
    # Verify display
    display_no_access = get_display_value(user_no_access, project, 'capex')
    display_with_access = get_display_value(user_with_access, project, 'capex')
    
    assert display_no_access == "[Confidential - Access Restricted]"
    assert display_with_access == 50000000
```

**Test: Relationship Confidentiality**
```python
def test_relationship_confidentiality():
    """Test relationship visibility"""
    user_no_access = create_test_user(has_confidential_access=False)
    user_with_access = create_test_user(has_confidential_access=True)
    
    rel = Project_Vendor_Relationships(
        project_id=1,
        vendor_id=2,
        is_confidential=True
    )
    db.add(rel)
    db.commit()
    
    assert not can_view_relationship(user_no_access, rel)
    assert can_view_relationship(user_with_access, rel)
```

**Test: NED Team Access**
```python
def test_ned_team_access():
    """Test NED Team content access"""
    ned_user = create_test_user(is_ned_team=True)
    regular_user = create_test_user(is_ned_team=False)
    
    assert can_view_ned_content(ned_user)
    assert not can_view_ned_content(regular_user)
    
    # Test roundtable history retrieval
    owner = create_test_owner()
    history = get_roundtable_history(ned_user, 'Owner', owner.owner_id)
    history_regular = get_roundtable_history(regular_user, 'Owner', owner.owner_id)
    
    assert len(history) > 0
    assert len(history_regular) == 0
```

### Data Validation

**Test: Validation Rules**
```python
def test_email_validation():
    """Test email format validation"""
    assert validate_email("user@example.com") == True
    assert validate_email("invalid.email") == False
    assert validate_email("") == True  # Optional

def test_positive_number_validation():
    """Test positive number validation"""
    valid, msg = validate_positive_number(50000, "CAPEX")
    assert valid == True
    
    valid, msg = validate_positive_number(-100, "CAPEX")
    assert valid == False
    assert "non-negative" in msg

def test_date_not_future():
    """Test date cannot be in future"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    
    assert validate_date_not_future(yesterday, "Contact Date")[0] == True
    assert validate_date_not_future(tomorrow, "Contact Date")[0] == False
```

---

## Integration Testing

### Database Migration

**Test: Schema Migration**
```python
def test_migration_application():
    """Test applying migrations"""
    # Create test database
    test_db = create_test_database()
    
    # Apply migrations
    apply_migrations(test_db, from_version=1, to_version=3)
    
    # Verify schema version
    version = get_schema_version(test_db)
    assert version == 3
    
    # Verify new columns exist
    assert column_exists(test_db, 'Projects', 'us_domestic_content_pct')
```

**Test: Migration Rollback**
```python
def test_migration_failure_rollback():
    """Test migration rolls back on error"""
    test_db = create_test_database()
    
    # Insert bad migration that will fail
    bad_migration = create_failing_migration()
    
    try:
        apply_migration(test_db, bad_migration)
        assert False, "Should have raised exception"
    except Exception:
        # Verify database unchanged
        version = get_schema_version(test_db)
        assert version == 1  # Original version
```

### Snapshot & Restore

**Test: Create Snapshot**
```python
def test_create_snapshot():
    """Test snapshot creation"""
    # Add test data
    vendor = create_test_vendor()
    db.commit()
    
    # Create snapshot
    snapshot_path = create_snapshot(db_path)
    
    assert os.path.exists(snapshot_path)
    assert snapshot_path.endswith('.sqlite')
    
    # Verify snapshot metadata recorded
    snapshot_record = db.query(Database_Snapshots).order_by(
        Database_Snapshots.snapshot_timestamp.desc()
    ).first()
    
    assert snapshot_record is not None
    assert snapshot_record.file_path == snapshot_path
```

**Test: Restore Snapshot**
```python
def test_restore_snapshot():
    """Test restoring from snapshot"""
    # Create snapshot
    vendor1 = create_test_vendor(name="Vendor 1")
    db.commit()
    snapshot_path = create_snapshot(db_path)
    
    # Make changes
    vendor2 = create_test_vendor(name="Vendor 2")
    db.commit()
    
    # Restore snapshot
    restore_from_snapshot(db_path, snapshot_path)
    
    # Verify only vendor1 exists
    vendors = db.query(Technology_Vendors).all()
    assert len(vendors) == 1
    assert vendors[0].vendor_name == "Vendor 1"
```

### Import/Export

**Test: Excel Import**
```python
def test_excel_import():
    """Test importing data from Excel"""
    # Create test Excel file
    excel_file = create_test_excel_file([
        {'vendor_name': 'Vendor A', 'notes': 'Notes A'},
        {'vendor_name': 'Vendor B', 'notes': 'Notes B'},
    ])
    
    # Import
    result = import_from_excel(excel_file, 'Technology_Vendors')
    
    assert result['success'] == True
    assert result['imported_count'] == 2
    
    # Verify data
    vendors = db.query(Technology_Vendors).all()
    assert len(vendors) >= 2
```

---

## End-to-End Testing

### Complete User Workflows

**Test: Data Entry & Retrieval Flow**
```python
def test_complete_project_workflow():
    """Test complete project lifecycle"""
    # 1. Login
    login_response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    assert login_response.status_code == 302  # Redirect after login
    
    # 2. Create project
    response = client.post('/projects/new', data={
        'project_name': 'Test Project',
        'location': 'California',
        'project_status': 'Planning',
        'capex': 50000000,
        'capex_confidential': 'on'
    })
    assert response.status_code == 302
    
    # 3. Verify project created
    project = db.query(Projects).filter_by(project_name='Test Project').first()
    assert project is not None
    
    # 4. Verify confidentiality flag
    flag = db.query(Confidential_Field_Flags).filter_by(
        table_name='Projects',
        record_id=project.project_id,
        field_name='capex'
    ).first()
    assert flag.is_confidential == True
    
    # 5. View as user without access
    client.get('/logout')
    login_as(client, create_test_user(has_confidential_access=False))
    
    response = client.get(f'/projects/{project.project_id}')
    assert b'[Confidential - Access Restricted]' in response.data
```

**Test: CRM Workflow (NED Team)**
```python
def test_crm_workflow():
    """Test CRM features end-to-end"""
    # Setup: NED Team user
    ned_user = create_test_user(is_ned_team=True)
    login_as(client, ned_user)
    
    owner = create_test_owner()
    
    # 1. Add contact log
    response = client.post('/contact-log/add', data={
        'entity_type': 'Owner',
        'entity_id': owner.owner_id,
        'contact_date': '2025-12-01',
        'contact_type': 'Phone',
        'contacted_by': get_internal_personnel_id(),
        'summary': 'Discussed project timeline'
    })
    assert response.status_code == 302
    
    # 2. Add roundtable entry
    response = client.post(f'/owners/{owner.owner_id}/roundtable/add', data={
        'meeting_date': '2025-12-15',
        'discussion': 'Client needs more attention',
        'action_items': 'Schedule site visit'
    })
    assert response.status_code == 302
    
    # 3. View CRM dashboard
    response = client.get('/crm')
    assert b'Client Relationship Dashboard' in response.data
    
    # 4. Verify non-NED user cannot access
    client.get('/logout')
    login_as(client, create_test_user(is_ned_team=False))
    
    response = client.get('/crm')
    assert response.status_code == 403  # Forbidden
```

**Test: Report Generation**
```python
def test_report_generation():
    """Test PDF report generation end-to-end"""
    user = create_test_user(has_confidential_access=True)
    login_as(client, user)
    
    project = create_test_project()
    
    # Generate report
    response = client.post('/reports/project-summary', data={
        'project_id': project.project_id,
        'include_confidential': 'on',
        'format': 'pdf'
    })
    
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'
    assert b'%PDF' in response.data  # PDF signature
```

---

## Security Testing

### Authentication

**Test: Login Security**
```python
def test_password_hashing():
    """Test passwords are properly hashed"""
    user = create_user('testuser', 'password123')
    
    # Password should be hashed, not stored in plain text
    assert user.password_hash != 'password123'
    assert len(user.password_hash) > 50  # Bcrypt hash length
    
    # Should be able to verify correct password
    assert check_password(user, 'password123') == True
    assert check_password(user, 'wrongpassword') == False

def test_login_attempts():
    """Test invalid login attempts"""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 200  # Stay on login page
    assert b'Invalid credentials' in response.data
```

### Authorization

**Test: Admin-Only Access**
```python
def test_admin_only_routes():
    """Test admin routes are protected"""
    regular_user = create_test_user(is_admin=False)
    login_as(client, regular_user)
    
    # Try to access admin routes
    response = client.get('/admin/users')
    assert response.status_code == 403
    
    response = client.get('/admin/settings')
    assert response.status_code == 403
```

### Input Validation

**Test: SQL Injection Prevention**
```python
def test_sql_injection_protection():
    """Test SQL injection attempts are blocked"""
    malicious_input = "'; DROP TABLE Projects; --"
    
    response = client.post('/projects/new', data={
        'project_name': malicious_input
    })
    
    # Should either validate and reject, or safely escape
    # Projects table should still exist
    assert table_exists('Projects')
    
    # If saved, should be escaped text, not SQL
    project = db.query(Projects).filter_by(project_name=malicious_input).first()
    if project:
        assert project.project_name == malicious_input  # Stored as text

def test_xss_prevention():
    """Test XSS attempts are escaped"""
    malicious_input = "<script>alert('XSS')</script>"
    
    project = create_test_project(project_name=malicious_input)
    
    response = client.get(f'/projects/{project.project_id}')
    
    # Should be HTML-escaped in output
    assert b'<script>' not in response.data
    assert b'&lt;script&gt;' in response.data or b'alert(&#39;XSS&#39;)' in response.data
```

---

## Performance Testing

### Load Testing

**Test: Concurrent Users**
```python
def test_concurrent_access():
    """Test multiple users accessing database simultaneously"""
    import threading
    
    def create_vendor(name):
        vendor = Technology_Vendors(vendor_name=name)
        db.add(vendor)
        db.commit()
    
    # Create 10 vendors concurrently
    threads = []
    for i in range(10):
        t = threading.Thread(target=create_vendor, args=(f"Vendor {i}",))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Verify all created successfully
    vendors = db.query(Technology_Vendors).all()
    assert len(vendors) >= 10
```

**Test: Large Dataset Performance**
```python
def test_large_dataset_query_performance():
    """Test query performance with large dataset"""
    import time
    
    # Create 1000 projects
    for i in range(1000):
        project = create_test_project(project_name=f"Project {i}")
        db.add(project)
    db.commit()
    
    # Test query performance
    start = time.time()
    projects = db.query(Projects).limit(25).all()
    elapsed = time.time() - start
    
    assert elapsed < 1.0  # Should complete in under 1 second
    assert len(projects) == 25
```

**Test: Report Generation Performance**
```python
def test_report_generation_performance():
    """Test report generation with realistic data"""
    import time
    
    project = create_test_project_with_relationships()
    user = create_test_user(has_confidential_access=True)
    
    start = time.time()
    report_data = generate_project_summary_data(user, project.project_id)
    elapsed = time.time() - start
    
    assert elapsed < 5.0  # Should complete in under 5 seconds
```

### Network Latency Testing

**Test: Network Drive Performance**
```python
def test_network_drive_operations():
    """Test database operations on network drive"""
    import time
    
    # Measure write performance
    start = time.time()
    for i in range(10):
        vendor = create_test_vendor()
        db.commit()
    write_time = time.time() - start
    
    # Measure read performance
    start = time.time()
    vendors = db.query(Technology_Vendors).all()
    read_time = time.time() - start
    
    # Should be reasonable even on network drive
    assert write_time < 5.0  # 10 writes in under 5 seconds
    assert read_time < 1.0   # Read all in under 1 second
```

---

## Test Data

### Test Data Setup

**Fixtures:**
```python
# tests/fixtures.py

import pytest
from datetime import datetime, date, timedelta

@pytest.fixture
def test_user():
    """Create test user"""
    user = Users(
        username='testuser',
        email='test@example.com',
        password_hash=hash_password('password123'),
        full_name='Test User',
        has_confidential_access=False,
        is_ned_team=False,
        is_admin=False
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def test_vendor():
    """Create test technology vendor"""
    vendor = Technology_Vendors(
        vendor_name='Test Vendor Inc',
        notes='A test vendor for unit testing'
    )
    db.add(vendor)
    db.commit()
    return vendor

@pytest.fixture
def test_project():
    """Create test project"""
    project = Projects(
        project_name='Test Project Alpha',
        location='California, USA',
        project_status='Planning',
        capex=50000000,
        opex=2000000,
        cod=date.today() + timedelta(days=730)
    )
    db.add(project)
    db.commit()
    return project

@pytest.fixture
def test_owner():
    """Create test owner/developer"""
    owner = Owners_Developers(
        company_name='Test Utility Co',
        company_type='IOU',
        engagement_level='Interested'
    )
    db.add(owner)
    db.commit()
    return owner

@pytest.fixture
def ned_team_user():
    """Create NED Team user"""
    user = Users(
        username='neduser',
        email='ned@example.com',
        password_hash=hash_password('password123'),
        full_name='NED Team Member',
        has_confidential_access=True,
        is_ned_team=True,
        is_admin=False
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def admin_user():
    """Create admin user"""
    user = Users(
        username='admin',
        email='admin@example.com',
        password_hash=hash_password('admin123'),
        full_name='Admin User',
        is_admin=True
    )
    db.add(user)
    db.commit()
    return user
```

### Test Database Setup

```python
# tests/conftest.py

import pytest
import os
import tempfile
from app import create_app
from utils.db import init_db

@pytest.fixture
def test_db():
    """Create temporary test database"""
    db_fd, db_path = tempfile.mkstemp(suffix='.sqlite')
    
    # Initialize database
    init_db(db_path)
    
    yield db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(test_db):
    """Create test client"""
    app = create_app({'DATABASE_PATH': test_db, 'TESTING': True})
    
    with app.test_client() as client:
        with app.app_context():
            yield client
```

---

## Test Execution

### Running Tests

**Run All Tests:**
```bash
pytest tests/
```

**Run Specific Test File:**
```bash
pytest tests/test_permissions.py
```

**Run with Coverage:**
```bash
pytest --cov=. --cov-report=html tests/
```

**Run Performance Tests Only:**
```bash
pytest -m performance tests/
```

### Test Organization

```
tests/
├── conftest.py (shared fixtures)
├── fixtures.py (test data)
│
├── unit/
│   ├── test_models.py
│   ├── test_permissions.py
│   ├── test_validators.py
│   └── test_utils.py
│
├── integration/
│   ├── test_migrations.py
│   ├── test_snapshots.py
│   ├── test_imports.py
│   └── test_reports.py
│
├── e2e/
│   ├── test_user_workflows.py
│   ├── test_crm_workflows.py
│   └── test_admin_workflows.py
│
├── security/
│   ├── test_authentication.py
│   ├── test_authorization.py
│   └── test_input_validation.py
│
└── performance/
    ├── test_concurrent_access.py
    ├── test_large_datasets.py
    └── test_network_performance.py
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml

name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        files: ./coverage.xml
```

---

## Test Coverage Goals

### Minimum Coverage Requirements

| Component | Target Coverage |
|-----------|-----------------|
| Models (database) | 90% |
| Permissions logic | 95% |
| Validators | 90% |
| Routes (endpoints) | 80% |
| Services | 85% |
| Utilities | 85% |
| **Overall** | **>80%** |

### Critical Paths (100% Coverage Required)

- Permission checking functions
- Data validation
- Password hashing/verification
- Audit logging
- Migration application
- Snapshot creation/restoration

---

## Manual Testing Checklist

### Pre-Release Testing

**Functional Testing:**
- [ ] All CRUD operations work for each entity type
- [ ] Confidential data properly hidden from unauthorized users
- [ ] NED Team content only visible to authorized users
- [ ] Reports generate correctly with confidentiality filtering
- [ ] Network diagram displays relationships correctly
- [ ] Import from Excel works with sample data
- [ ] Export to Excel produces valid files
- [ ] Snapshots create and restore successfully
- [ ] Migrations apply without errors

**UI Testing:**
- [ ] All forms validate properly
- [ ] Navigation works on all pages
- [ ] Search functionality returns correct results
- [ ] Pagination works correctly
- [ ] Responsive design works on different screen sizes
- [ ] Browser compatibility (Chrome, Edge, Firefox)

**Security Testing:**
- [ ] Cannot access admin pages without admin role
- [ ] Cannot view confidential data without permission
- [ ] Cannot access NED Team content without permission
- [ ] SQL injection attempts fail
- [ ] XSS attempts are escaped
- [ ] Session expires after inactivity

**Performance Testing:**
- [ ] Application starts in <10 seconds
- [ ] Pages load in <2 seconds
- [ ] Reports generate in <10 seconds
- [ ] No memory leaks during extended use
- [ ] Works with 2+ concurrent users

**Network Drive Testing:**
- [ ] Database accessible from network drive
- [ ] Multiple users can access simultaneously
- [ ] No database corruption with concurrent access
- [ ] Reasonable performance over network
- [ ] Graceful handling of network interruptions

---

## Bug Tracking

### Bug Report Template

```
Title: [Brief description]

Environment:
- OS: Windows 10/11
- Browser: Chrome 120
- Application Version: 1.5.0

Steps to Reproduce:
1. Navigate to...
2. Click on...
3. Enter data...

Expected Behavior:
[What should happen]

Actual Behavior:
[What actually happens]

Screenshots:
[If applicable]

Additional Context:
[Any other relevant information]

Priority: High/Medium/Low
Category: Bug/Feature/Enhancement
```

---

## Summary

### Testing Strategy

1. ✅ **Unit Tests** - Test individual functions and classes
2. ✅ **Integration Tests** - Test component interactions
3. ✅ **E2E Tests** - Test complete user workflows
4. ✅ **Security Tests** - Test authentication and authorization
5. ✅ **Performance Tests** - Test with realistic loads

### Key Testing Principles

- **Test early and often** during development
- **Automate what you can** to catch regressions
- **Test edge cases** and error conditions
- **Test permissions thoroughly** - security critical
- **Test on network drive** - matches production
- **Maintain >80% coverage** overall

### Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Coverage goals met
- [ ] Manual testing complete
- [ ] Security audit performed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Deployment plan reviewed

---

**Document End**