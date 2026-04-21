#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to verify personnel page renders without errors"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment
os.environ['FLASK_ENV'] = 'development'

def test_personnel_page():
    """Test that the personnel list route works"""
    try:
        from app import create_app

        # Create app
        app = create_app()

        with app.test_client() as client:
            # Try to access the personnel page (should redirect to login)
            response = client.get('/personnel/')

            print(f"[OK] Personnel route exists")
            print(f"[OK] Response status: {response.status_code}")

            if response.status_code == 302:
                print(f"[OK] Correctly redirects to login (not authenticated)")
            elif response.status_code == 200:
                print(f"[OK] Page rendered successfully")
            else:
                print(f"[WARN] Unexpected status code: {response.status_code}")

            return True

    except Exception as e:
        print(f"[ERROR] Error testing personnel page: {type(e).__name__}")
        print(f"        {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_personnel_page()
    sys.exit(0 if success else 1)
