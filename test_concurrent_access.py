#!/usr/bin/env python3
"""
Test concurrent database access
This script helps verify that two users are actually accessing the same database file

Usage:
    1. User A runs: python test_concurrent_access.py write <db_path>
    2. User B runs: python test_concurrent_access.py read <db_path>
    3. User B should see the changes User A made
"""
import sqlite3
import sys
import time
import os
from datetime import datetime

def write_test_marker(db_path):
    """Write a test marker to the database"""
    print(f"\n{'='*70}")
    print(f"WRITE TEST - Adding test marker to database")
    print(f"{'='*70}")
    print(f"Database: {db_path}")
    print(f"Absolute path: {os.path.abspath(db_path)}")
    print(f"File exists: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        stat = os.stat(db_path)
        print(f"File size: {stat.st_size:,} bytes")
        print(f"Last modified: {datetime.fromtimestamp(stat.st_mtime)}")
    
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    
    # Check if system_settings table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_settings'")
    if not cursor.fetchone():
        print("ERROR: system_settings table does not exist in this database!")
        conn.close()
        return
    
    # Write a test marker with current timestamp
    test_timestamp = time.time()
    test_marker = f"CONCURRENT_TEST_{test_timestamp}"
    
    cursor.execute("""
        INSERT OR REPLACE INTO system_settings 
        (setting_name, setting_value, setting_category, created_by, modified_by)
        VALUES (?, ?, 'System', 1, 1)
    """, ('concurrent_test_marker', test_marker))
    
    conn.commit()
    
    # Verify write
    cursor.execute("SELECT setting_value FROM system_settings WHERE setting_name = 'concurrent_test_marker'")
    result = cursor.fetchone()
    
    print(f"\n✓ Test marker written: {test_marker}")
    print(f"✓ Verified in database: {result[0] if result else 'NOT FOUND'}")
    print(f"\nTimestamp for verification: {test_timestamp}")
    print(f"Human readable: {datetime.fromtimestamp(test_timestamp)}")
    
    # Get file info after write
    conn.close()
    stat = os.stat(db_path)
    print(f"\nAfter write:")
    print(f"  File size: {stat.st_size:,} bytes")
    print(f"  Last modified: {datetime.fromtimestamp(stat.st_mtime)}")
    
    print(f"\n{'='*70}")
    print(f"Now have the other user run: python test_concurrent_access.py read {db_path}")
    print(f"{'='*70}\n")


def read_test_marker(db_path):
    """Read the test marker from the database"""
    print(f"\n{'='*70}")
    print(f"READ TEST - Checking for test marker in database")
    print(f"{'='*70}")
    print(f"Database: {db_path}")
    print(f"Absolute path: {os.path.abspath(db_path)}")
    print(f"File exists: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        stat = os.stat(db_path)
        print(f"File size: {stat.st_size:,} bytes")
        print(f"Last modified: {datetime.fromtimestamp(stat.st_mtime)}")
    else:
        print("ERROR: Database file does not exist!")
        return
    
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    
    # Read test marker
    cursor.execute("SELECT setting_value FROM system_settings WHERE setting_name = 'concurrent_test_marker'")
    result = cursor.fetchone()
    
    if result:
        marker = result[0]
        print(f"\n✓ Test marker found: {marker}")
        
        # Extract timestamp
        if marker.startswith("CONCURRENT_TEST_"):
            timestamp_str = marker.replace("CONCURRENT_TEST_", "")
            try:
                test_time = float(timestamp_str)
                current_time = time.time()
                age_seconds = current_time - test_time
                
                print(f"✓ Timestamp: {test_time}")
                print(f"✓ Written at: {datetime.fromtimestamp(test_time)}")
                print(f"✓ Age: {age_seconds:.1f} seconds ago")
                
                if age_seconds < 60:
                    print(f"\n{'='*70}")
                    print(f"SUCCESS! You are accessing the SAME database file!")
                    print(f"The test marker was written {age_seconds:.1f} seconds ago.")
                    print(f"{'='*70}\n")
                else:
                    print(f"\nWARNING: Test marker is {age_seconds:.1f} seconds old.")
                    print(f"It may be stale or from a different test.")
            except:
                print(f"Could not parse timestamp from marker")
    else:
        print(f"\n✗ NO test marker found!")
        print(f"Either:")
        print(f"  1. The other user hasn't written it yet")
        print(f"  2. You are accessing a DIFFERENT database file")
        print(f"  3. The marker was deleted")
    
    # Show all system settings as reference
    print(f"\nAll system settings (first 5):")
    cursor.execute("SELECT setting_name, setting_value FROM system_settings LIMIT 5")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    conn.close()
    print(f"\n{'='*70}\n")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Write test: python test_concurrent_access.py write <db_path>")
        print("  Read test:  python test_concurrent_access.py read <db_path>")
        print()
        print("Example:")
        print('  User A: python test_concurrent_access.py write "Q:\\10001\\PS05DNED\\...\\deve_nukeworks.sqlite"')
        print('  User B: python test_concurrent_access.py read "Q:\\10001\\PS05DNED\\...\\deve_nukeworks.sqlite"')
        sys.exit(1)
    
    action = sys.argv[1].lower()
    db_path = sys.argv[2]
    
    if action == 'write':
        write_test_marker(db_path)
    elif action == 'read':
        read_test_marker(db_path)
    else:
        print(f"Unknown action: {action}")
        print("Use 'write' or 'read'")
        sys.exit(1)


