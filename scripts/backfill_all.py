"""Master backfill script - runs all company unification backfills in correct order."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app.models import (
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
from app.services.company_sync import (
    sync_company_from_vendor,
    sync_company_from_owner,
    sync_company_from_client,
    sync_company_from_operator,
    sync_company_from_constructor,
    sync_company_from_offtaker,
    sync_personnel_affiliation,
    sync_project_vendor_relationship,
    sync_project_constructor_relationship,
    sync_project_operator_relationship,
    sync_project_owner_relationship,
    sync_project_offtaker_relationship,
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print('\n' + '=' * 80)
    print(f'  {title}')
    print('=' * 80)


def backfill_companies(session, dry_run: bool = False) -> dict:
    """Backfill base company records."""
    print_section('Step 1: Backfill Base Company Records')

    results = {}

    # Vendors
    vendors = session.query(TechnologyVendor).all()
    print(f'Processing {len(vendors)} vendors...')
    for vendor in vendors:
        if not dry_run:
            sync_company_from_vendor(vendor, None)
    results['vendors'] = len(vendors)

    # Owners/Developers
    owners = session.query(OwnerDeveloper).all()
    print(f'Processing {len(owners)} owners/developers...')
    for owner in owners:
        if not dry_run:
            sync_company_from_owner(owner, None)
    results['owners'] = len(owners)

    # Clients
    clients = session.query(Client).all()
    print(f'Processing {len(clients)} clients...')
    for client in clients:
        if not dry_run:
            sync_company_from_client(client, None)
    results['clients'] = len(clients)

    # Operators
    operators = session.query(Operator).all()
    print(f'Processing {len(operators)} operators...')
    for operator in operators:
        if not dry_run:
            sync_company_from_operator(operator, None)
    results['operators'] = len(operators)

    # Constructors
    constructors = session.query(Constructor).all()
    print(f'Processing {len(constructors)} constructors...')
    for constructor in constructors:
        if not dry_run:
            sync_company_from_constructor(constructor, None)
    results['constructors'] = len(constructors)

    # Offtakers
    offtakers = session.query(Offtaker).all()
    print(f'Processing {len(offtakers)} offtakers...')
    for offtaker in offtakers:
        if not dry_run:
            sync_company_from_offtaker(offtaker, None)
    results['offtakers'] = len(offtakers)

    if not dry_run:
        session.flush()

    print(f'\nCompany backfill complete:')
    print(f'  Vendors:       {results["vendors"]}')
    print(f'  Owners:        {results["owners"]}')
    print(f'  Clients:       {results["clients"]}')
    print(f'  Operators:     {results["operators"]}')
    print(f'  Constructors:  {results["constructors"]}')
    print(f'  Offtakers:     {results["offtakers"]}')
    print(f'  Total:         {sum(results.values())}')

    return results


def backfill_personnel_affiliations(session, dry_run: bool = False) -> dict:
    """Backfill personnel-company affiliations."""
    print_section('Step 2: Backfill Personnel Affiliations')

    personnel_rels = session.query(PersonnelEntityRelationship).all()
    print(f'Processing {len(personnel_rels)} personnel-entity relationships...')

    synced = 0
    skipped = 0

    for rel in personnel_rels:
        if not dry_run:
            result = sync_personnel_affiliation(rel, None)
            if result:
                synced += 1
            else:
                skipped += 1
        else:
            synced += 1

    if not dry_run:
        session.flush()

    print(f'\nPersonnel affiliation backfill complete:')
    print(f'  Total relationships: {len(personnel_rels)}')
    print(f'  Synced:             {synced}')
    print(f'  Skipped:            {skipped}')

    return {'total': len(personnel_rels), 'synced': synced, 'skipped': skipped}


def backfill_project_relationships(session, dry_run: bool = False) -> dict:
    """Backfill project-company relationships."""
    print_section('Step 3: Backfill Project Relationships')

    results = {}

    # Vendor relationships
    vendor_rels = session.query(ProjectVendorRelationship).all()
    print(f'Processing {len(vendor_rels)} project-vendor relationships...')
    vendor_synced = 0
    for rel in vendor_rels:
        if not dry_run:
            if sync_project_vendor_relationship(rel, None):
                vendor_synced += 1
        else:
            vendor_synced += 1
    results['vendor'] = {'total': len(vendor_rels), 'synced': vendor_synced}

    # Constructor relationships
    constructor_rels = session.query(ProjectConstructorRelationship).all()
    print(f'Processing {len(constructor_rels)} project-constructor relationships...')
    constructor_synced = 0
    for rel in constructor_rels:
        if not dry_run:
            if sync_project_constructor_relationship(rel, None):
                constructor_synced += 1
        else:
            constructor_synced += 1
    results['constructor'] = {'total': len(constructor_rels), 'synced': constructor_synced}

    # Operator relationships
    operator_rels = session.query(ProjectOperatorRelationship).all()
    print(f'Processing {len(operator_rels)} project-operator relationships...')
    operator_synced = 0
    for rel in operator_rels:
        if not dry_run:
            if sync_project_operator_relationship(rel, None):
                operator_synced += 1
        else:
            operator_synced += 1
    results['operator'] = {'total': len(operator_rels), 'synced': operator_synced}

    # Owner relationships
    owner_rels = session.query(ProjectOwnerRelationship).all()
    print(f'Processing {len(owner_rels)} project-owner relationships...')
    owner_synced = 0
    for rel in owner_rels:
        if not dry_run:
            if sync_project_owner_relationship(rel, None):
                owner_synced += 1
        else:
            owner_synced += 1
    results['owner'] = {'total': len(owner_rels), 'synced': owner_synced}

    # Offtaker relationships
    offtaker_rels = session.query(ProjectOfftakerRelationship).all()
    print(f'Processing {len(offtaker_rels)} project-offtaker relationships...')
    offtaker_synced = 0
    for rel in offtaker_rels:
        if not dry_run:
            if sync_project_offtaker_relationship(rel, None):
                offtaker_synced += 1
        else:
            offtaker_synced += 1
    results['offtaker'] = {'total': len(offtaker_rels), 'synced': offtaker_synced}

    if not dry_run:
        session.flush()

    print(f'\nProject relationship backfill complete:')
    for rel_type, stats in results.items():
        print(f'  {rel_type.capitalize()}: {stats["synced"]}/{stats["total"]} synced')

    total_synced = sum(r['synced'] for r in results.values())
    total_rels = sum(r['total'] for r in results.values())
    print(f'  Total: {total_synced}/{total_rels} synced')

    return results


def run_backfill(config_name: str = None, dry_run: bool = False) -> None:
    """Run complete backfill process."""
    flask_app = app_module.create_app(config_name)

    with flask_app.app_context():
        session = app_module.db_session

        start_time = datetime.now()

        print('=' * 80)
        print('  COMPANY UNIFICATION BACKFILL')
        print('=' * 80)
        print(f'Environment: {config_name or "development"}')
        print(f'Mode: {"DRY RUN (no changes will be saved)" if dry_run else "LIVE"}')
        print(f'Started: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')

        # Step 1: Backfill base company records
        company_results = backfill_companies(session, dry_run)

        # Step 2: Backfill personnel affiliations
        personnel_results = backfill_personnel_affiliations(session, dry_run)

        # Step 3: Backfill project relationships
        project_results = backfill_project_relationships(session, dry_run)

        # Commit or rollback
        if dry_run:
            print_section('Dry Run Complete - Rolling Back')
            session.rollback()
        else:
            print_section('Committing Changes')
            session.commit()
            print('Changes committed successfully.')

        end_time = datetime.now()
        duration = end_time - start_time

        print_section('Summary')
        print(f'Completed: {end_time.strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'Duration: {duration}')
        print(f'\nBase Companies: {sum(company_results.values())} processed')
        print(f'Personnel Affiliations: {personnel_results["synced"]}/{personnel_results["total"]} synced')

        total_project_synced = sum(r['synced'] for r in project_results.values())
        total_project_rels = sum(r['total'] for r in project_results.values())
        print(f'Project Relationships: {total_project_synced}/{total_project_rels} synced')

        if dry_run:
            print('\n⚠️  DRY RUN - No changes were saved to the database.')
        else:
            print('\n✓ Backfill complete - all changes saved.')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Run complete company unification backfill (companies, personnel, projects).'
    )
    parser.add_argument(
        '--config',
        dest='config',
        default=os.environ.get('FLASK_ENV', 'development'),
        help='Flask configuration name (default: from FLASK_ENV or development).'
    )
    parser.add_argument(
        '--dry-run',
        dest='dry_run',
        action='store_true',
        help='Run in dry-run mode (no changes will be saved).'
    )
    args = parser.parse_args()

    run_backfill(args.config, args.dry_run)


if __name__ == '__main__':
    main()
