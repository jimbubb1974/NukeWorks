import argparse
import os
import sqlite3


def run_checks(db_path: str) -> None:
    db_path = os.path.normpath(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    print(f"DB: {db_path}")

    def q(sql: str):
        cur.execute(sql)
        return cur.fetchall()

    print("roles:", q("SELECT role_id, role_code FROM company_roles WHERE role_code IN ('owner','developer') ORDER BY role_code"))
    print(
        "owner_assignments:",
        q(
            "SELECT COUNT(*) FROM company_role_assignments WHERE role_id IN (SELECT role_id FROM company_roles WHERE role_code='owner')"
        ),
    )
    print(
        "developer_assignments:",
        q(
            "SELECT COUNT(*) FROM company_role_assignments WHERE role_id IN (SELECT role_id FROM company_roles WHERE role_code='developer')"
        ),
    )
    print("indexes:", q("PRAGMA index_list('company_role_assignments')"))
    print("idx_info:", q("PRAGMA index_info('idx_cra_unique')"))
    print(
        "legacy_tables:",
        q(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('owners_developers','owner_developers','technology_vendors','vendor_preferred_constructor')"
        ),
    )

    con.close()


def main():
    parser = argparse.ArgumentParser(description="Verify NukeWorks DB cleanup state")
    parser.add_argument("--db", required=True, help="Path to SQLite database file")
    args = parser.parse_args()
    run_checks(args.db)


if __name__ == "__main__":
    main()








