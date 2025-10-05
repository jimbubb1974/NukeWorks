"""
Two-Tier Permission System for NukeWorks
Implements field-level and relationship-level confidentiality
Following docs/05_PERMISSION_SYSTEM.md specification
"""
from functools import wraps
from flask import flash, redirect, url_for, abort, current_app
from flask_login import current_user
from app.models import ConfidentialFieldFlag


def get_db_session():
    """Get db_session from current app context"""
    from app import db_session as app_db_session
    if app_db_session is not None:
        return app_db_session
    # Fallback to app context
    if current_app:
        return current_app.db_session
    raise RuntimeError("No database session available")


# =============================================================================
# TIER 1: BUSINESS DATA CONFIDENTIALITY
# =============================================================================

def can_view_field(user, table_name, record_id, field_name):
    """
    Check if user can view a specific field (Tier 1: Business Confidentiality)

    Args:
        user: User object (or current_user)
        table_name: Name of database table (e.g., 'projects')
        record_id: ID of the specific record
        field_name: Name of the field to check

    Returns:
        Boolean: True if user can view field, False otherwise

    Examples:
        >>> can_view_field(current_user, 'projects', 45, 'capex')
        True  # If user has confidential access or field is not flagged
    """
    # Admin has access to everything
    if user and user.is_admin:
        return True

    # Check if field is flagged as confidential
    db_session = get_db_session()
    flag = db_session.query(ConfidentialFieldFlag).filter_by(
        table_name=table_name,
        record_id=record_id,
        field_name=field_name
    ).first()

    # If no flag exists or flag says not confidential, field is public
    if not flag or not flag.is_confidential:
        return True

    # Field is confidential - check user permission
    if user:
        return user.has_confidential_access or user.is_admin

    return False


def get_field_display_value(user, entity, field_name, table_name=None, redaction_message="[Confidential]"):
    """
    Get display value for a field, respecting confidentiality

    Args:
        user: User object (or current_user)
        entity: SQLAlchemy model instance
        field_name: Name of the field to display
        table_name: Optional table name (defaults to entity.__tablename__)
        redaction_message: Message to show for restricted fields

    Returns:
        String or value: Actual value if allowed, redaction message otherwise

    Examples:
        >>> get_field_display_value(current_user, project, 'capex')
        5000000  # Or "[Confidential]" if no access
    """
    if table_name is None:
        table_name = entity.__tablename__

    # Get the actual value
    actual_value = getattr(entity, field_name, None)

    # Get primary key value (assumes field named {table}_id or id)
    pk_field = f"{table_name.rstrip('s')}_id" if hasattr(entity, f"{table_name.rstrip('s')}_id") else 'id'
    record_id = getattr(entity, pk_field, None)

    if record_id and can_view_field(user, table_name, record_id, field_name):
        return actual_value
    elif actual_value is not None and not can_view_field(user, table_name, record_id, field_name):
        return redaction_message
    else:
        return actual_value


def can_view_relationship(user, relationship):
    """
    Check if user can view a specific relationship (Tier 1: Business Confidentiality)

    Args:
        user: User object (or current_user)
        relationship: Relationship model instance (must have is_confidential attribute)

    Returns:
        Boolean: True if user can view relationship, False otherwise

    Examples:
        >>> can_view_relationship(current_user, project_vendor_relationship)
        True  # If user has confidential access or relationship is not flagged
    """
    # Admin has access to everything
    if user and user.is_admin:
        return True

    # Check if relationship has is_confidential attribute
    if not hasattr(relationship, 'is_confidential'):
        return True  # If no confidentiality flag, assume public

    # If not confidential, everyone can see it
    if not relationship.is_confidential:
        return True

    # Relationship is confidential - check user permission
    if user:
        return user.has_confidential_access or user.is_admin

    return False


def filter_relationships(user, relationships):
    """
    Filter a list/query of relationships based on user permissions

    Args:
        user: User object (or current_user)
        relationships: List or SQLAlchemy query of relationship objects

    Returns:
        List: Filtered relationships user can view

    Examples:
        >>> visible = filter_relationships(current_user, project.vendor_relationships)
        >>> len(visible)  # Only non-confidential or user has access
    """
    # Admin can see everything
    if user and user.is_admin:
        return list(relationships) if not hasattr(relationships, 'all') else relationships.all()

    # Filter based on permissions
    visible = []
    items = relationships if hasattr(relationships, '__iter__') and not hasattr(relationships, 'all') else relationships.all()

    for rel in items:
        if can_view_relationship(user, rel):
            visible.append(rel)

    return visible


def mark_field_confidential(table_name, record_id, field_name, is_confidential=True, user_id=None):
    """
    Mark a specific field as confidential (or remove confidentiality)

    Args:
        table_name: Name of database table
        record_id: ID of the specific record
        field_name: Name of the field to mark
        is_confidential: True to mark confidential, False to make public
        user_id: ID of user making the change

    Returns:
        ConfidentialFieldFlag: The flag object created/updated
    """
    db_session = get_db_session()

    # Check if flag already exists
    flag = db_session.query(ConfidentialFieldFlag).filter_by(
        table_name=table_name,
        record_id=record_id,
        field_name=field_name
    ).first()

    if flag:
        # Update existing flag
        flag.is_confidential = is_confidential
        if user_id:
            flag.marked_by = user_id
    else:
        # Create new flag
        flag = ConfidentialFieldFlag(
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            is_confidential=is_confidential,
            marked_by=user_id
        )
        db_session.add(flag)

    db_session.commit()
    return flag


def mark_financial_fields_confidential(project_id, is_confidential=True, user_id=None):
    """
    Mark all financial fields of a project as confidential

    Args:
        project_id: ID of the project
        is_confidential: True to mark confidential, False to make public
        user_id: ID of user making the change

    Returns:
        List[ConfidentialFieldFlag]: List of flags created/updated
    """
    financial_fields = ['capex', 'opex', 'fuel_cost', 'lcoe']
    flags = []

    for field in financial_fields:
        flag = mark_field_confidential('projects', project_id, field, is_confidential, user_id)
        flags.append(flag)

    return flags


# =============================================================================
# TIER 2: NED TEAM ACCESS (INTERNAL NOTES)
# =============================================================================

def can_view_ned_content(user):
    """
    Check if user can view NED Team content (Tier 2: Internal Notes)

    Args:
        user: User object (or current_user)

    Returns:
        Boolean: True if user is NED Team or Admin

    Examples:
        >>> can_view_ned_content(current_user)
        True  # If user.is_ned_team or user.is_admin
    """
    if not user or not user.is_authenticated:
        return False

    return user.is_ned_team or user.is_admin


def get_ned_field_value(user, entity, field_name, redaction_message="[NED Team Only]"):
    """
    Get value for a NED Team-restricted field

    Args:
        user: User object
        entity: Entity with NED fields
        field_name: Name of NED field
        redaction_message: Message for non-NED users

    Returns:
        Value or redaction message
    """
    if can_view_ned_content(user):
        return getattr(entity, field_name, None)
    else:
        # Check if field has a value
        actual_value = getattr(entity, field_name, None)
        if actual_value:
            return redaction_message
        return None


def filter_ned_fields(user, entity):
    """
    Return a copy of entity dict with NED fields redacted if user lacks access

    Args:
        user: User object
        entity: Entity object or dict

    Returns:
        dict: Entity data with NED fields redacted if necessary
    """
    NED_FIELDS = [
        'relationship_strength',
        'relationship_notes',
        'client_priority',
        'client_status'
    ]

    if isinstance(entity, dict):
        data = entity.copy()
    else:
        data = entity.to_dict() if hasattr(entity, 'to_dict') else {}

    if not can_view_ned_content(user):
        for field in NED_FIELDS:
            if field in data and data[field]:
                data[field] = "[NED Team Only]"

    return data


# =============================================================================
# ROUTE PROTECTION DECORATORS
# =============================================================================

def confidential_access_required(f):
    """
    Decorator to require Tier 1 (Confidential Access) permission

    Usage:
        @bp.route('/financial-reports')
        @login_required
        @confidential_access_required
        def financial_reports():
            # Only users with confidential access can access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not (current_user.has_confidential_access or current_user.is_admin):
            flash('Access denied. This page requires confidential data access permissions.', 'danger')
            return abort(403)

        return f(*args, **kwargs)

    return decorated_function


def ned_team_required(f):
    """
    Decorator to require Tier 2 (NED Team) permission

    Usage:
        @bp.route('/crm/roundtable')
        @login_required
        @ned_team_required
        def roundtable():
            # Only NED Team members can access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not can_view_ned_content(current_user):
            flash('Access denied. This page is restricted to NED Team members.', 'danger')
            return abort(403)

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Decorator to require Administrator permission

    Usage:
        @bp.route('/admin/users')
        @login_required
        @admin_required
        def manage_users():
            # Only admins can access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_admin:
            flash('Access denied. This page requires administrator privileges.', 'danger')
            return abort(403)

        return f(*args, **kwargs)

    return decorated_function


# =============================================================================
# PERMISSION CHECKING UTILITIES
# =============================================================================

def get_user_permission_summary(user):
    """
    Get a summary of user's permissions for display

    Args:
        user: User object

    Returns:
        dict: Summary of permissions
    """
    return {
        'is_admin': user.is_admin if user else False,
        'has_confidential_access': user.has_confidential_access if user else False,
        'is_ned_team': user.is_ned_team if user else False,
        'can_view_confidential': user.can_view_confidential() if user else False,
        'can_view_ned': user.can_view_ned_content() if user else False,
        'can_manage_users': user.can_manage_users() if user else False,
        'permission_level': get_permission_level_name(user)
    }


def get_permission_level_name(user):
    """
    Get a human-readable name for user's permission level

    Args:
        user: User object

    Returns:
        str: Permission level name
    """
    if not user or not user.is_authenticated:
        return "Not Authenticated"

    if user.is_admin:
        return "Administrator"

    parts = []
    if user.has_confidential_access:
        parts.append("Confidential Access")
    if user.is_ned_team:
        parts.append("NED Team")

    if parts:
        return " + ".join(parts)

    return "Standard User"


def check_entity_access(user, entity, action='view'):
    """
    Check if user can perform action on entity

    Args:
        user: User object
        entity: Entity object
        action: 'view', 'edit', 'delete'

    Returns:
        Boolean: True if action allowed
    """
    # Admins can do everything
    if user and user.is_admin:
        return True

    # For now, all authenticated users can view/edit public data
    # Extend this based on specific business rules
    if user and user.is_authenticated:
        return True

    return False


# =============================================================================
# QUERY HELPER FUNCTIONS
# =============================================================================

def apply_confidential_filter(query, user, relationship_class):
    """
    Apply confidentiality filter to a relationship query

    Args:
        query: SQLAlchemy query object
        user: User object
        relationship_class: The relationship model class

    Returns:
        SQLAlchemy query: Filtered query

    Examples:
        >>> query = db_session.query(ProjectVendorRelationship)
        >>> query = apply_confidential_filter(query, current_user, ProjectVendorRelationship)
    """
    # Admin and confidential users see everything
    if user and (user.is_admin or user.has_confidential_access):
        return query

    # Regular users only see non-confidential
    if hasattr(relationship_class, 'is_confidential'):
        query = query.filter_by(is_confidential=False)

    return query


def get_visible_relationships_for_entity(user, entity_type, entity_id, relationship_class):
    """
    Get all visible relationships for a specific entity

    Args:
        user: User object
        entity_type: Type of entity ('project', 'vendor', etc.)
        entity_id: ID of entity
        relationship_class: The relationship model class

    Returns:
        List: Visible relationships
    """
    db_session = get_db_session()

    # Build base query
    filter_field = f"{entity_type}_id"
    query = db_session.query(relationship_class).filter_by(**{filter_field: entity_id})

    # Apply confidential filter
    query = apply_confidential_filter(query, user, relationship_class)

    return query.all()
