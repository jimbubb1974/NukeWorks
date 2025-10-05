"""Backfill PersonCompanyAffiliation from legacy PersonnelEntityRelationship records."""
from __future__ import annotations

import argparse
import os
from typing import Optional

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app.models import PersonnelEntityRelationship
from app.services.company_sync import sync_personnel_affiliation


def backfill(config_name: Optional[str] = None) -> None:
    flask_app = app_module.create_app(config_name)

    with flask_app.app_context():
        session = app_module.db_session

        # Get all personnel entity relationships
        personnel_relationships = session.query(PersonnelEntityRelationship).all()

        synced_count = 0
        skipped_count = 0

        for rel in personnel_relationships:
            result = sync_personnel_affiliation(rel, None)
            if result:
                synced_count += 1
            else:
                skipped_count += 1
                print(f"Skipped: {rel.entity_type} ID {rel.entity_id} (company not found)")

        session.commit()

        print('Personnel affiliation backfill complete:')
        print(f'  Total relationships processed: {len(personnel_relationships)}')
        print(f'  Synced to unified schema     : {synced_count}')
        print(f'  Skipped (no company found)   : {skipped_count}')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Backfill PersonCompanyAffiliation from legacy PersonnelEntityRelationship records.'
    )
    parser.add_argument('--config', dest='config', default=os.environ.get('FLASK_ENV', 'development'),
                        help='Flask configuration name (default: from FLASK_ENV or development).')
    args = parser.parse_args()
    backfill(args.config)


if __name__ == '__main__':
    main()
