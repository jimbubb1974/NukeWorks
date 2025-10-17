"""Check what confidential flags are currently set in the database"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.confidential import ConfidentialFieldFlag

def check_flags():
    print("=" * 80)
    print("CURRENT CONFIDENTIAL FIELD FLAGS")
    print("=" * 80)

    from app import db_session

    flags = db_session.query(ConfidentialFieldFlag).filter_by(
        table_name='projects',
        record_id=1
    ).all()

    if not flags:
        print("\n[INFO] No flags found for project_id=1")
    else:
        print(f"\n[FOUND] {len(flags)} flags for project_id=1:")
        for flag in flags:
            status = "CONFIDENTIAL" if flag.is_confidential else "PUBLIC"
            print(f"   - {flag.field_name}: {status}")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        check_flags()
