import sqlite3

db_path = r'Q:\0001\PS05DNED\Uncontrolled Documents\5 - Reference Info\Projects Database\dev_nukeworks.sqlite'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print('Tables in Q drive database:')
for table in tables[:25]:
    print(f'  - {table[0]}')

# Check if company_id 45 exists
if 'company' in [t[0] for t in tables]:
    cursor.execute('SELECT COUNT(*) FROM company')
    count = cursor.fetchone()[0]
    print(f'\nTotal companies: {count}')
    
    cursor.execute('SELECT company_id, company_name FROM company WHERE company_id = 45')
    result = cursor.fetchone()
    if result:
        print(f'Company 45 found: {result}')
    else:
        print('Company 45 not found')
        # List some companies
        cursor.execute('SELECT company_id, company_name FROM company LIMIT 5')
        companies = cursor.fetchall()
        print('Sample companies:')
        for c in companies:
            print(f'  - ID {c[0]}: {c[1]}')

conn.close()
