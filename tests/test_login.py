#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to verify login functionality"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment
os.environ['FLASK_ENV'] = 'development'

def test_login():
    """Test that we can query the User model without errors"""
    try:
        from app import create_app
        from app.models import User

        # Create app context
        app = create_app()

        with app.app_context():
            # Get db_session from app
            from app import db_session

            # Try to query a user (this will trigger model initialization)
            user = db_session.query(User).filter_by(username='admin').first()

            if user:
                print("[OK] Successfully queried User model")
                print(f"[OK] Found user: {user.username}")
                print(f"[OK] User ID: {user.user_id}")
                print(f"[OK] User is admin: {user.is_admin}")
                print(f"\n[OK] All models initialized successfully!")
                return True
            else:
                print("[WARN] User 'admin' not found in database")
                print("       (This might be expected if the database is new)")
                return False

    except Exception as e:
        print(f"[ERROR] Error during login test: {type(e).__name__}")
        print(f"        {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_login()
    sys.exit(0 if success else 1)
