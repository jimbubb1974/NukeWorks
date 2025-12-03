#!/usr/bin/env python3
"""
Simple database creation and initialization script for NukeWorks

This script creates a new SQLite database with all required tables
and a default admin user (admin/admin123).

Usage:
    python create_database.py [database_path]
    
If no path is provided, creates 'nukeworks.sqlite' in current directory.
"""

import sys
import os
from pathlib import Path

def create_and_init_database(db_path):
    """Create and initialize a NukeWorks database"""
    
    print("=" * 60)
    print("NukeWorks Database Creation")
    print("=" * 60)
    print()
    
    # Convert to absolute path
    db_path = os.path.abspath(db_path)
    print(f"📁 Database path: {db_path}")
    
    # Check if file exists
    if os.path.exists(db_path):
        print()
        print(f"⚠️  WARNING: File already exists!")
        response = input("Delete and recreate? This will DESTROY all data! (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled.")
            return False
        try:
            os.remove(db_path)
            print("✓ Existing file deleted")
        except Exception as e:
            print(f"❌ Failed to delete existing file: {e}")
            return False
    
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            print(f"✓ Created directory: {db_dir}")
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")
            return False
    
    # Set environment variable so Flask uses this database
    os.environ['NUKEWORKS_DB_PATH'] = db_path
    
    print()
    print("🔧 Initializing Flask application...")
    
    try:
        from app import create_app
        from app.utils.db_init import init_database
        
        app = create_app()
        
        print("✓ Flask application created")
        print("✓ Database tables created")
        print()
        print("👤 Creating default admin user...")
        
        init_database(app.db_session)
        
        print()
        print("=" * 60)
        print("✅ SUCCESS! Database created and initialized")
        print("=" * 60)
        print()
        print(f"📁 Location: {db_path}")
        if os.path.exists(db_path):
            print(f"📊 Size: {os.path.getsize(db_path):,} bytes")
        else:
            print("⚠️  Note: Database created in memory, file will be written on next use")
        print()
        print("🔐 Default Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print()
        print("⚠️  IMPORTANT: Change the admin password after first login!")
        print()
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run NukeWorks.exe")
        print("  2. On database selection page, browse to:")
        print(f"     {db_path}")
        print("  3. Login with: admin / admin123")
        print("  4. Change your password immediately!")
        print()
        
        return True
        
    except ImportError as e:
        print()
        print("❌ ERROR: Failed to import NukeWorks modules")
        print(f"   {e}")
        print()
        print("Make sure you're running this script from the NukeWorks directory")
        print("and that all dependencies are installed.")
        return False
        
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    
    # Get database path from command line or use default
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default to current directory
        db_path = 'nukeworks.sqlite'
        print()
        print("No path provided, using default: nukeworks.sqlite")
        print("(You can specify a path: python create_database.py path/to/database.sqlite)")
        print()
    
    # Create and initialize
    success = create_and_init_database(db_path)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()

