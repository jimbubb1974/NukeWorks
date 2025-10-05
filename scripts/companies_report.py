"""Generate summary counts for the unified company schema."""
from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app.models import CompanyRoleAssignment, CompanyRole


def main(config_name: str | None = None) -> None:
    app = app_module.create_app(config_name)
    with app.app_context():
        session = app_module.db_session
        total_companies = session.query(app_module.models.Company).count()
        assignments = session.query(CompanyRoleAssignment).all()
        role_lookup = {role.role_id: role.role_label for role in session.query(CompanyRole).all()}

        counts = Counter()
        for assignment in assignments:
            counts[role_lookup.get(assignment.role_id, str(assignment.role_id))] += 1

        print(f"Total companies: {total_companies}")
        for role, count in sorted(counts.items(), key=lambda item: item[0]):
            print(f"  {role}: {count}")


if __name__ == '__main__':
    config = os.environ.get('FLASK_ENV', 'development')
    main(config)
