#!/usr/bin/env python3
"""
Randomly assign Tier and Priority to all MPR clients for roundtable matrix testing.
"""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.company import Company, ClientProfile

TIERS = ['Tier 1', 'Tier 2', 'Tier 3', 'Tier 4']
PRIORITIES = ['High', 'Medium', 'Low']


def seed(db_path):
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        clients = session.query(Company).filter(Company.is_mpr_client == True).order_by(Company.company_name).all()

        if not clients:
            print('No MPR clients found.')
            return True

        print(f'Found {len(clients)} MPR clients. Assigning random Tier and Priority...\n')

        for company in clients:
            profile = company.client_profile
            if not profile:
                profile = ClientProfile(company_id=company.company_id)
                session.add(profile)

            tier = random.choice(TIERS)
            priority = random.choice(PRIORITIES)
            profile.client_tier = tier
            profile.client_priority = priority

            print(f'  {company.company_name:<40} {tier}  /  {priority}')

        session.commit()
        print(f'\nDone.')
        return True

    except Exception as e:
        session.rollback()
        print(f'[ERROR] {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == '__main__':
    import os

    db_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\jimbu\Coding Projects\NukeWorks\databases\dev_nukeworks.sqlite'

    if not os.path.exists(db_path):
        print(f'[ERROR] Database not found: {db_path}')
        sys.exit(1)

    success = seed(db_path)
    sys.exit(0 if success else 1)
