#!/usr/bin/env python3
"""
Add test encrypted data to demonstrate encryption working
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.project import Project
from app.models.company import ClientProfile
from app.models.roundtable import RoundtableHistory


def add_test_data(db_path):
    """Add encrypted test data to database"""

    print("=" * 70)
    print("ADDING TEST ENCRYPTED DATA")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()

    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get first project
        project = session.query(Project).first()

        if project:
            print(f"[PROJECT] {project.project_name}")

            # Add confidential financial data using encrypted fields
            project.capex = '5000000'  # $5 million
            project.opex = '500000'    # $500k per year
            project.fuel_cost = '10000'  # $10k
            project.lcoe = '0.085'      # 8.5 cents per kWh

            print("  Added encrypted financial data:")
            print(f"    CAPEX: $5,000,000")
            print(f"    OPEX: $500,000")
            print(f"    Fuel Cost: $10,000")
            print(f"    LCOE: $0.085/kWh")
            print()

        # Get first client profile
        client = session.query(ClientProfile).first()

        if client:
            print(f"[CLIENT PROFILE] Company ID: {client.company_id}")

            # Add NED Team encrypted data
            client.relationship_strength = 'Strong'
            client.relationship_notes = 'Excellent relationship with key decision makers. Regular quarterly meetings.'
            client.client_priority = 'High'
            client.client_status = 'Active'

            print("  Added encrypted CRM data:")
            print(f"    Relationship Strength: Strong")
            print(f"    Priority: High")
            print(f"    Status: Active")
            print()

        # Get first roundtable entry (or create one)
        roundtable = session.query(RoundtableHistory).first()

        if roundtable:
            print(f"[ROUNDTABLE] Entry ID: {roundtable.history_id}")

            # Add NED Team encrypted notes
            roundtable.discussion = 'Discussed upcoming licensing milestones and timeline concerns. Client expressed interest in cost optimization strategies.'
            roundtable.action_items = '1. Follow up on licensing application status\n2. Prepare cost analysis for Q2 review'
            roundtable.next_steps = 'Schedule technical review meeting for next month'

            print("  Added encrypted meeting notes:")
            print(f"    Discussion: (confidential)")
            print(f"    Action Items: (confidential)")
            print()

        # Commit all changes
        session.commit()

        print("=" * 70)
        print("[SUCCESS] Test data added and encrypted!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Open the database in DB Browser for SQLite")
        print("2. Look at the encrypted columns - you'll see gibberish bytes")
        print(f"3. Check project_id={project.project_id} in the projects table")
        print("   - capex_encrypted column will show binary data (not readable)")
        print("4. Try accessing via Flask app with different user permissions")
        print()

        return True

    except Exception as e:
        session.rollback()
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == '__main__':
    import os

    db_path = sys.argv[1] if len(sys.argv) > 1 else 'dev_nukeworks.sqlite'

    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        sys.exit(1)

    success = add_test_data(db_path)
    sys.exit(0 if success else 1)
