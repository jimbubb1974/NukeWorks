#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge AI Research Extraction JSON data into NukeWorks database
Handles external personnel, roundtable history, and client profiles
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
import sys
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = Path("C:/Users/jimbu/Coding Projects/NukeWorks/databases/development/dev_nukeworks.sqlite")
JSON_PATH = Path("C:/Users/jimbu/Coding Projects/temp/docs/AI_RESEARCH_EXTRACTION_2025-10-18.json")

def load_json_data():
    """Load the JSON extraction file"""
    with open(JSON_PATH, 'r') as f:
        return json.load(f)

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(str(DB_PATH))

def get_existing_personnel(conn, company_id):
    """Get all existing personnel for a company"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT personnel_id, full_name, email, phone, role
        FROM external_personnel
        WHERE company_id = ?
    """, (company_id,))
    return {row[1]: row for row in cursor.fetchall()}

def add_external_personnel(conn, contact_data, company_id):
    """Add external personnel record"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO external_personnel
            (full_name, email, phone, role, company_id, contact_type, is_active, notes, created_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contact_data.get('contact_name'),
            contact_data.get('contact_email'),
            contact_data.get('contact_phone'),
            contact_data.get('contact_title'),
            company_id,
            'external',
            1,
            f"DB Match Confidence: {contact_data.get('db_match_confidence', 'N/A')}. Reason: {contact_data.get('db_match_reason', '')}. Relationship: {contact_data.get('relationship_to_mpr', '')}",
            datetime.now().isoformat(),
            1  # system user
        ))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        print(f"  ! Duplicate/Error adding {contact_data.get('contact_name')}: {e}")
        return None

def add_roundtable_entry(conn, client_name, company_id, roundtable_data, client_profile):
    """Add roundtable history record"""
    cursor = conn.cursor()

    # Prepare the fields
    next_steps = "\n".join(roundtable_data.get('next_steps', []))
    client_near_term_focus = "\n".join(roundtable_data.get('client_near_term_focus_areas', []))
    mpr_work_targets = "\n".join(roundtable_data.get('mpr_work_targets_goals', []))
    client_strategic_objectives = "\n".join(roundtable_data.get('client_strategic_objectives_priorities', []))
    discussion = roundtable_data.get('general_discussion', '')

    try:
        cursor.execute("""
            INSERT INTO roundtable_history
            (entity_type, entity_id, discussion, next_steps, client_near_term_focus,
             mpr_work_targets, client_strategic_objectives_encrypted, created_by, created_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'company',
            company_id,
            discussion,
            next_steps,
            client_near_term_focus,
            mpr_work_targets,
            client_strategic_objectives,
            1,  # system user
            datetime.now().isoformat()
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"  ! Error adding roundtable for {client_name}: {e}")
        return None

def update_client_profile(conn, company_id, client_profile_data):
    """Update or create client profile record"""
    cursor = conn.cursor()

    # First check if client_profiles table exists and has the needed fields
    try:
        # Try to get existing profile
        cursor.execute("""
            SELECT * FROM client_profiles WHERE company_id = ?
        """, (company_id,))
        existing = cursor.fetchone()

        profile_data = {
            'priority': client_profile_data.get('client_priority', 'Unknown'),
            'status': client_profile_data.get('client_status', 'Active'),
            'relationship_strength': client_profile_data.get('relationship_strength', 'New'),
            'relationship_notes': client_profile_data.get('relationship_notes', ''),
            'last_contact_date': client_profile_data.get('last_contact_date'),
            'last_contact_type': client_profile_data.get('last_contact_type'),
        }

        if existing:
            # Update existing
            cursor.execute("""
                UPDATE client_profiles
                SET priority = ?, status = ?, relationship_strength = ?,
                    relationship_notes = ?, last_contact_date = ?, last_contact_type = ?,
                    modified_date = ?
                WHERE company_id = ?
            """, (
                profile_data['priority'],
                profile_data['status'],
                profile_data['relationship_strength'],
                profile_data['relationship_notes'],
                profile_data['last_contact_date'],
                profile_data['last_contact_type'],
                datetime.now().isoformat(),
                company_id
            ))
        else:
            # Create new
            cursor.execute("""
                INSERT INTO client_profiles
                (company_id, priority, status, relationship_strength, relationship_notes,
                 last_contact_date, last_contact_type, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_id,
                profile_data['priority'],
                profile_data['status'],
                profile_data['relationship_strength'],
                profile_data['relationship_notes'],
                profile_data['last_contact_date'],
                profile_data['last_contact_type'],
                datetime.now().isoformat()
            ))

        conn.commit()
        return True
    except Exception as e:
        print(f"  ! Error updating client profile for company_id {company_id}: {e}")
        return False

def main():
    print("=" * 80)
    print("NukeWorks Database Merge - AI Research Extraction")
    print("=" * 80)
    print()

    # Load data
    print("Loading JSON data...")
    data = load_json_data()
    print(f"[OK] Loaded extraction for {len(data['clients'])} clients")
    print()

    # Connect to database
    conn = get_db_connection()
    print("[OK] Connected to database")
    print()

    # Statistics
    personnel_added = 0
    personnel_skipped = 0
    roundtable_added = 0
    profiles_updated = 0

    # Process each client
    for client_entry in data['clients']:
        company_data = client_entry['external_client']
        company_name = company_data['company_name']
        company_id = company_data['company_id']

        print(f"Processing: {company_name} (ID: {company_id})")
        print("-" * 40)

        # Get existing personnel
        existing_personnel = get_existing_personnel(conn, company_id)

        # Add external personnel
        if 'external_personnel' in client_entry:
            for contact in client_entry['external_personnel']:
                contact_name = contact.get('contact_name')

                # Skip if already exists (by name)
                if contact_name in existing_personnel:
                    print(f"  [SKIP] {contact_name} (already exists)")
                    personnel_skipped += 1
                else:
                    result = add_external_personnel(conn, contact, company_id)
                    if result:
                        print(f"  [ADD] {contact_name}")
                        personnel_added += 1
                    else:
                        personnel_skipped += 1

        # Add roundtable entry
        if 'roundtable_entry' in client_entry and 'client_profile' in client_entry:
            result = add_roundtable_entry(
                conn,
                company_name,
                company_id,
                client_entry['roundtable_entry'].get('fields', {}),
                client_entry['client_profile']
            )
            if result:
                print(f"  [ADD] Roundtable entry created (ID: {result})")
                roundtable_added += 1

        # Update client profile
        if 'client_profile' in client_entry:
            result = update_client_profile(conn, company_id, client_entry['client_profile'])
            if result:
                print(f"  [UPDATE] Client profile updated")
                profiles_updated += 1

        print()

    # Close connection
    conn.close()

    # Print summary
    print("=" * 80)
    print("MERGE SUMMARY")
    print("=" * 80)
    print(f"External Personnel Added:    {personnel_added}")
    print(f"External Personnel Skipped:  {personnel_skipped}")
    print(f"Roundtable Entries Created:  {roundtable_added}")
    print(f"Client Profiles Updated:     {profiles_updated}")
    print()
    print("[OK] Merge complete!")
    print()

if __name__ == '__main__':
    main()
