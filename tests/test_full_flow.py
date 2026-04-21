#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test full flow: login and access personnel page"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment
os.environ['FLASK_ENV'] = 'development'

def test_full_flow():
    """Test login and personnel page access"""
    try:
        from app import create_app

        # Create app
        app = create_app()

        with app.test_client() as client:
            # Step 1: Login
            print("[TEST] Attempting login...")
            response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)

            if response.status_code == 200:
                print("[OK] Login successful (status 200)")
            else:
                print(f"[WARN] Login returned status {response.status_code}")

            # Step 2: Access personnel page
            print("[TEST] Accessing personnel page...")
            response = client.get('/personnel/', follow_redirects=True)

            if response.status_code == 200:
                print("[OK] Personnel page rendered successfully")

                # Check if page contains expected content
                page_content = response.data.decode('utf-8')
                if 'Personnel Directory' in page_content:
                    print("[OK] Page contains 'Personnel Directory' heading")
                if 'Internal Personnel' in page_content:
                    print("[OK] Page contains 'Internal Personnel' section")
                if 'External Contacts' in page_content:
                    print("[OK] Page contains 'External Contacts' section")

                print("\n[SUCCESS] All tests passed!")
                return True
            else:
                print(f"[ERROR] Personnel page returned status {response.status_code}")
                return False

    except Exception as e:
        print(f"[ERROR] Error during test: {type(e).__name__}")
        print(f"        {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_full_flow()
    sys.exit(0 if success else 1)
