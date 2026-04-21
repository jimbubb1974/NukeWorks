#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Re-import roundtable data with proper encryption
This copies plain text data from the plain columns to encrypted columns
"""

import sys
sys.path.insert(0, '.')

from app import create_app, db_session
from app.models import RoundtableHistory
from app.utils.encryption import encrypt_ned_team

app = create_app()

print("Migrating roundtable data with proper encryption...")
print()

with app.app_context():
    # Import here to ensure app context is active
    from sqlalchemy.orm import Session
    from app import db

    # Create a session
    session = Session(db.engine)

    # Find all entries with plain text data that need encryption
    entries = session.query(RoundtableHistory).filter(
        RoundtableHistory.entity_type == 'Company'
    ).all()

    print(f"Found {len(entries)} Company entries")
    print()

    encrypted_count = 0
    for entry in entries:
        # Check if any encrypted columns are empty but plain text columns have data
        needs_encryption = False

        if entry.discussion and not entry._discussion_encrypted:
            print(f"Encrypting discussion for history_id {entry.history_id}...")
            entry._discussion_encrypted = encrypt_ned_team(entry.discussion)
            needs_encryption = True

        if entry.next_steps and not entry._next_steps_encrypted:
            print(f"Encrypting next_steps for history_id {entry.history_id}...")
            entry._next_steps_encrypted = encrypt_ned_team(entry.next_steps)
            needs_encryption = True

        if entry.client_near_term_focus and not entry._client_near_term_focus_encrypted:
            print(f"Encrypting client_near_term_focus for history_id {entry.history_id}...")
            entry._client_near_term_focus_encrypted = encrypt_ned_team(entry.client_near_term_focus)
            needs_encryption = True

        if entry.mpr_work_targets and not entry._mpr_work_targets_encrypted:
            print(f"Encrypting mpr_work_targets for history_id {entry.history_id}...")
            entry._mpr_work_targets_encrypted = encrypt_ned_team(entry.mpr_work_targets)
            needs_encryption = True

        if entry.client_strategic_objectives and not entry._client_strategic_objectives_encrypted:
            print(f"Encrypting client_strategic_objectives for history_id {entry.history_id}...")
            entry._client_strategic_objectives_encrypted = encrypt_ned_team(entry.client_strategic_objectives)
            needs_encryption = True

        if needs_encryption:
            session.add(entry)
            encrypted_count += 1

    if encrypted_count > 0:
        session.commit()
        print()
        print(f"[OK] Encrypted {encrypted_count} entries")
    else:
        print("[OK] All entries already encrypted or no data to encrypt")

    print()
    print("Verifying encryption...")
    entries = session.query(RoundtableHistory).filter(
        RoundtableHistory.entity_id == 32
    ).all()

    for entry in entries:
        print()
        print(f"Entry {entry.history_id} (Company {entry.entity_id}):")
        print(f"  Discussion: {entry.discussion[:50] if entry.discussion else 'None'}...")
        print(f"  Next Steps: {entry.next_steps[:50] if entry.next_steps else 'None'}...")
        print(f"  Focus: {entry.client_near_term_focus[:50] if entry.client_near_term_focus else 'None'}...")

    session.close()
    print()
    print("[OK] Migration complete!")
