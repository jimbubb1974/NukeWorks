# Technology Vendors CRUD Implementation

**Date:** 2025-10-05
**Status:** ✅ Complete
**Pattern:** Reference implementation for other entities

---

## Overview

Complete CRUD (Create, Read, Update, Delete) operations have been implemented for Technology_Vendors following `docs/02_DATABASE_SCHEMA.md` and `docs/06_BUSINESS_RULES.md`. This serves as the **pattern for implementing CRUD operations for all other entities**.

## Implementation Summary

### ✅ Components Implemented

1. **Forms** (`app/forms/vendors.py`)
   - VendorForm - Create/edit with validation
   - DeleteVendorForm - Delete confirmation with CSRF protection

2. **Routes** (`app/routes/vendors.py`)
   - List vendors (with search)
   - View vendor details
   - Create vendor
   - Edit vendor
   - Delete vendor (with dependency checking)
   - API endpoints (search, get vendor)

3. **Templates** (`app/templates/vendors/`)
   - `list.html` - List view with search
   - `detail.html` - Detail view with relationships
   - `form.html` - Create/edit form
   - `delete.html` - Delete confirmation

---

## File Structure

```
NukeWorks/
├── app/
│   ├── forms/
│   │   └── vendors.py                    # Vendor forms with validation
│   │
│   ├── routes/
│   │   └── vendors.py                    # Complete CRUD routes + API
│   │
│   ├── templates/
│   │   └── vendors/
│   │       ├── list.html                # List view
│   │       ├── detail.html              # Detail view
│   │       ├── form.html                # Create/edit form
│   │       └── delete.html              # Delete confirmation
│   │
│   └── utils/
│       └── validators.py                # Reusable validators
│
└── VENDOR_CRUD_IMPLEMENTATION.md        # This file
```

---

## 1. Forms (`app/forms/vendors.py`)

### VendorForm

Complete form with integrated validation using both WTForms and custom validators.

```python
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.utils.validators import validate_string_field, validate_unique_vendor_name

class VendorForm(FlaskForm):
    vendor_name = StringField(
        'Vendor Name',
        validators=[DataRequired(), Length(min=1, max=255)]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Length(max=10000)]
    )

    submit = SubmitField('Save Vendor')

    def validate_vendor_name(self, field):
        # Clean and validate string
        cleaned_name = validate_string_field(field.data, "vendor_name", max_length=255, required=True)
        field.data = cleaned_name

        # Check uniqueness
        validate_unique_vendor_name(cleaned_name, vendor_id=self.vendor_id)
```

**Features:**
- Integrated validation with custom validators
- Automatic string cleaning (trim whitespace)
- Uniqueness check (case-insensitive)
- Contextual validation (excludes self when editing)

### DeleteVendorForm

Simple form for CSRF protection on delete operations.

```python
class DeleteVendorForm(FlaskForm):
    submit = SubmitField('Confirm Delete')
```

---

## 2. Routes (`app/routes/vendors.py`)

### List Vendors - `GET /vendors/`

**Features:**
- Alphabetical sorting
- Search functionality
- Product count display
- Empty state handling

```python
@bp.route('/')
@login_required
def list_vendors():
    search = request.args.get('search', '').strip()
    query = db_session.query(TechnologyVendor)

    if search:
        query = query.filter(TechnologyVendor.vendor_name.ilike(f'%{search}%'))

    vendors = query.order_by(TechnologyVendor.vendor_name).all()
    # ... get product counts ...
    return render_template('vendors/list.html', ...)
```

### View Vendor - `GET /vendors/<id>`

**Features:**
- Full vendor information
- Related products list
- Project relationships
- Edit/delete buttons (permission-aware)

```python
@bp.route('/<int:vendor_id>')
@login_required
def view_vendor(vendor_id):
    vendor = db_session.get(TechnologyVendor, vendor_id)
    if not vendor:
        abort(404)

    products = db_session.query(Product).filter(...).all()
    project_relationships = db_session.query(ProjectVendorRelationship).filter(...).all()

    return render_template('vendors/detail.html', ...)
```

### Create Vendor - `GET/POST /vendors/new`

**Features:**
- Form validation
- Auto-set created_by/modified_by
- Success message
- Error handling with rollback

```python
@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_vendor():
    form = VendorForm()

    if form.validate_on_submit():
        vendor = TechnologyVendor(
            vendor_name=form.vendor_name.data,
            notes=form.notes.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )
        db_session.add(vendor)
        db_session.commit()

        flash(f'Vendor "{vendor.vendor_name}" created successfully', 'success')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor.vendor_id))

    return render_template('vendors/form.html', ...)
```

**Validation:**
- vendor_name: required, unique, max 255 chars
- notes: optional, max 10000 chars
- Automatic whitespace trimming
- Case-insensitive uniqueness check

### Edit Vendor - `GET/POST /vendors/<id>/edit`

**Features:**
- Pre-populated form
- Uniqueness check excludes current vendor
- Updates modified_by/modified_date
- Error handling

```python
@bp.route('/<int:vendor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vendor(vendor_id):
    vendor = db_session.get(TechnologyVendor, vendor_id)
    if not vendor:
        abort(404)

    form = VendorForm(vendor_id=vendor_id, obj=vendor)

    if form.validate_on_submit():
        vendor.vendor_name = form.vendor_name.data
        vendor.notes = form.notes.data
        vendor.modified_by = current_user.user_id
        vendor.modified_date = datetime.utcnow()

        db_session.commit()
        flash(f'Vendor "{vendor.vendor_name}" updated successfully', 'success')
        return redirect(url_for('vendors.view_vendor', vendor_id=vendor.vendor_id))

    return render_template('vendors/form.html', ...)
```

### Delete Vendor - `GET/POST /vendors/<id>/delete`

**Features:**
- Admin-only access (`@admin_required`)
- Dependency checking
- Cannot delete if products or relationships exist
- Confirmation page with dependency info

```python
@bp.route('/<int:vendor_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_vendor(vendor_id):
    vendor = db_session.get(TechnologyVendor, vendor_id)
    if not vendor:
        abort(404)

    # Check dependencies
    product_count = db_session.query(func.count(Product.product_id)).filter(...).scalar()
    relationship_count = db_session.query(func.count(ProjectVendorRelationship.relationship_id)).filter(...).scalar()
    has_dependencies = product_count > 0 or relationship_count > 0

    form = DeleteVendorForm()

    if form.validate_on_submit():
        if has_dependencies:
            flash('Cannot delete - has dependencies', 'error')
            return redirect(...)

        db_session.delete(vendor)
        db_session.commit()
        flash(f'Vendor "{vendor_name}" deleted successfully', 'success')
        return redirect(url_for('vendors.list_vendors'))

    return render_template('vendors/delete.html', ...)
```

**Business Rules:**
- Only admins can delete
- Cannot delete if products exist
- Cannot delete if relationships exist
- Shows detailed dependency information

### API Endpoints

#### Search Vendors - `GET /vendors/api/search`

Autocomplete endpoint for vendor selection.

```python
@bp.route('/api/search')
@login_required
def api_search_vendors():
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    vendors = db_session.query(TechnologyVendor).filter(
        TechnologyVendor.vendor_name.ilike(f'%{query}%')
    ).order_by(TechnologyVendor.vendor_name).limit(limit).all()

    return jsonify([{'id': v.vendor_id, 'name': v.vendor_name} for v in vendors])
```

#### Get Vendor - `GET /vendors/api/<id>`

Returns vendor data as JSON.

```python
@bp.route('/api/<int:vendor_id>')
@login_required
def api_get_vendor(vendor_id):
    vendor = db_session.get(TechnologyVendor, vendor_id)
    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404

    return jsonify({
        'vendor_id': vendor.vendor_id,
        'vendor_name': vendor.vendor_name,
        'notes': vendor.notes,
        ...
    })
```

---

## 3. Templates

### List View (`list.html`)

**Features:**
- Header with "Add New" button
- Search bar with clear button
- Table with product counts
- View/Edit action buttons
- Empty state messaging
- Responsive design

**Key Elements:**
- Search form: `GET` request to same route
- Product count badges
- Truncated notes preview
- Bootstrap Icons
- Clean, professional layout

### Detail View (`detail.html`)

**Features:**
- Breadcrumb navigation
- Vendor information card
- Products list
- Project relationships table
- Edit/Delete buttons (permission-aware)
- Responsive 2-column layout

**Sections:**
1. **Vendor Information**
   - Vendor ID
   - Vendor Name
   - Notes (with pre-wrap formatting)
   - Created/Modified dates

2. **Products**
   - List of products
   - Add Product button
   - Reactor type display
   - Empty state

3. **Project Relationships**
   - Table of relationships
   - Confidential flag badges
   - Project links
   - Notes preview

### Form View (`form.html`)

**Features:**
- Dynamic title (Create vs Edit)
- Breadcrumb navigation
- Form with validation errors
- Help panel with rules
- Cancel button (context-aware)
- Responsive 2-column layout

**Form Fields:**
```html
<!-- Vendor Name (required) -->
<div class="mb-3">
    {{ form.vendor_name.label(class="form-label") }}
    <span class="text-danger">*</span>
    {{ form.vendor_name(class="form-control" + (" is-invalid" if form.vendor_name.errors else "")) }}
    <!-- Error display -->
    <!-- Help text -->
</div>

<!-- Notes (optional) -->
<div class="mb-3">
    {{ form.notes.label(class="form-label") }}
    {{ form.notes(class="form-control" + (" is-invalid" if form.notes.errors else "")) }}
    <!-- Error display -->
    <!-- Help text -->
</div>
```

**Help Panel:**
- Required fields list
- Validation rules
- Examples
- Best practices

### Delete Confirmation (`delete.html`)

**Features:**
- Warning header with danger styling
- Dependency checking
- Cannot delete if dependencies exist
- Detailed dependency information
- Confirmation form
- Alternative actions suggested

**States:**

1. **Has Dependencies** (Cannot Delete)
   - Warning alert
   - List of dependencies
   - Product count
   - Relationship count
   - Back button only

2. **No Dependencies** (Can Delete)
   - Confirmation prompt
   - Danger warning
   - Vendor information summary
   - Confirm Delete button
   - Cancel button

---

## Validation Rules

### Field Validation

| Field | Required | Max Length | Validation |
|-------|----------|------------|------------|
| vendor_name | Yes | 255 | Unique (case-insensitive), trimmed |
| notes | No | 10,000 | Newlines allowed, trimmed |

### Business Rules

1. **Uniqueness**
   - Vendor names must be unique (case-insensitive)
   - Checked on create and edit
   - Edit excludes current vendor from check

2. **Dependencies**
   - Cannot delete if products exist
   - Cannot delete if project relationships exist
   - Must remove dependencies first

3. **Permissions**
   - All users can view/create/edit
   - Only admins can delete
   - Permission checks in routes and templates

### Custom Validators Used

```python
from app.utils.validators import (
    validate_string_field,        # Clean and validate strings
    validate_unique_vendor_name   # Check uniqueness
)
```

---

## Usage Examples

### Creating a Vendor

1. Navigate to `/vendors/`
2. Click "Add New Vendor"
3. Fill in form:
   - Vendor Name: "NuScale Power" (required)
   - Notes: "Portland-based SMR developer" (optional)
4. Click "Save Vendor"
5. Redirected to vendor detail page

### Searching Vendors

1. Navigate to `/vendors/`
2. Enter search term in search box
3. Click "Search"
4. Results filtered by name
5. Click "Clear" to show all

### Editing a Vendor

1. Navigate to vendor detail page
2. Click "Edit" button
3. Update fields
4. Click "Save Vendor"
5. Changes saved, redirected to detail

### Deleting a Vendor

1. Navigate to vendor detail page (admin only)
2. Click "Delete" button
3. Review confirmation page
4. If dependencies exist: shown error, cannot proceed
5. If no dependencies: click "Confirm Delete"
6. Vendor deleted, redirected to list

---

## Pattern for Other Entities

This implementation serves as the **reference pattern** for implementing CRUD operations for other entities. Follow these steps:

### 1. Create Forms (`app/forms/<entity>.py`)

```python
from flask_wtf import FlaskForm
from wtforms import StringField, ...
from wtforms.validators import DataRequired, Length
from app.utils.validators import validate_string_field, validate_unique_<entity>_name

class <Entity>Form(FlaskForm):
    <field> = StringField('Field Name', validators=[...])

    def __init__(self, <entity>_id=None, *args, **kwargs):
        super(<Entity>Form, self).__init__(*args, **kwargs)
        self.<entity>_id = <entity>_id

    def validate_<field>(self, field):
        # Custom validation using validators.py
        cleaned = validate_string_field(field.data, "<field>", ...)
        field.data = cleaned
        validate_unique_<entity>_name(cleaned, <entity>_id=self.<entity>_id)
```

### 2. Create Routes (`app/routes/<entity>.py`)

**List Route:**
```python
@bp.route('/')
@login_required
def list_<entities>():
    search = request.args.get('search', '').strip()
    query = db_session.query(<Entity>)
    if search:
        query = query.filter(<Entity>.<field>.ilike(f'%{search}%'))
    <entities> = query.order_by(<Entity>.<field>).all()
    return render_template('<entity>/list.html', ...)
```

**View Route:**
```python
@bp.route('/<int:<entity>_id>')
@login_required
def view_<entity>(<entity>_id):
    <entity> = db_session.get(<Entity>, <entity>_id)
    if not <entity>:
        abort(404)
    # Get related data...
    return render_template('<entity>/detail.html', ...)
```

**Create Route:**
```python
@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_<entity>():
    form = <Entity>Form()
    if form.validate_on_submit():
        <entity> = <Entity>(
            <field>=form.<field>.data,
            created_by=current_user.user_id,
            modified_by=current_user.user_id
        )
        db_session.add(<entity>)
        db_session.commit()
        flash('Created successfully', 'success')
        return redirect(url_for('<entity>.view_<entity>', <entity>_id=<entity>.<entity>_id))
    return render_template('<entity>/form.html', ...)
```

**Edit Route:**
```python
@bp.route('/<int:<entity>_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_<entity>(<entity>_id):
    <entity> = db_session.get(<Entity>, <entity>_id)
    if not <entity>:
        abort(404)
    form = <Entity>Form(<entity>_id=<entity>_id, obj=<entity>)
    if form.validate_on_submit():
        <entity>.<field> = form.<field>.data
        <entity>.modified_by = current_user.user_id
        <entity>.modified_date = datetime.utcnow()
        db_session.commit()
        flash('Updated successfully', 'success')
        return redirect(url_for('<entity>.view_<entity>', <entity>_id=<entity>_id))
    return render_template('<entity>/form.html', ...)
```

**Delete Route:**
```python
@bp.route('/<int:<entity>_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_<entity>(<entity>_id):
    <entity> = db_session.get(<Entity>, <entity>_id)
    if not <entity>:
        abort(404)

    # Check dependencies
    has_dependencies = check_<entity>_dependencies(<entity>_id)

    form = Delete<Entity>Form()
    if form.validate_on_submit():
        if has_dependencies:
            flash('Cannot delete - has dependencies', 'error')
            return redirect(...)
        db_session.delete(<entity>)
        db_session.commit()
        flash('Deleted successfully', 'success')
        return redirect(url_for('<entity>.list_<entities>'))

    return render_template('<entity>/delete.html', ...)
```

### 3. Create Templates

Copy and adapt the vendor templates:
- `list.html` - Replace vendor with entity name
- `detail.html` - Add entity-specific fields and relationships
- `form.html` - Add entity-specific form fields
- `delete.html` - Update dependency checks

### 4. Add Validators

If entity has unique fields, add to `app/utils/validators.py`:

```python
def validate_unique_<entity>_name(name, <entity>_id=None):
    from app.models import <Entity>

    query = db_session.query(<Entity>).filter(<Entity>.name.ilike(name))
    if <entity>_id is not None:
        query = query.filter(<Entity>.<entity>_id != <entity>_id)

    if query.first():
        raise ValidationError(f"<Entity> '{name}' already exists")
```

---

## Testing Checklist

### Manual Testing

- [ ] **List View**
  - [ ] Shows all vendors
  - [ ] Search works correctly
  - [ ] Product counts accurate
  - [ ] Action buttons visible
  - [ ] Empty state shows when no results

- [ ] **Detail View**
  - [ ] All vendor information displayed
  - [ ] Products list shown
  - [ ] Relationships shown
  - [ ] Edit/Delete buttons for authorized users
  - [ ] 404 for invalid ID

- [ ] **Create**
  - [ ] Form displays correctly
  - [ ] Validation works (required fields)
  - [ ] Uniqueness check works
  - [ ] Success message shown
  - [ ] Redirects to detail page
  - [ ] created_by/modified_by set correctly

- [ ] **Edit**
  - [ ] Form pre-populated
  - [ ] Validation works
  - [ ] Uniqueness excludes current vendor
  - [ ] Success message shown
  - [ ] modified_by/modified_date updated

- [ ] **Delete**
  - [ ] Admin-only access enforced
  - [ ] Dependency check works
  - [ ] Cannot delete with dependencies
  - [ ] Confirmation page shows
  - [ ] Success message shown
  - [ ] Redirects to list

- [ ] **API**
  - [ ] Search endpoint works
  - [ ] Get endpoint returns JSON
  - [ ] 404 for invalid vendor

---

## Best Practices

### 1. Validation
- Use custom validators from `validators.py`
- Validate in forms AND routes
- Clean data (trim whitespace)
- Check uniqueness properly

### 2. Error Handling
- Always use try/except for database operations
- Rollback on error
- Show user-friendly error messages
- Log errors for debugging

### 3. Permissions
- Use decorators (`@login_required`, `@admin_required`)
- Check permissions in templates
- Hide unauthorized actions

### 4. User Experience
- Clear success/error messages
- Breadcrumb navigation
- Contextual help panels
- Responsive design
- Empty states

### 5. Data Integrity
- Check dependencies before delete
- Use transactions for multi-step operations
- Set audit fields (created_by, modified_by)
- Handle NULL values properly

---

## Common Patterns

### 1. Search Functionality
```python
search = request.args.get('search', '').strip()
if search:
    query = query.filter(<Entity>.<field>.ilike(f'%{search}%'))
```

### 2. Dependency Checking
```python
count = db_session.query(func.count(<Related>.id)).filter(
    <Related>.<entity>_id == <entity>_id
).scalar()
has_dependencies = count > 0
```

### 3. Error Handling
```python
try:
    # Database operation
    db_session.commit()
    flash('Success', 'success')
except Exception as e:
    db_session.rollback()
    flash(f'Error: {str(e)}', 'error')
```

### 4. Form Validation
```python
def validate_<field>(self, field):
    cleaned = validate_string_field(field.data, "<field>", ...)
    field.data = cleaned
    validate_unique_<entity>_name(cleaned, <entity>_id=self.<entity>_id)
```

---

## Troubleshooting

### Issue: Form Validation Fails

**Problem:** Form validation errors not showing

**Solution:**
- Check `{{ form.hidden_tag() }}` is present
- Ensure field has `class="is-invalid"` when errors exist
- Verify error messages are in `<div class="invalid-feedback">`

### Issue: Uniqueness Check Fails on Edit

**Problem:** Can't save edited vendor with same name

**Solution:**
- Pass `vendor_id` to form constructor
- Validator should exclude current record: `query.filter(<Entity>.id != <entity>_id)`

### Issue: Delete Not Working

**Problem:** Delete button doesn't delete vendor

**Solution:**
- Check `@admin_required` decorator is present
- Verify CSRF token in form
- Check for dependencies
- Look for database constraints

---

## Conclusion

The Technology Vendors CRUD implementation is **complete and serves as the reference pattern** for all other entities. Key features:

✅ **Complete CRUD Operations**
- List with search
- Detail view with relationships
- Create with validation
- Edit with pre-population
- Delete with dependency checking

✅ **Robust Validation**
- Custom validators integration
- Uniqueness checking
- String cleaning
- Business rules enforcement

✅ **Professional UI**
- Bootstrap 5 styling
- Responsive design
- Icons and badges
- Help panels
- Empty states

✅ **Security**
- Permission-based access
- CSRF protection
- SQL injection prevention
- Input sanitization

✅ **User Experience**
- Clear messages
- Breadcrumb navigation
- Contextual help
- Error handling

---

**Implementation Complete** ✅

This pattern should be followed for implementing:
- Products
- Projects
- Owners/Developers
- Operators
- Constructors
- Personnel
- And all other entities
