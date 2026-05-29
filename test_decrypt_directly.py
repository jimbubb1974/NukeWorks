import sys
import os
sys.path.insert(0, '.')

# Use the correct keys from .env
os.environ['CONFIDENTIAL_DATA_KEY'] = 'rAzGf5eGO7Qoinauxhy6Rutnt_Kj5PXH1U12bguzk_k='
os.environ['NED_TEAM_KEY'] = 'iumcO7VtmYp_ESXpMupQAXGXsGl9QqG3Q_dA8Ng2014='

from app.utils.encryption import decrypt_value
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

db_path = r'Q:\0001\PS05DNED\Uncontrolled Documents\5 - Reference Info\Projects Database\dev_nukeworks.sqlite'
engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
session = Session()

# Get the raw encrypted values
result = session.execute(text('SELECT company_id, client_tier_encrypted, client_priority_encrypted FROM client_profiles WHERE company_id = 45')).first()
if result:
    print('Raw database values:')
    tier_encrypted = result[1]
    priority_encrypted = result[2]
    print(f'  tier_encrypted type: {type(tier_encrypted)}, starts with: {str(tier_encrypted)[:20]}')
    print(f'  priority_encrypted type: {type(priority_encrypted)}, starts with: {str(priority_encrypted)[:20]}')
    
    # Try to decrypt manually with correct key type
    try:
        tier_decrypted = decrypt_value(tier_encrypted, 'confidential')
        print(f'\n✓ Decrypted tier: {tier_decrypted}')
    except Exception as e:
        print(f'\n✗ Failed to decrypt tier: {e}')
    
    try:
        priority_decrypted = decrypt_value(priority_encrypted, 'confidential')
        print(f'✓ Decrypted priority: {priority_decrypted}')
    except Exception as e:
        print(f'✗ Failed to decrypt priority: {e}')
