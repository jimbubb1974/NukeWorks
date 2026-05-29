import sys
import os
sys.path.insert(0, '.')

# Use the correct keys from .env
os.environ['CONFIDENTIAL_DATA_KEY'] = 'rAzGf5eGO7Qoinauxhy6Rutnt_Kj5PXH1U12bguzk_k='
os.environ['NED_TEAM_KEY'] = 'iumcO7VtmYp_ESXpMupQAXGXsGl9QqG3Q_dA8Ng2014='
os.environ['NUKEWORKS_DB_PATH'] = r'Q:\0001\PS05DNED\Uncontrolled Documents\5 - Reference Info\Projects Database\dev_nukeworks.sqlite'

from app import create_app
from app.models import Company, ClientProfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

app = create_app()

# Create session to the Q drive database
db_path = r'Q:\0001\PS05DNED\Uncontrolled Documents\5 - Reference Info\Projects Database\dev_nukeworks.sqlite'
engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
session = Session()

# Get the company
company = session.query(Company).filter_by(company_id=45).first()
print(f'Company: {company.company_name}')

# Check BEFORE 
result = session.execute(text('SELECT client_tier_encrypted, client_priority_encrypted FROM client_profiles WHERE company_id = 45')).first()
if result:
    tier_before = result[0]
    print(f'\nBEFORE save:')
    print(f'  tier_encrypted length: {len(tier_before) if tier_before else 0}')
else:
    print('No profile before save')

# Simulate the form submission - set values exactly as the route does
profile = company.client_profile
if not profile:
    profile = ClientProfile(company_id=company.company_id)
    session.add(profile)

# This is what the route code does
tier_from_form = 'Tier 1'  # simulating form value
priority_from_form = 'High'  # simulating form value

profile.client_tier = tier_from_form or None
profile.client_priority = priority_from_form or None

print(f'\nSetting tier={tier_from_form}, priority={priority_from_form}')
session.commit()
print('✓ Committed to database')

# Check AFTER
result = session.execute(text('SELECT client_tier_encrypted, client_priority_encrypted FROM client_profiles WHERE company_id = 45')).first()
if result:
    tier_after = result[0]
    print(f'\nAFTER save:')
    print(f'  tier_encrypted length: {len(tier_after) if tier_after else 0}')
    if tier_before and tier_after:
        print(f'  Did tier change? {tier_before != tier_after}')
        if tier_before != tier_after:
            print(f'  BEFORE first 20 bytes: {tier_before[:20]}')
            print(f'  AFTER  first 20 bytes: {tier_after[:20]}')

# Try to read back via ORM
session.refresh(company)
print(f'\nRead back via ORM:')
print(f'  tier: {company.client_profile.client_tier}')
print(f'  priority: {company.client_profile.client_priority}')
