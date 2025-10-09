"""Validation script to verify company unification migration integrity."""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app.models import (
    Company,
    CompanyRole,
    CompanyRoleAssignment,
    PersonCompanyAffiliation,
    TechnologyVendor,
    OwnerDeveloper,
    Client,
    Operator,
    Constructor,
    Offtaker,
    PersonnelEntityRelationship,
    ProjectVendorRelationship,
    ProjectConstructorRelationship,
    ProjectOperatorRelationship,
    ProjectOwnerRelationship,
    ProjectOfftakerRelationship,
)


def print_section(title: str) -> None:
    """Print formatted section header."""
    print('\n' + '=' * 80)
    print(f'  {title}')
    print('=' * 80)


def check_company_coverage(session) -> dict:
    """Check that all legacy entities have corresponding company records."""
    print_section('Company Coverage Check')

    issues = []
    stats = {}

    # Get roles
    vendor_role = session.query(CompanyRole).filter(CompanyRole.role_code == 'vendor').first()
    owner_role = session.query(CompanyRole).filter(CompanyRole.role_code == 'developer').first()
    client_role = session.query(CompanyRole).filter(CompanyRole.role_code == 'client').first()
    operator_role = session.query(CompanyRole).filter(CompanyRole.role_code == 'operator').first()
    constructor_role = session.query(CompanyRole).filter(CompanyRole.role_code == 'constructor').first()
    offtaker_role = session.query(CompanyRole).filter(CompanyRole.role_code == 'offtaker').first()

    # Check vendors
    vendors = session.query(TechnologyVendor).all()
    vendor_missing = []
    if vendor_role:
        for vendor in vendors:
            assignment = session.query(CompanyRoleAssignment).filter_by(
                role_id=vendor_role.role_id,
                context_type='VendorRecord',
                context_id=vendor.vendor_id
            ).first()
            if not assignment:
                vendor_missing.append(vendor.vendor_name)

    stats['vendors'] = {'total': len(vendors), 'missing': len(vendor_missing)}
    if vendor_missing:
        issues.append(f'Missing {len(vendor_missing)} vendor companies')

    # Check owners
    owners = session.query(OwnerDeveloper).all()
    owner_missing = []
    if owner_role:
        for owner in owners:
            assignment = session.query(CompanyRoleAssignment).filter_by(
                role_id=owner_role.role_id,
                context_type='OwnerRecord',
                context_id=owner.owner_id
            ).first()
            if not assignment:
                owner_missing.append(owner.company_name)

    stats['owners'] = {'total': len(owners), 'missing': len(owner_missing)}
    if owner_missing:
        issues.append(f'Missing {len(owner_missing)} owner companies')

    # Check clients
    clients = session.query(Client).all()
    client_missing = []
    if client_role:
        for client in clients:
            assignment = session.query(CompanyRoleAssignment).filter_by(
                role_id=client_role.role_id,
                context_type='ClientRecord',
                context_id=client.client_id
            ).first()
            if not assignment:
                client_missing.append(client.client_name)

    stats['clients'] = {'total': len(clients), 'missing': len(client_missing)}
    if client_missing:
        issues.append(f'Missing {len(client_missing)} client companies')

    # Check operators
    operators = session.query(Operator).all()
    operator_missing = []
    if operator_role:
        for operator in operators:
            assignment = session.query(CompanyRoleAssignment).filter_by(
                role_id=operator_role.role_id,
                context_type='OperatorRecord',
                context_id=operator.operator_id
            ).first()
            if not assignment:
                operator_missing.append(operator.company_name)

    stats['operators'] = {'total': len(operators), 'missing': len(operator_missing)}
    if operator_missing:
        issues.append(f'Missing {len(operator_missing)} operator companies')

    # Check constructors
    constructors = session.query(Constructor).all()
    constructor_missing = []
    if constructor_role:
        for constructor in constructors:
            assignment = session.query(CompanyRoleAssignment).filter_by(
                role_id=constructor_role.role_id,
                context_type='ConstructorRecord',
                context_id=constructor.constructor_id
            ).first()
            if not assignment:
                constructor_missing.append(constructor.company_name)

    stats['constructors'] = {'total': len(constructors), 'missing': len(constructor_missing)}
    if constructor_missing:
        issues.append(f'Missing {len(constructor_missing)} constructor companies')

    # Check offtakers
    offtakers = session.query(Offtaker).all()
    offtaker_missing = []
    if offtaker_role:
        for offtaker in offtakers:
            assignment = session.query(CompanyRoleAssignment).filter_by(
                role_id=offtaker_role.role_id,
                context_type='OfftakerRecord',
                context_id=offtaker.offtaker_id
            ).first()
            if not assignment:
                offtaker_missing.append(offtaker.organization_name)

    stats['offtakers'] = {'total': len(offtakers), 'missing': len(offtaker_missing)}
    if offtaker_missing:
        issues.append(f'Missing {len(offtaker_missing)} offtaker companies')

    # Print results
    print(f'Vendors:      {stats["vendors"]["total"]} total, {stats["vendors"]["missing"]} missing')
    print(f'Owners:       {stats["owners"]["total"]} total, {stats["owners"]["missing"]} missing')
    print(f'Clients:      {stats["clients"]["total"]} total, {stats["clients"]["missing"]} missing')
    print(f'Operators:    {stats["operators"]["total"]} total, {stats["operators"]["missing"]} missing')
    print(f'Constructors: {stats["constructors"]["total"]} total, {stats["constructors"]["missing"]} missing')
    print(f'Offtakers:    {stats["offtakers"]["total"]} total, {stats["offtakers"]["missing"]} missing')

    if not issues:
        print('\n[SUCCESS] All legacy entities have corresponding company records')

    return {'stats': stats, 'issues': issues}


def check_duplicate_companies(session) -> dict:
    """Check for duplicate company names."""
    print_section('Duplicate Company Name Check')

    companies = session.query(Company).all()
    name_counts = defaultdict(list)

    for company in companies:
        name_counts[company.company_name.lower().strip()].append(company)

    duplicates = {name: comps for name, comps in name_counts.items() if len(comps) > 1}

    if duplicates:
        print(f'Found {len(duplicates)} duplicate company names:')
        for name, comps in duplicates.items():
            print(f'\n  "{name}" ({len(comps)} instances):')
            for comp in comps:
                roles = session.query(CompanyRoleAssignment).filter_by(company_id=comp.company_id).all()
                role_names = [r.role.role_code if r.role else 'unknown' for r in roles]
                print(f'    - ID {comp.company_id}: roles={role_names}, type={comp.company_type}')
    else:
        print('[SUCCESS] No duplicate company names found')

    return {'duplicates': duplicates}


def check_project_relationship_coverage(session) -> dict:
    """Check that project relationships are synced to unified schema."""
    print_section('Project Relationship Coverage Check')

    issues = []
    stats = {}

    # Vendor relationships
    vendor_rels = session.query(ProjectVendorRelationship).all()
    vendor_synced = 0
    for rel in vendor_rels:
        unified = session.query(CompanyRoleAssignment).filter_by(
            context_type='Project',
            context_id=rel.project_id
        ).join(CompanyRole).filter(CompanyRole.role_code == 'vendor').first()
        if unified:
            vendor_synced += 1

    stats['vendor'] = {'total': len(vendor_rels), 'synced': vendor_synced}

    # Constructor relationships
    constructor_rels = session.query(ProjectConstructorRelationship).all()
    constructor_synced = 0
    for rel in constructor_rels:
        unified = session.query(CompanyRoleAssignment).filter_by(
            context_type='Project',
            context_id=rel.project_id
        ).join(CompanyRole).filter(CompanyRole.role_code == 'constructor').first()
        if unified:
            constructor_synced += 1

    stats['constructor'] = {'total': len(constructor_rels), 'synced': constructor_synced}

    # Operator relationships
    operator_rels = session.query(ProjectOperatorRelationship).all()
    operator_synced = 0
    for rel in operator_rels:
        unified = session.query(CompanyRoleAssignment).filter_by(
            context_type='Project',
            context_id=rel.project_id
        ).join(CompanyRole).filter(CompanyRole.role_code == 'operator').first()
        if unified:
            operator_synced += 1

    stats['operator'] = {'total': len(operator_rels), 'synced': operator_synced}

    # Owner relationships
    owner_rels = session.query(ProjectOwnerRelationship).all()
    owner_synced = 0
    for rel in owner_rels:
        unified = session.query(CompanyRoleAssignment).filter_by(
            context_type='Project',
            context_id=rel.project_id
        ).join(CompanyRole).filter(CompanyRole.role_code == 'developer').first()
        if unified:
            owner_synced += 1

    stats['owner'] = {'total': len(owner_rels), 'synced': owner_synced}

    # Offtaker relationships
    offtaker_rels = session.query(ProjectOfftakerRelationship).all()
    offtaker_synced = 0
    for rel in offtaker_rels:
        unified = session.query(CompanyRoleAssignment).filter_by(
            context_type='Project',
            context_id=rel.project_id
        ).join(CompanyRole).filter(CompanyRole.role_code == 'offtaker').first()
        if unified:
            offtaker_synced += 1

    stats['offtaker'] = {'total': len(offtaker_rels), 'synced': offtaker_synced}

    # Print results
    for rel_type, data in stats.items():
        coverage = (data['synced'] / data['total'] * 100) if data['total'] > 0 else 100
        print(f'{rel_type.capitalize()}: {data["synced"]}/{data["total"]} ({coverage:.1f}%)')
        if data['synced'] < data['total']:
            issues.append(f'{rel_type}: {data["total"] - data["synced"]} not synced')

    if not issues:
        print('\n[SUCCESS] All project relationships synced')

    return {'stats': stats, 'issues': issues}


def check_personnel_affiliations(session) -> dict:
    """Check personnel affiliation coverage."""
    print_section('Personnel Affiliation Coverage Check')

    personnel_rels = session.query(PersonnelEntityRelationship).all()

    # Filter for company-related entities (not projects)
    company_entity_types = ['Vendor', 'Owner', 'Developer', 'Operator', 'Constructor', 'Offtaker', 'Client']
    company_rels = [r for r in personnel_rels if r.entity_type in company_entity_types]

    affiliations = session.query(PersonCompanyAffiliation).all()

    print(f'Total personnel-entity relationships: {len(personnel_rels)}')
    print(f'Company-related relationships: {len(company_rels)}')
    print(f'PersonCompanyAffiliation records: {len(affiliations)}')

    coverage = (len(affiliations) / len(company_rels) * 100) if len(company_rels) > 0 else 100
    print(f'Coverage: {coverage:.1f}%')

    issues = []
    if len(affiliations) < len(company_rels):
        issues.append(f'{len(company_rels) - len(affiliations)} personnel affiliations not migrated')
    else:
        print('\n[SUCCESS] Personnel affiliations migrated')

    return {'company_rels': len(company_rels), 'affiliations': len(affiliations), 'issues': issues}


def run_validation(config_name: str = None) -> None:
    """Run complete validation suite."""
    flask_app = app_module.create_app(config_name)

    with flask_app.app_context():
        session = app_module.db_session

        print('=' * 80)
        print('  COMPANY UNIFICATION MIGRATION VALIDATION')
        print('=' * 80)
        print(f'Environment: {config_name or "development"}')

        all_issues = []

        # Check 1: Company coverage
        company_check = check_company_coverage(session)
        all_issues.extend(company_check['issues'])

        # Check 2: Duplicates
        duplicate_check = check_duplicate_companies(session)

        # Check 3: Project relationships
        project_check = check_project_relationship_coverage(session)
        all_issues.extend(project_check['issues'])

        # Check 4: Personnel affiliations
        personnel_check = check_personnel_affiliations(session)
        all_issues.extend(personnel_check['issues'])

        # Final summary
        print_section('Validation Summary')

        if not all_issues and not duplicate_check['duplicates']:
            print('[SUCCESS] All validation checks passed!')
            print('  - All legacy entities have company records')
            print('  - No duplicate company names')
            print('  - All project relationships synced')
            print('  - All personnel affiliations migrated')
        else:
            print('[WARNING] Issues found:')
            if all_issues:
                for issue in all_issues:
                    print(f'  - {issue}')
            if duplicate_check['duplicates']:
                print(f'  - {len(duplicate_check["duplicates"])} duplicate company names (review above)')
            print('\nRun backfill scripts to resolve missing data.')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Validate company unification migration integrity.'
    )
    parser.add_argument(
        '--config',
        dest='config',
        default=os.environ.get('FLASK_ENV', 'development'),
        help='Flask configuration name (default: from FLASK_ENV or development).'
    )
    args = parser.parse_args()

    run_validation(args.config)


if __name__ == '__main__':
    main()
