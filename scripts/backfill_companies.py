"""Backfill unified company tables from legacy role-specific records."""
from __future__ import annotations

import argparse
import os
from typing import Optional

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app.models import (
    TechnologyVendor,
    OwnerDeveloper,
    Client,
    Operator,
    Constructor,
    Offtaker,
)
from app.services.company_sync import (
    sync_company_from_vendor,
    sync_company_from_owner,
    sync_company_from_client,
    sync_company_from_operator,
    sync_company_from_constructor,
    sync_company_from_offtaker,
)


def _process_records(query, sync_fn, label: str) -> int:
    count = 0
    for record in query:
        sync_fn(record, None)
        count += 1
    return count


def backfill(config_name: Optional[str] = None) -> None:
    flask_app = app_module.create_app(config_name)

    with flask_app.app_context():
        session = app_module.db_session
        total = 0

        vendors = session.query(TechnologyVendor).all()
        vendor_count = _process_records(vendors, sync_company_from_vendor, 'Vendors')
        total += vendor_count

        owners = session.query(OwnerDeveloper).all()
        owner_count = _process_records(owners, sync_company_from_owner, 'Owners/Developers')
        total += owner_count

        clients = session.query(Client).all()
        client_count = _process_records(clients, sync_company_from_client, 'Clients')
        total += client_count

        operators = session.query(Operator).all()
        operator_count = _process_records(operators, sync_company_from_operator, 'Operators')
        total += operator_count

        constructors = session.query(Constructor).all()
        constructor_count = _process_records(constructors, sync_company_from_constructor, 'Constructors')
        total += constructor_count

        offtakers = session.query(Offtaker).all()
        offtaker_count = _process_records(offtakers, sync_company_from_offtaker, 'Off-takers')
        total += offtaker_count

        session.commit()

        print('Backfill complete:')
        print(f'  Vendors        : {vendor_count}')
        print(f'  Owners         : {owner_count}')
        print(f'  Clients        : {client_count}')
        print(f'  Operators      : {operator_count}')
        print(f'  Constructors   : {constructor_count}')
        print(f'  Off-takers     : {offtaker_count}')
        print(f'  Total processed: {total}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Backfill unified company tables from legacy data.')
    parser.add_argument('--config', dest='config', default=os.environ.get('FLASK_ENV', 'development'),
                        help='Flask configuration name (default: from FLASK_ENV or development).')
    args = parser.parse_args()
    backfill(args.config)


if __name__ == '__main__':
    main()
