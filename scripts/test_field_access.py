"""Test actual field access with bwilson user to verify per-field confidentiality"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Project, User
from flask_login import login_user
from flask import Flask

def test_field_access(app):
    print("=" * 80)
    print("TESTING FIELD ACCESS FOR BWILSON (NO CONFIDENTIAL ACCESS)")
    print("=" * 80)

    from app import db_session
    from flask_login import login_user

    # Get project and user
    project = db_session.get(Project, 1)
    bwilson = db_session.query(User).filter_by(username='bwilson').first()

    print(f"\n[PROJECT] {project.project_name}")
    print(f"[USER] bwilson - has_confidential_access: {bwilson.has_confidential_access}")

    # Use the actual app's request context (which has encryption keys loaded)
    with app.test_request_context():
        login_user(bwilson)

        print("\n[FIELD ACCESS TEST]")
        fields = ['capex', 'opex', 'fuel_cost', 'lcoe']

        for field in fields:
            value = getattr(project, field)
            is_redacted = value == '[Confidential]'
            status = "REDACTED" if is_redacted else f"VALUE: {value}"
            icon = "[NO]" if is_redacted else "[OK]"
            print(f"   {icon} {field}: {status}")

    print("\n[EXPECTED RESULTS]")
    print("   [NO] capex: REDACTED (flagged as confidential)")
    print("   [OK] opex: VALUE (not flagged)")
    print("   [NO] fuel_cost: REDACTED (flagged as confidential)")
    print("   [OK] lcoe: VALUE (not flagged)")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        test_field_access(app)
