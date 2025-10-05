"""Backfill CompanyRoleAssignment from legacy project relationship records."""
from __future__ import annotations

import argparse
import os
from typing import Optional

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app.models import (
    ProjectVendorRelationship,
    ProjectConstructorRelationship,
    ProjectOperatorRelationship,
    ProjectOwnerRelationship,
    ProjectOfftakerRelationship,
)
from app.services.company_sync import (
    sync_project_vendor_relationship,
    sync_project_constructor_relationship,
    sync_project_operator_relationship,
    sync_project_owner_relationship,
    sync_project_offtaker_relationship,
)


def backfill(config_name: Optional[str] = None) -> None:
    flask_app = app_module.create_app(config_name)

    with flask_app.app_context():
        session = app_module.db_session

        # Vendor relationships
        vendor_rels = session.query(ProjectVendorRelationship).all()
        vendor_synced = 0
        vendor_skipped = 0
        for rel in vendor_rels:
            result = sync_project_vendor_relationship(rel, None)
            if result:
                vendor_synced += 1
            else:
                vendor_skipped += 1

        # Constructor relationships
        constructor_rels = session.query(ProjectConstructorRelationship).all()
        constructor_synced = 0
        constructor_skipped = 0
        for rel in constructor_rels:
            result = sync_project_constructor_relationship(rel, None)
            if result:
                constructor_synced += 1
            else:
                constructor_skipped += 1

        # Operator relationships
        operator_rels = session.query(ProjectOperatorRelationship).all()
        operator_synced = 0
        operator_skipped = 0
        for rel in operator_rels:
            result = sync_project_operator_relationship(rel, None)
            if result:
                operator_synced += 1
            else:
                operator_skipped += 1

        # Owner relationships
        owner_rels = session.query(ProjectOwnerRelationship).all()
        owner_synced = 0
        owner_skipped = 0
        for rel in owner_rels:
            result = sync_project_owner_relationship(rel, None)
            if result:
                owner_synced += 1
            else:
                owner_skipped += 1

        # Offtaker relationships
        offtaker_rels = session.query(ProjectOfftakerRelationship).all()
        offtaker_synced = 0
        offtaker_skipped = 0
        for rel in offtaker_rels:
            result = sync_project_offtaker_relationship(rel, None)
            if result:
                offtaker_synced += 1
            else:
                offtaker_skipped += 1

        session.commit()

        print('Project relationship backfill complete:')
        print(f'  Vendor relationships     : {len(vendor_rels)} total, {vendor_synced} synced, {vendor_skipped} skipped')
        print(f'  Constructor relationships: {len(constructor_rels)} total, {constructor_synced} synced, {constructor_skipped} skipped')
        print(f'  Operator relationships   : {len(operator_rels)} total, {operator_synced} synced, {operator_skipped} skipped')
        print(f'  Owner relationships      : {len(owner_rels)} total, {owner_synced} synced, {owner_skipped} skipped')
        print(f'  Offtaker relationships   : {len(offtaker_rels)} total, {offtaker_synced} synced, {offtaker_skipped} skipped')
        print(f'  Total synced             : {vendor_synced + constructor_synced + operator_synced + owner_synced + offtaker_synced}')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Backfill CompanyRoleAssignment from legacy project relationship records.'
    )
    parser.add_argument('--config', dest='config', default=os.environ.get('FLASK_ENV', 'development'),
                        help='Flask configuration name (default: from FLASK_ENV or development).')
    args = parser.parse_args()
    backfill(args.config)


if __name__ == '__main__':
    main()
