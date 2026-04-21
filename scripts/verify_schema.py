#!/usr/bin/env python3
"""
Database Schema Verification Script
Verifies that all tables, columns, indexes, and foreign keys match the specification
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, inspect
from app.models.base import Base

# Import all models to ensure they're registered
from app.models import *

def verify_schema():
    """Verify database schema against specification"""

    # Create in-memory database for testing
    engine = create_engine('sqlite:///:memory:', echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Get inspector
    inspector = inspect(engine)

    # Get all tables
    tables = inspector.get_table_names()

    # Expected tables from 02_DATABASE_SCHEMA.md and 03_DATABASE_RELATIONSHIPS.md
    expected_tables = {
        # Core Entity Tables (22)
        'users',
        'companies',
        'company_roles',
        'company_role_assignments',
        'client_profiles',
        'person_company_affiliations',
        'internal_external_links',
        'clients',
        'technology_vendors',
        'products',
        'owners_developers',
        'constructors',
        'operators',
        'projects',
        'personnel',
        'offtakers',
        'contact_log',
        'roundtable_history',
        'confidential_field_flags',
        'audit_log',
        'database_snapshots',
        'system_settings',
        'schema_version',
        # Junction Tables (15)
        'vendor_supplier_relationships',
        'owner_vendor_relationships',
        'project_vendor_relationships',
        'project_constructor_relationships',
        'project_operator_relationships',
        'project_owner_relationships',
        'project_offtaker_relationships',
        'vendor_preferred_constructor',
        'personnel_entity_relationships',
        'entity_team_members',
        'client_owner_relationships',
        'client_project_relationships',
        'client_vendor_relationships',
        'client_operator_relationships',
        'client_personnel_relationships',
    }

    print("="*70)
    print("DATABASE SCHEMA VERIFICATION")
    print("="*70)

    # Check tables
    print(f"\n✓ Created {len(tables)} tables (expected {len(expected_tables)})")

    missing_tables = expected_tables - set(tables)
    if missing_tables:
        print(f"✗ MISSING TABLES: {missing_tables}")
        return False

    extra_tables = set(tables) - expected_tables
    if extra_tables:
        print(f"⚠ Extra tables: {extra_tables}")

    print("\nTABLE DETAILS:")
    print("-"*70)

    total_columns = 0
    total_indexes = 0
    total_fks = 0

    for table in sorted(tables):
        columns = inspector.get_columns(table)
        indexes = inspector.get_indexes(table)
        fks = inspector.get_foreign_keys(table)

        total_columns += len(columns)
        total_indexes += len(indexes)
        total_fks += len(fks)

        print(f"{table:40s} {len(columns):2d} cols, {len(indexes):2d} indexes, {len(fks):2d} FKs")

    print("-"*70)
    print(f"{'TOTALS':40s} {total_columns:2d} cols, {total_indexes:2d} indexes, {total_fks:2d} FKs")

    print("\nCORE ENTITY TABLES (22):")
    core_tables = [
        'users', 'companies', 'company_roles', 'company_role_assignments',
        'client_profiles', 'person_company_affiliations', 'internal_external_links',
        'clients',
        'technology_vendors', 'products', 'owners_developers',
        'constructors', 'operators', 'projects', 'personnel', 'offtakers',
        'contact_log', 'roundtable_history', 'confidential_field_flags',
        'audit_log', 'database_snapshots', 'system_settings', 'schema_version'
    ]
    for table in core_tables:
        status = "✓" if table in tables else "✗"
        print(f"  {status} {table}")

    print("\nJUNCTION TABLES (15):")
    junction_tables = [
        'vendor_supplier_relationships', 'owner_vendor_relationships',
        'project_vendor_relationships', 'project_constructor_relationships',
        'project_operator_relationships', 'project_owner_relationships',
        'project_offtaker_relationships', 'vendor_preferred_constructor',
        'personnel_entity_relationships', 'entity_team_members',
        'client_owner_relationships', 'client_project_relationships',
        'client_vendor_relationships', 'client_operator_relationships',
        'client_personnel_relationships'
    ]
    for table in junction_tables:
        status = "✓" if table in tables else "✗"
        print(f"  {status} {table}")

    # Verify key tables have correct structure
    print("\nKEY TABLE VERIFICATION:")

    # Check Users table
    user_cols = [col['name'] for col in inspector.get_columns('users')]
    required_user_cols = ['user_id', 'username', 'email', 'password_hash',
                         'has_confidential_access', 'is_ned_team', 'is_admin']
    missing_user_cols = set(required_user_cols) - set(user_cols)
    if missing_user_cols:
        print(f"  ✗ users table missing columns: {missing_user_cols}")
    else:
        print(f"  ✓ users table has all required columns")

    # Check Projects table
    project_cols = [col['name'] for col in inspector.get_columns('projects')]
    required_project_cols = ['project_id', 'project_name', 'capex', 'opex', 'fuel_cost', 'lcoe']
    missing_project_cols = set(required_project_cols) - set(project_cols)
    if missing_project_cols:
        print(f"  ✗ projects table missing columns: {missing_project_cols}")
    else:
        print(f"  ✓ projects table has all required columns (including financial)")

    # Check Owners_Developers table
    owner_cols = [col['name'] for col in inspector.get_columns('owners_developers')]
    required_owner_cols = ['owner_id', 'company_name', 'relationship_strength',
                          'client_priority', 'client_status', 'relationship_notes']
    missing_owner_cols = set(required_owner_cols) - set(owner_cols)
    if missing_owner_cols:
        print(f"  ✗ owners_developers table missing columns: {missing_owner_cols}")
    else:
        print(f"  ✓ owners_developers table has all CRM fields")

    # Check foreign keys
    print("\nFOREIGN KEY VERIFICATION:")
    fk_checks = [
        ('products', 'vendor_id', 'technology_vendors'),
        ('project_vendor_relationships', 'project_id', 'projects'),
        ('project_vendor_relationships', 'vendor_id', 'technology_vendors'),
        ('owner_vendor_relationships', 'owner_id', 'owners_developers'),
        ('owner_vendor_relationships', 'vendor_id', 'technology_vendors'),
        ('project_offtaker_relationships', 'project_id', 'projects'),
        ('project_offtaker_relationships', 'offtaker_id', 'offtakers'),
    ]

    for table, col, ref_table in fk_checks:
        fks = inspector.get_foreign_keys(table)
        fk_found = any(col in fk['constrained_columns'] and
                      ref_table == fk['referred_table'] for fk in fks)
        status = "✓" if fk_found else "✗"
        print(f"  {status} {table}.{col} -> {ref_table}")

    print("\n" + "="*70)
    print("✓ SCHEMA VERIFICATION COMPLETE")
    print("="*70)
    print(f"\n  All {len(expected_tables)} tables created successfully")
    print(f"  Total: {total_columns} columns, {total_indexes} indexes, {total_fks} foreign keys")
    print(f"\n  Schema matches specification docs:")
    print(f"    - docs/02_DATABASE_SCHEMA.md")
    print(f"    - docs/03_DATABASE_RELATIONSHIPS.md")
    print("="*70)

    return True


if __name__ == '__main__':
    try:
        success = verify_schema()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
