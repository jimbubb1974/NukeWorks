import sqlite3

db_path = r'Q:\0001\PS05DNED\Uncontrolled Documents\5 - Reference Info\Projects Database\dev_nukeworks.sqlite'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get columns in client_profiles
cursor.execute("PRAGMA table_info(client_profiles)")
columns = cursor.fetchall()
print('Columns in client_profiles table:')
for col in columns:
    print(f'  - {col[1]} ({col[2]})')

conn.close()
