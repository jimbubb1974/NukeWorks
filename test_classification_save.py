import sys
import os
sys.path.insert(0, '.')

os.environ['CONFIDENTIAL_DATA_KEY'] = 'ljDoOzaiZ5_1n3EiKoCbyL7TDEqHc6Js_hqwK_R4UEA='
os.environ['NED_TEAM_KEY'] = 'lCRatlKRIlEE4-04Pjp1q_OIyYnkdrQRiU_6swEVJHw='

from app.models import Company, ClientProfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

db_path = r'Q:\0001\PS05DNED\Uncontrolled Documents\5 - Reference Info\Projects Database\dev_nukeworks.sqlite'
engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
session = Session()

# Check raw database values BEFORE
result = session.execute(text('SELECT company_id, client_tier_encrypted, client_priority_encrypted FROM client_profiles WHERE company_id = 45')).first()
if result:
    print(f'BEFORE save:')
    print(f'  client_tier_encrypted length: {len(result[1]) if result[1] else 0}')
    print(f'  client_priority_encrypted length: {len(result[2]) if result[2] else 0}')
else:
    print('No profile for company 45 before save')

# Get company and set values through ORM (which will encrypt them)
company = session.query(Company).filter_by(company_id=45).first()
print(f'\nCompany found: {company.company_name}')
print(f'Current profile tier (via ORM): {company.client_profile.client_tier if company.client_profile else None}')
print(f'Current profile priority (via ORM): {company.client_profile.client_priority if company.client_profile else None}')

profile = company.client_profile
if not profile:
    profile = ClientProfile(company_id=company.company_id)
    session.add(profile)

# Set through ORM descriptors (proper way)
profile.client_tier = 'Tier 1'
profile.client_priority = 'High'
session.commit()
print('\n✓ Saved: Tier 1 / High')

# Check raw database values AFTER
result = session.execute(text('SELECT company_id, client_tier_encrypted, client_priority_encrypted FROM client_profiles WHERE company_id = 45')).first()
if result:
    print(f'\nAFTER save:')
    print(f'  client_tier_encrypted length: {len(result[1]) if result[1] else 0}')
    print(f'  client_priority_encrypted length: {len(result[2]) if result[2] else 0}')
    if result[1]:
        print(f'  tier starts with gAAAAA: {str(result[1])[:7]}')

# Refresh and verify we can read it back
session.refresh(company)
print(f'\nRead back via ORM:')
print(f'  tier: {company.client_profile.client_tier}')
print(f'  priority: {company.client_profile.client_priority}')

# Try changing to different values
profile.client_tier = 'Tier 2'
profile.client_priority = 'Medium'
session.commit()
print('\n✓ Saved: Tier 2 / Medium')

session.refresh(company)
print(f'Read back after 2nd save:')
print(f'  tier: {company.client_profile.client_tier}')
print(f'  priority: {company.client_profile.client_priority}')
