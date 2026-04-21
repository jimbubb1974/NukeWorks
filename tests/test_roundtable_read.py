#!/usr/bin/env python3
"""Test reading roundtable data via ORM"""

import sys
sys.path.insert(0, '.')

from app import create_app, db_session
from app.models import RoundtableHistory, Company

app = create_app()

with app.app_context():
    print("Testing RoundtableHistory ORM read...")
    print()

    # Test 1: Query Blue Energy entries
    print("Blue Energy (ID: 32) entries:")
    entries = db_session.query(RoundtableHistory).filter(
        RoundtableHistory.entity_type == 'Company',
        RoundtableHistory.entity_id == 32
    ).all()

    print(f"Found {len(entries)} entries")
    for entry in entries:
        print(f"\nEntry ID: {entry.history_id}")
        print(f"  Entity: {entry.entity_type} {entry.entity_id}")
        print(f"  Timestamp: {entry.created_timestamp}")
        print(f"  Discussion: {entry.discussion[:60] if entry.discussion else 'None'}...")
        print(f"  Next Steps: {entry.next_steps[:60] if entry.next_steps else 'None'}...")
        print(f"  Focus: {entry.client_near_term_focus[:60] if entry.client_near_term_focus else 'None'}...")
        print(f"  Targets: {entry.mpr_work_targets[:60] if entry.mpr_work_targets else 'None'}...")

    print("\n" + "="*60)
    print("All new entries (entity_type='Company'):")
    all_entries = db_session.query(RoundtableHistory).filter(
        RoundtableHistory.entity_type == 'Company'
    ).order_by(RoundtableHistory.entity_id).all()

    for entry in all_entries:
        company = db_session.get(Company, entry.entity_id)
        company_name = company.company_name if company else "Unknown"
        print(f"\n{company_name} (ID: {entry.entity_id}) - {entry.created_timestamp}")
        print(f"  Discussion: {entry.discussion[:50] if entry.discussion else 'None'}...")
