"""Test actual field access with debug output"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Project, User
from app.utils.permissions import can_view_field

def test_field_access_debug():
    print("=" * 80)
    print("DEBUG: TESTING FIELD ACCESS LOGIC")
    print("=" * 80)

    from app import db_session

    # Get project and user
    project = db_session.get(Project, 1)
    bwilson = db_session.query(User).filter_by(username='bwilson').first()

    print(f"\n[PROJECT] ID={project.project_id}, Name={project.project_name}")
    print(f"[USER] username={bwilson.username}, has_confidential_access={bwilson.has_confidential_access}")

    print("\n[TESTING can_view_field FUNCTION]")
    fields = ['capex', 'opex', 'fuel_cost', 'lcoe']

    for field in fields:
        can_view = can_view_field(bwilson, 'projects', 1, field)
        print(f"   {field}: can_view={can_view}")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        test_field_access_debug()
