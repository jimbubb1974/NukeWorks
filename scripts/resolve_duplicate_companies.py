"""Utility to identify and resolve duplicate company records."""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app.models import Company, CompanyRoleAssignment, PersonCompanyAffiliation


def normalize_name(name: str) -> str:
    """Normalize company name for comparison."""
    return name.lower().strip()


def find_duplicates(session) -> dict:
    """Find all companies with duplicate names."""
    companies = session.query(Company).all()
    name_map = defaultdict(list)

    for company in companies:
        normalized = normalize_name(company.company_name)
        name_map[normalized].append(company)

    # Filter to only duplicates
    duplicates = {name: comps for name, comps in name_map.items() if len(comps) > 1}
    return duplicates


def analyze_company(session, company: Company) -> dict:
    """Analyze a company record to understand its usage."""
    role_assignments = session.query(CompanyRoleAssignment).filter_by(
        company_id=company.company_id
    ).all()

    affiliations = session.query(PersonCompanyAffiliation).filter_by(
        company_id=company.company_id
    ).all()

    # Group assignments by context
    contexts = defaultdict(list)
    for assignment in role_assignments:
        key = f"{assignment.context_type}:{assignment.context_id}" if assignment.context_id else "Global"
        contexts[key].append({
            'role': assignment.role.role_code if assignment.role else 'unknown',
            'is_primary': assignment.is_primary,
            'is_confidential': assignment.is_confidential,
        })

    return {
        'company_id': company.company_id,
        'company_name': company.company_name,
        'company_type': company.company_type,
        'is_mpr_client': company.is_mpr_client,
        'role_assignments': len(role_assignments),
        'affiliations': len(affiliations),
        'contexts': dict(contexts),
        'created_date': company.created_date,
        'modified_date': company.modified_date,
    }


def print_duplicate_group(session, name: str, companies: List[Company]) -> None:
    """Print detailed analysis of a duplicate group."""
    print(f'\n{"=" * 80}')
    print(f'Duplicate Name: "{companies[0].company_name}"')
    print(f'Normalized: "{name}"')
    print(f'Instances: {len(companies)}')
    print('=' * 80)

    for i, company in enumerate(companies, 1):
        analysis = analyze_company(session, company)
        print(f'\n[{i}] Company ID: {analysis["company_id"]}')
        print(f'    Type: {analysis["company_type"] or "Not set"}')
        print(f'    MPR Client: {analysis["is_mpr_client"]}')
        print(f'    Role Assignments: {analysis["role_assignments"]}')
        print(f'    Personnel Affiliations: {analysis["affiliations"]}')
        print(f'    Created: {analysis["created_date"]}')
        print(f'    Modified: {analysis["modified_date"]}')

        if analysis['contexts']:
            print(f'    Contexts:')
            for context, roles in analysis['contexts'].items():
                role_str = ', '.join([r['role'] for r in roles])
                print(f'      - {context}: {role_str}')


def suggest_merge_strategy(companies: List[dict]) -> dict:
    """Suggest which company should be kept and which merged."""
    # Score each company based on:
    # 1. Number of role assignments (higher = more important)
    # 2. Number of affiliations (higher = more important)
    # 3. Is MPR client (yes = more important)
    # 4. Created date (earlier = potentially more important)

    scored = []
    for comp in companies:
        score = 0
        score += comp['role_assignments'] * 10
        score += comp['affiliations'] * 5
        score += 20 if comp['is_mpr_client'] else 0
        # Earlier creation = small bonus
        if comp['created_date']:
            days_old = (comp['created_date'] - companies[0]['created_date']).days
            score += max(0, 10 - abs(days_old))

        scored.append({'company': comp, 'score': score})

    # Sort by score descending
    scored.sort(key=lambda x: x['score'], reverse=True)

    return {
        'keep': scored[0]['company'],
        'merge_from': [s['company'] for s in scored[1:]],
        'reasoning': f"Keep ID {scored[0]['company']['company_id']} (score: {scored[0]['score']}) - "
                     f"has most relationships and context"
    }


def merge_companies(session, keep_id: int, merge_ids: List[int], dry_run: bool = True) -> dict:
    """
    Merge companies by reassigning all relationships to the kept company.

    Args:
        session: Database session
        keep_id: Company ID to keep
        merge_ids: List of company IDs to merge into keep_id
        dry_run: If True, don't actually make changes

    Returns:
        Dictionary with merge statistics
    """
    stats = {
        'role_assignments_moved': 0,
        'affiliations_moved': 0,
        'companies_deleted': 0,
    }

    for merge_id in merge_ids:
        # Move role assignments
        assignments = session.query(CompanyRoleAssignment).filter_by(
            company_id=merge_id
        ).all()

        for assignment in assignments:
            # Check if equivalent assignment exists
            existing = session.query(CompanyRoleAssignment).filter_by(
                company_id=keep_id,
                role_id=assignment.role_id,
                context_type=assignment.context_type,
                context_id=assignment.context_id,
            ).first()

            if existing:
                # Duplicate assignment, just delete the old one
                if not dry_run:
                    session.delete(assignment)
            else:
                # Move to kept company
                if not dry_run:
                    assignment.company_id = keep_id
                stats['role_assignments_moved'] += 1

        # Move affiliations
        affiliations = session.query(PersonCompanyAffiliation).filter_by(
            company_id=merge_id
        ).all()

        for affiliation in affiliations:
            # Check if equivalent affiliation exists
            existing = session.query(PersonCompanyAffiliation).filter_by(
                person_id=affiliation.person_id,
                company_id=keep_id,
                title=affiliation.title,
            ).first()

            if existing:
                # Duplicate, delete old one
                if not dry_run:
                    session.delete(affiliation)
            else:
                # Move to kept company
                if not dry_run:
                    affiliation.company_id = keep_id
                stats['affiliations_moved'] += 1

        # Delete the merged company
        if not dry_run:
            company = session.get(Company, merge_id)
            if company:
                session.delete(company)
        stats['companies_deleted'] += 1

    if not dry_run:
        session.flush()

    return stats


def interactive_resolution(session) -> None:
    """Interactive mode to resolve duplicates."""
    duplicates = find_duplicates(session)

    if not duplicates:
        print('No duplicate companies found!')
        return

    print(f'\nFound {len(duplicates)} sets of duplicate companies.\n')

    for name, companies in duplicates.items():
        print_duplicate_group(session, name, companies)

        analyses = [analyze_company(session, c) for c in companies]
        suggestion = suggest_merge_strategy(analyses)

        print(f'\n{"-" * 80}')
        print('SUGGESTED ACTION:')
        print(f'  {suggestion["reasoning"]}')
        print(f'\n  Keep: Company ID {suggestion["keep"]["company_id"]}')
        print(f'  Merge: Company IDs {[c["company_id"] for c in suggestion["merge_from"]]}')
        print('-' * 80)

        response = input('\nAction? [(s)kip, (m)erge as suggested, (c)ustom, (q)uit]: ').lower().strip()

        if response == 'q':
            print('Exiting.')
            break
        elif response == 's':
            print('Skipped.\n')
            continue
        elif response == 'm':
            print(f'\nMerging companies...')
            stats = merge_companies(
                session,
                suggestion['keep']['company_id'],
                [c['company_id'] for c in suggestion['merge_from']],
                dry_run=False
            )
            print(f"  Role assignments moved: {stats['role_assignments_moved']}")
            print(f"  Affiliations moved: {stats['affiliations_moved']}")
            print(f"  Companies deleted: {stats['companies_deleted']}")
            session.commit()
            print('✓ Merge complete.')
        elif response == 'c':
            print('Custom merge not yet implemented. Use (s)kip for now.')
        else:
            print('Invalid option. Skipping.')


def run_duplicate_report(session) -> None:
    """Generate a report of all duplicates without interactive resolution."""
    duplicates = find_duplicates(session)

    if not duplicates:
        print('No duplicate companies found!')
        return

    print(f'Found {len(duplicates)} sets of duplicate companies:')

    for name, companies in duplicates.items():
        print_duplicate_group(session, name, companies)
        analyses = [analyze_company(session, c) for c in companies]
        suggestion = suggest_merge_strategy(analyses)
        print(f'\n  SUGGESTION: {suggestion["reasoning"]}\n')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Identify and resolve duplicate company records.'
    )
    parser.add_argument(
        '--config',
        dest='config',
        default=os.environ.get('FLASK_ENV', 'development'),
        help='Flask configuration name (default: from FLASK_ENV or development).'
    )
    parser.add_argument(
        '--interactive',
        dest='interactive',
        action='store_true',
        help='Run in interactive mode to resolve duplicates.'
    )
    args = parser.parse_args()

    flask_app = app_module.create_app(args.config)

    with flask_app.app_context():
        session = app_module.db_session

        print('=' * 80)
        print('  DUPLICATE COMPANY RESOLUTION')
        print('=' * 80)
        print(f'Environment: {args.config or "development"}')

        if args.interactive:
            print('Mode: Interactive')
            print('\nWARNING: This will modify the database. Make sure you have a backup!')
            confirm = input('Continue? [y/N]: ').lower().strip()
            if confirm != 'y':
                print('Cancelled.')
                return
            interactive_resolution(session)
        else:
            print('Mode: Report Only')
            run_duplicate_report(session)


if __name__ == '__main__':
    main()
