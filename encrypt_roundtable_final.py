#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Encrypt roundtable data using cryptography directly
Loads keys from .env file
"""

import sqlite3
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

# Load .env file
env_path = Path("C:/Users/jimbu/Coding Projects/NukeWorks/.env")
load_dotenv(env_path)

DB_PATH = "C:/Users/jimbu/Coding Projects/NukeWorks/databases/development/dev_nukeworks.sqlite"

def load_keys():
    """Load encryption keys from environment"""
    ned_team_key = os.environ.get('NED_TEAM_KEY')
    if ned_team_key:
        return ned_team_key
    return None

def encrypt_data(data, key):
    """Encrypt data with the key"""
    if not data or not key:
        return None
    cipher = Fernet(key.encode() if isinstance(key, str) else key)
    return cipher.encrypt(data.encode('utf-8'))

def main():
    print("Encrypting roundtable data...")
    print()

    # Get the encryption key
    ned_team_key = load_keys()
    if not ned_team_key:
        print("ERROR: Could not load encryption keys from", KEYS_FILE)
        return

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all Company roundtable entries
    cursor.execute("""
        SELECT history_id, discussion, next_steps, client_near_term_focus,
               mpr_work_targets
        FROM roundtable_history
        WHERE entity_type = 'Company'
    """)

    entries = cursor.fetchall()
    print(f"Found {len(entries)} entries to encrypt")
    print()

    encrypted_count = 0
    for entry_id, discussion, next_steps, focus, targets in entries:
        updates = []
        params = []

        # Encrypt each field that has data
        if discussion:
            encrypted = encrypt_data(discussion, ned_team_key)
            updates.append("discussion_encrypted = ?")
            params.append(encrypted)
            print(f"  Encrypting discussion for entry {entry_id}")

        if next_steps:
            encrypted = encrypt_data(next_steps, ned_team_key)
            updates.append("next_steps_encrypted = ?")
            params.append(encrypted)
            print(f"  Encrypting next_steps for entry {entry_id}")

        if focus:
            encrypted = encrypt_data(focus, ned_team_key)
            updates.append("client_near_term_focus_encrypted = ?")
            params.append(encrypted)
            print(f"  Encrypting client_near_term_focus for entry {entry_id}")

        if targets:
            encrypted = encrypt_data(targets, ned_team_key)
            updates.append("mpr_work_targets_encrypted = ?")
            params.append(encrypted)
            print(f"  Encrypting mpr_work_targets for entry {entry_id}")

        if updates:
            params.append(entry_id)
            sql = f"UPDATE roundtable_history SET {', '.join(updates)} WHERE history_id = ?"
            cursor.execute(sql, params)
            encrypted_count += 1

    conn.commit()
    conn.close()

    print()
    print(f"[OK] Encrypted {encrypted_count} entries")
    print("[OK] Migration complete!")

if __name__ == '__main__':
    main()
