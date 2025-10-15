# NukeWorks Database Encryption Implementation Plan

## Overview

This plan implements a two-layer encryption system:
1. **Layer 1: File-Level Encryption (SQLCipher)** - Prevents unauthorized file access
2. **Layer 2: Field-Level Encryption (Fernet)** - Encrypts confidential columns within the database

**User Experience**: Users enter ONE password (database password). The application automatically grants/denies access to confidential data based on their `has_confidential_access` permission flag.

---

## Architecture Summary

### Security Layers

| Layer | What It Protects | Who Has Access | Key Storage |
|-------|------------------|----------------|-------------|
| Database File Encryption | Entire .db file | All authorized users (enter password at DB selection) | User enters password |
| Confidential Field Encryption | Financial data (capex, opex, etc.) | Users with `has_confidential_access=True` | Server `.env` file |
| NED Team Field Encryption | Internal notes, relationship data | Users with `is_ned_team=True` | Server `.env` file |
| Application Permissions | UI-level filtering | Based on user flags | Database `users` table |

### User Access Matrix

| User Type | DB Password | Login | Confidential Key | NED Key | What They See |
|-----------|-------------|-------|------------------|---------|---------------|
| Joe (Standard) | ✓ Required | ✓ Required | ✗ Auto-denied | ✗ Auto-denied | Public data only |
| Sally (Confidential) | ✓ Required | ✓ Required | ✓ Auto-granted | ✗ Auto-denied | Public + confidential data |
| NED Team Member | ✓ Required | ✓ Required | ✗ Auto-denied | ✓ Auto-granted | Public + NED notes |
| Admin | ✓ Required | ✓ Required | ✓ Auto-granted | ✓ Auto-granted | Everything |

### What Happens When Joe Opens DB Browser

| Scenario | What Joe Sees |
|----------|---------------|
| Without DB password | Can't open file at all ✓ |
| With DB password | Opens file, sees table structure ✓ |
| Views `project_name` column | Sees actual names (public data) ✓ |
| Views `capex` column | Sees encrypted gibberish: `gAAAAABh4K2m...` ✓ |
| Through Flask app | Sees `[Confidential]` for capex ✓ |

---

## Implementation Phases

### Phase 1: Dependencies & Environment Setup
**Estimated Time**: 1-2 hours

#### Tasks:
1. Install SQLCipher and encryption libraries
2. Generate master encryption keys
3. Configure environment variables
4. Test basic encryption/decryption

#### Files to Create/Modify:
- `requirements.txt` - Add new dependencies
- `.env.example` - Document required environment variables
- `.env` - Add master encryption keys (not committed to git)
- `.gitignore` - Ensure `.env` is excluded

---

### Phase 2: Encryption Utilities
**Estimated Time**: 3-4 hours

#### Tasks:
1. Create encryption utility module
2. Implement permission-based key access
3. Create encrypted column types for SQLAlchemy
4. Add encryption/decryption helpers

#### Files to Create:
- `app/utils/encryption.py` - Core encryption utilities
- `app/utils/key_management.py` - Master key handling
- `app/exceptions.py` - Add encryption-related exceptions

---

### Phase 3: Database Models Update
**Estimated Time**: 4-6 hours

#### Tasks:
1. Identify fields requiring encryption
2. Add encrypted columns to models
3. Create hybrid properties for transparent access
4. Test model encryption/decryption

#### Files to Modify:
- `app/models/project.py` - Encrypt financial fields
- `app/models/company.py` - Encrypt confidential business data
- `app/models/personnel.py` - Encrypt sensitive personnel data
- `app/models/contact.py` - Encrypt NED team notes

#### Fields to Encrypt:

**Projects (Confidential Access Required):**
- `capex`
- `opex`
- `fuel_cost`
- `lcoe`
- Any other financial/competitive data

**Companies (Confidential Access Required):**
- `financial_status`
- `revenue_estimate`
- Any proprietary business intelligence

**Personnel/CRM (NED Team Access Required):**
- `relationship_notes`
- `internal_notes`
- `client_priority`
- `relationship_strength`

---

### Phase 4: SQLCipher Integration
**Estimated Time**: 3-4 hours

#### Tasks:
1. Modify database connection to support SQLCipher
2. Update engine creation to handle encrypted databases
3. Add encryption key validation
4. Test encrypted database connections

#### Files to Modify:
- `config.py` - Add SQLCipher URI generation
- `app/__init__.py` - Update `get_or_create_engine_session()`
- `app/exceptions.py` - Add `EncryptionKeyError`

---

### Phase 5: Database Selection UI
**Estimated Time**: 3-4 hours

#### Tasks:
1. Add password field to database selector
2. Implement password validation
3. Add "remember password" functionality
4. Update selector logic to handle encryption

#### Files to Modify:
- `app/routes/db_select.py` - Add password handling
- `templates/db_select/select.html` - Add password input
- `app/models/user.py` - Add saved password storage (optional)

---

### Phase 6: Database Migration Tools
**Estimated Time**: 4-5 hours

#### Tasks:
1. Create script to encrypt existing databases
2. Create script to add encrypted columns to existing schemas
3. Create data migration script (plain → encrypted columns)
4. Test migration on development database

#### Files to Create:
- `scripts/encrypt_database.py` - Convert plain SQLite → SQLCipher
- `scripts/migrate_to_encrypted_columns.py` - Add encrypted columns
- `scripts/encrypt_existing_data.py` - Migrate data to encrypted columns
- `migrations/013_add_encrypted_columns.sql` - Schema migration

---

### Phase 7: Views & Templates Update
**Estimated Time**: 2-3 hours

#### Tasks:
1. Update templates to handle encrypted fields
2. Test permission-based field visibility
3. Add UI indicators for encrypted data
4. Update forms to handle encrypted fields

#### Files to Modify:
- `templates/projects/view.html`
- `templates/companies/view.html`
- `templates/crm/view.html`
- Various other view templates

---

### Phase 8: Testing & Validation
**Estimated Time**: 4-6 hours

#### Tasks:
1. Unit tests for encryption utilities
2. Integration tests for permission-based access
3. Test database opening with correct/incorrect passwords
4. Test field visibility for different user types
5. Manual testing with DB Browser

#### Files to Create:
- `tests/test_encryption.py` - Encryption unit tests
- `tests/test_encrypted_models.py` - Model encryption tests
- `tests/test_permission_encryption.py` - Permission integration tests

---

### Phase 9: Documentation & Deployment
**Estimated Time**: 2-3 hours

#### Tasks:
1. Update setup documentation
2. Create encryption key management guide
3. Document migration procedure
4. Create troubleshooting guide

#### Files to Create/Modify:
- `docs/ENCRYPTION_GUIDE.md` - User guide
- `docs/ENCRYPTION_KEY_MANAGEMENT.md` - Admin guide
- `README.md` - Update setup instructions
- `docs/21_TROUBLESHOOTING.md` - Add encryption issues

---

## Total Estimated Time: 26-37 hours

---

## Detailed Implementation Steps

### Phase 1: Dependencies & Environment Setup

#### Step 1.1: Update requirements.txt

```python
# Add to requirements.txt
pysqlcipher3==1.2.0
cryptography==41.0.7
```

#### Step 1.2: Generate Master Encryption Keys

```bash
# Run this on your development machine
python -c "from cryptography.fernet import Fernet; print('CONFIDENTIAL_DATA_KEY=' + Fernet.generate_key().decode())"
python -c "from cryptography.fernet import Fernet; print('NED_TEAM_KEY=' + Fernet.generate_key().decode())"
```

#### Step 1.3: Create .env file

```bash
# .env (DO NOT COMMIT TO GIT)

# Master encryption keys for field-level encryption
CONFIDENTIAL_DATA_KEY=your_generated_key_here
NED_TEAM_KEY=your_generated_key_here

# Existing environment variables
FLASK_ENV=development
SECRET_KEY=your_secret_key
```

#### Step 1.4: Update .env.example

```bash
# .env.example (SAFE TO COMMIT)

# Master encryption keys for field-level encryption (GENERATE YOUR OWN!)
CONFIDENTIAL_DATA_KEY=GENERATE_WITH_FERNET_GENERATE_KEY
NED_TEAM_KEY=GENERATE_WITH_FERNET_GENERATE_KEY

# Flask configuration
FLASK_ENV=development
SECRET_KEY=change_this_in_production
```

#### Step 1.5: Update .gitignore

```
# Ensure .env is excluded
.env
*.env

# Exclude unencrypted databases in production
databases/production/*.sqlite
databases/production/*_unencrypted.*
```

---

### Phase 2: Encryption Utilities

#### Step 2.1: Create app/utils/encryption.py

This file will contain:
- `PermissionBasedEncryption` class
- Automatic key access based on user permissions
- Field encryption/decryption methods
- Encrypted column type for SQLAlchemy

#### Step 2.2: Create app/utils/key_management.py

This file will contain:
- Master key loading from environment
- Key rotation utilities (future)
- Session key encryption/decryption

#### Step 2.3: Update app/exceptions.py

Add new exceptions:
- `EncryptionKeyError` - Invalid or missing encryption key
- `DecryptionError` - Failed to decrypt field
- `InsufficientPermissionsError` - User lacks permission for encrypted data

---

### Phase 3: Database Models Update

#### Step 3.1: Identify Fields to Encrypt

**Confidential Access Required:**
- All financial fields (capex, opex, lcoe, fuel_cost)
- Competitive intelligence data
- Proprietary business metrics

**NED Team Access Required:**
- Internal relationship notes
- Client priority/status
- Team-only commentary

#### Step 3.2: Update Project Model

Before:
```python
class Project(Base):
    capex = Column(Float)
```

After:
```python
class Project(Base):
    _capex_encrypted = Column('capex', LargeBinary)

    @hybrid_property
    def capex(self):
        from flask_login import current_user
        from app.utils.encryption import PermissionBasedEncryption
        return PermissionBasedEncryption.decrypt_field_for_user(
            self._capex_encrypted, 'confidential', current_user
        )

    @capex.setter
    def capex(self, value):
        from app.utils.encryption import PermissionBasedEncryption
        self._capex_encrypted = PermissionBasedEncryption.encrypt_field(
            value, 'confidential'
        )
```

---

### Phase 4: SQLCipher Integration

#### Step 4.1: Update config.py

```python
class Config:
    # ... existing config ...

    # Encryption settings
    ENABLE_DB_ENCRYPTION = True
    DB_CIPHER_ALGORITHM = 'aes-256-cbc'
    DB_KDF_ITERATIONS = 64000

    # Field-level encryption keys (from environment)
    CONFIDENTIAL_DATA_KEY = os.environ.get('CONFIDENTIAL_DATA_KEY')
    NED_TEAM_KEY = os.environ.get('NED_TEAM_KEY')

    @staticmethod
    def get_database_uri(db_path, encryption_password=None):
        """Generate SQLite or SQLCipher URI"""
        if Config.ENABLE_DB_ENCRYPTION and encryption_password:
            import urllib.parse
            key_escaped = urllib.parse.quote_plus(encryption_password)
            return (f'sqlite+pysqlcipher:///{db_path}'
                   f'?cipher={Config.DB_CIPHER_ALGORITHM}'
                   f'&kdf_iter={Config.DB_KDF_ITERATIONS}'
                   f'&key={key_escaped}')
        else:
            return f'sqlite:///{db_path}'
```

#### Step 4.2: Update app/__init__.py

Modify `get_or_create_engine_session()` to:
1. Accept optional `encryption_password` parameter
2. Generate SQLCipher URI if password provided
3. Test connection to validate password
4. Cache engines with encryption status

---

### Phase 5: Database Selection UI

#### Step 5.1: Update app/routes/db_select.py

Add:
- Password field to form
- Password validation logic
- Encrypted password storage in session
- Optional "remember password" feature

#### Step 5.2: Update templates/db_select/select.html

Add:
- Password input field
- Password visibility toggle
- "Remember password" checkbox
- Security information banner

---

### Phase 6: Database Migration Tools

#### Step 6.1: Create scripts/encrypt_database.py

Script to convert existing plain SQLite → SQLCipher encrypted database

Features:
- Prompt for encryption password
- Copy all tables and data
- Preserve indexes and constraints
- Verify data integrity

#### Step 6.2: Create scripts/migrate_to_encrypted_columns.py

Script to add encrypted columns to existing schema

Features:
- Detect existing columns that need encryption
- Add new `_*_encrypted` LargeBinary columns
- Preserve existing data temporarily
- Create migration rollback script

#### Step 6.3: Create scripts/encrypt_existing_data.py

Script to migrate data from plain columns to encrypted columns

Features:
- Read plain text values
- Encrypt with appropriate keys
- Store in encrypted columns
- Verify encryption/decryption works
- Optional: Drop old plain columns after verification

---

### Phase 7: Views & Templates Update

#### Step 7.1: Update Project Templates

Test that templates correctly show/hide encrypted fields based on permissions using existing permission filters:

```html
<!-- Already works with encrypted fields! -->
{{ project|field_value('capex') }}
```

#### Step 7.2: Add Encryption Indicators (Optional)

```html
{% if current_user.has_confidential_access %}
    <span class="badge badge-success">🔓 Confidential Access</span>
{% else %}
    <span class="badge badge-secondary">🔒 Limited Access</span>
{% endif %}
```

---

### Phase 8: Testing & Validation

#### Step 8.1: Unit Tests

```python
# tests/test_encryption.py

def test_encrypt_decrypt_field():
    """Test basic encryption/decryption"""

def test_permission_based_key_access():
    """Test users get correct keys based on permissions"""

def test_confidential_user_sees_data():
    """Test Sally can see encrypted confidential data"""

def test_standard_user_sees_redaction():
    """Test Joe sees [Confidential] for encrypted data"""
```

#### Step 8.2: Integration Tests

```python
# tests/test_permission_encryption.py

def test_sqlcipher_database_opens_with_password():
    """Test encrypted database requires password"""

def test_encrypted_field_in_database():
    """Test field is actually encrypted in DB"""

def test_db_browser_shows_encrypted_data():
    """Verify DB Browser sees gibberish for confidential fields"""
```

#### Step 8.3: Manual Testing Checklist

- [ ] Open encrypted database with correct password
- [ ] Attempt to open with wrong password (should fail)
- [ ] Log in as Joe, verify confidential fields show `[Confidential]`
- [ ] Log in as Sally, verify confidential fields show actual values
- [ ] Open database with DB Browser, verify financial fields show encrypted bytes
- [ ] Create new project with financial data, verify it encrypts
- [ ] Edit existing project, verify encryption persists

---

### Phase 9: Documentation & Deployment

#### Step 9.1: Create ENCRYPTION_GUIDE.md

Contents:
- Overview of encryption system
- User experience walkthrough
- How to open encrypted databases
- What each user type can see
- Troubleshooting common issues

#### Step 9.2: Create ENCRYPTION_KEY_MANAGEMENT.md

Contents:
- How to generate master keys
- Key rotation procedures
- Backup and recovery
- Adding/removing users from confidential access
- Security best practices

#### Step 9.3: Update README.md

Add sections:
- Encryption setup instructions
- Environment variable configuration
- Initial database encryption
- User permission configuration

---

## Migration Procedure for Existing Databases

### Step-by-Step Migration

1. **Backup everything**
   ```bash
   cp -r databases/ databases_backup_$(date +%Y%m%d)/
   ```

2. **Generate master encryption keys**
   ```bash
   python scripts/generate_keys.py
   # Save output to .env file
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add encrypted columns to schema**
   ```bash
   python scripts/migrate_to_encrypted_columns.py databases/development/nukeworks.sqlite
   ```

5. **Encrypt existing data**
   ```bash
   python scripts/encrypt_existing_data.py databases/development/nukeworks.sqlite
   ```

6. **Verify encryption**
   ```bash
   python scripts/verify_encryption.py databases/development/nukeworks.sqlite
   ```

7. **Convert database file to SQLCipher**
   ```bash
   python scripts/encrypt_database.py databases/development/nukeworks.sqlite
   # Enter database password when prompted
   # Output: databases/development/nukeworks_encrypted.db
   ```

8. **Test encrypted database**
   ```bash
   python app.py
   # Navigate to /select-db
   # Select encrypted database
   # Enter password
   # Test with different user accounts
   ```

9. **Replace production database**
   ```bash
   # After thorough testing
   mv databases/production/nukeworks.sqlite databases/production/nukeworks_unencrypted.sqlite.bak
   mv databases/production/nukeworks_encrypted.db databases/production/nukeworks.db
   ```

---

## Security Considerations

### Key Storage

**Master Encryption Keys (CONFIDENTIAL_DATA_KEY, NED_TEAM_KEY):**
- Store in `.env` file on application server
- Never commit to version control
- Backup securely (encrypted backup storage)
- Consider using a key management service (AWS KMS, Azure Key Vault) for production

**Database Passwords:**
- Share with authorized users via secure channel (password manager, encrypted email)
- Different passwords for different environments (dev, production)
- Consider using password manager integration for enterprise deployment

### Access Control

**Who should have confidential access?**
- Senior management
- Business development team
- Anyone who needs to see financial/competitive data

**Who should NOT have confidential access?**
- Contractors
- External consultants
- Junior staff who don't need financial visibility

**Granting access:**
```sql
-- In Flask admin interface or direct SQL
UPDATE users SET has_confidential_access = 1 WHERE username = 'sally';
```

### Audit Logging

Your existing audit system (`app/services/audit.py`) will automatically log:
- When users access encrypted fields
- Field modifications
- Permission changes

No additional changes needed - encryption is transparent to audit logging.

---

## Rollback Plan

If issues arise during deployment:

1. **Keep unencrypted backups** for 30 days
2. **Test rollback procedure** before production deployment
3. **Document rollback steps**:
   ```bash
   # Stop application
   # Restore unencrypted database
   cp databases_backup/nukeworks.sqlite databases/production/nukeworks.sqlite
   # Revert code changes (git checkout)
   # Restart application
   ```

---

## Performance Considerations

### Expected Impact

**Encryption overhead:**
- SQLCipher: ~5-10% performance overhead (negligible for most operations)
- Field-level encryption: Adds ~1-5ms per field decrypt operation
- Impact minimal for typical page loads (<100 fields)

**Optimization strategies:**
- Encrypted fields are only decrypted when accessed
- Use SQLAlchemy lazy loading for encrypted relationships
- Cache decrypted values in request context (avoid repeated decryption)

### Benchmarking

Test performance before/after encryption:
```bash
python scripts/benchmark_encryption.py
```

---

## Future Enhancements

### Phase 10 (Optional - Future):
- Key rotation mechanism
- Hardware security module (HSM) integration
- Per-user encryption keys (instead of per-role)
- Encrypted file attachments
- Encrypted audit log
- Compliance reporting (who accessed what encrypted data)

---

## Questions & Decisions

### Before Starting Implementation:

1. **Which fields should be encrypted?**
   - [ ] All financial fields (capex, opex, lcoe, fuel_cost)?
   - [ ] Company revenue/financial status?
   - [ ] Personnel contact information?
   - [ ] Other fields?

2. **Database passwords:**
   - [ ] Same password for all environments?
   - [ ] Different passwords per database?
   - [ ] How will passwords be distributed to users?

3. **Migration timing:**
   - [ ] Migrate all databases at once?
   - [ ] Start with development, then production?
   - [ ] Phased rollout?

4. **User communication:**
   - [ ] How will users be notified of the change?
   - [ ] Training required?
   - [ ] Documentation needs?

---

## Success Criteria

Implementation is complete when:
- [ ] All existing databases encrypted with SQLCipher
- [ ] All confidential fields encrypted at column level
- [ ] Users can open databases with single password
- [ ] Joe (standard user) sees `[Confidential]` for encrypted fields
- [ ] Sally (confidential user) sees actual values for encrypted fields
- [ ] Opening database with DB Browser shows encrypted gibberish for confidential fields
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Performance acceptable (<10% overhead)
- [ ] Rollback procedure tested and documented

---

## Next Steps

Ready to begin implementation? Choose one:

1. **Start with Phase 1** (Dependencies & Environment Setup)
2. **Review and adjust plan** based on your specific needs
3. **Pilot test on single database** before full deployment

Let me know when you're ready to proceed!
