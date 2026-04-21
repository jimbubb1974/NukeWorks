#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update client profiles with strategic data from JSON
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

def update_client_profile(conn, company_id, client_profile_data):
    """Update client profile record"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE client_profiles
            SET client_priority = ?,
                client_status = ?,
                relationship_strength = ?,
                relationship_notes = ?,
                last_contact_date = ?,
                last_contact_type = ?,
                modified_date = ?,
                modified_by = ?
            WHERE company_id = ?
        """, (
            client_profile_data.get('client_priority', 'Unknown'),
            client_profile_data.get('client_status', 'Active'),
            client_profile_data.get('relationship_strength', 'New'),
            client_profile_data.get('relationship_notes', ''),
            client_profile_data.get('last_contact_date'),
            client_profile_data.get('last_contact_type'),
            datetime.now().isoformat(),
            1,  # system user
            company_id
        ))

        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"  ! Error updating client profile for company_id {company_id}: {e}")
        return False

def main():
    print("=" * 80)
    print("Client Profiles Update - AI Research Extraction")
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
    profiles_updated = 0

    # Process each client
    for client_entry in data['clients']:
        company_data = client_entry['external_client']
        company_name = company_data['company_name']
        company_id = company_data['company_id']

        print(f"Processing: {company_name} (ID: {company_id})")

        # Update client profile
        if 'client_profile' in client_entry:
            result = update_client_profile(conn, company_id, client_entry['client_profile'])
            if result:
                print(f"  [UPDATE] Client profile updated")
                print(f"    Priority: {client_entry['client_profile'].get('client_priority')}")
                print(f"    Status: {client_entry['client_profile'].get('client_status')}")
                print(f"    Strength: {client_entry['client_profile'].get('relationship_strength')}")
                profiles_updated += 1
            else:
                print(f"  [SKIP] No changes made")
        print()

    # Close connection
    conn.close()

    # Print summary
    print("=" * 80)
    print("UPDATE SUMMARY")
    print("=" * 80)
    print(f"Client Profiles Updated:     {profiles_updated}")
    print()
    print("[OK] Update complete!")
    print()

if __name__ == '__main__':
    main()
