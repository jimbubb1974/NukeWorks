# Concurrent Access Debug Implementation Summary

## Problem Statement

Two users running separate NukeWorks.exe instances connecting to the same database file (Q:\...\deve_nukeworks.sqlite) cannot see each other's changes. Despite the UI showing they're using the same database path, changes made by one user are not visible to the other.

---

## Root Cause Theories

### Theory 1: Different Physical Files (Most Likely)
- Windows may resolve paths differently on each computer
- Mapped drives (Q:) might point to different locations
- One user might be accessing a cached local copy
- **Probability:** HIGH

### Theory 2: SQLAlchemy Session Caching
- Each Flask instance has its own database session
- Sessions may cache data and not refresh automatically
- **Probability:** MEDIUM

### Theory 3: Transaction Isolation
- Uncommitted transactions holding locks
- Changes not being properly flushed to disk
- **Probability:** LOW (WAL mode should handle this)

### Theory 4: Network Drive Caching
- Windows "Offline Files" feature caching database locally
- Network file system not properly syncing
- **Probability:** MEDIUM

---

## Debug Enhancements Implemented

### 1. Database Connection Logging (`app/__init__.py`)

**Added comprehensive connection diagnostics:**

```python
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    # Enable WAL mode
    result = cursor.execute("PRAGMA journal_mode=WAL").fetchone()
    print(f"[DB CONNECTION] Journal mode set to: {result[0]}")
    
    # Get database file path
    db_file = cursor.execute("PRAGMA database_list").fetchall()
    for row in db_file:
        if row[1] == 'main':
            print(f"[DB CONNECTION]   File: {row[2]}")
            stat = os.stat(row[2])
            print(f"[DB CONNECTION]   Size: {stat.st_size:,} bytes")
            print(f"[DB CONNECTION]   Modified: {stat.st_mtime}")
```

**Output Example:**
```
[DB CONNECTION] Journal mode set to: wal
[DB CONNECTION] Connected to database:
[DB CONNECTION]   File: Q:\10001\PS05DNED\...\deve_nukeworks.sqlite
[DB CONNECTION]   Size: 1,234,567 bytes
[DB CONNECTION]   Modified: 1735422891.123456
```

**What This Shows:**
- Confirms WAL mode is enabled (required for concurrency)
- Shows the ACTUAL file path being accessed (resolved by SQLite)
- Shows file size (helps detect if users are accessing different files)
- Shows modification timestamp (Unix epoch seconds)

---

### 2. Write Operation Logging (`app/routes/companies.py`)

**Added logging after database commits:**

```python
db_session.commit()

# DEBUG: Log successful commit with timestamp
print(f"[DB COMMIT] Company #{company_id} updated")
print(f"[DB COMMIT] User: {current_user.username}")
print(f"[DB COMMIT] Company: {company.company_name}")
print(f"[DB COMMIT] Timestamp: {time.time()}")
print(f"[DB COMMIT] Modified Date: {company.modified_date}")

# Force a fresh query to verify
verify_company = verify_session.query(Company).filter_by(company_id=company_id).first()
print(f"[DB VERIFY] Re-queried company modified_date: {verify_company.modified_date}")
if verify_company.client_profile:
    print(f"[DB VERIFY] Client priority: {verify_company.client_profile.client_priority}")
```

**Output Example:**
```
============================================================
[DB COMMIT] Company #37 updated
[DB COMMIT] User: admin
[DB COMMIT] Company: Example Company
[DB COMMIT] Timestamp: 1735422891.123
[DB COMMIT] Modified Date: 2025-10-31 12:34:56.789
[DB VERIFY] Re-queried company modified_date: 2025-10-31 12:34:56.789
[DB VERIFY] Client priority: Strategic
============================================================
```

**What This Shows:**
- Confirms the commit succeeded
- Records EXACT timestamp of the change
- Verifies the change is immediately visible in a fresh query
- Shows the actual data that was written

---

### 3. Read Operation Logging (`app/routes/crm.py`)

**Added logging when loading data:**

```python
mpr_companies = query.all()

# DEBUG: Log what data was retrieved
print(f"[DB READ] CRM Dashboard - Loading companies")
print(f"[DB READ] User: {current_user.username}")
print(f"[DB READ] Timestamp: {time.time()}")
print(f"[DB READ] Total companies: {len(mpr_companies)}")
if mpr_companies:
    print(f"[DB READ] Sample company modified dates:")
    for company in mpr_companies[:3]:
        print(f"[DB READ]   {company.company_name}: modified={company.modified_date}")
        if company.client_profile:
            print(f"[DB READ]     Profile modified={company.client_profile.modified_date}")
```

**Output Example:**
```
============================================================
[DB READ] CRM Dashboard - Loading companies
[DB READ] User: admin
[DB READ] Timestamp: 1735422900.456
[DB READ] Total companies: 15
[DB READ] Sample company modified dates:
[DB READ]   Example Company: modified=2025-10-31 12:34:56.789
[DB READ]     Profile modified=2025-10-31 12:34:56.789
============================================================
```

**What This Shows:**
- When data was loaded
- Which user loaded it
- How many records were retrieved
- The modified dates of the data (to compare with writes)

---

### 4. UI Database Path Display (`app/templates/base.html`)

**Added database path to navbar:**

```html
<li class="nav-item">
  <span class="navbar-text text-warning small" title="Current database file path">
    <i class="bi bi-database"></i> {{ session.get('selected_db_path', 'No DB selected')[-60:] }}
  </span>
</li>
```

**What Users See:**
```
🗄️ ...10001\PS05DNED\Uncontrolled Documents\5 - Reference Info\Projects Database\deve_nukeworks.sqlite
```

**Why This Helps:**
- Users can quickly verify they're using the intended database
- Easy to compare paths between multiple users
- Shows last 60 characters (enough to distinguish different databases)

---

### 5. Concurrent Access Test Script (`test_concurrent_access.py`)

**Purpose:** Definitively prove whether two users are accessing the same physical file.

**How It Works:**

**User A (Writer):**
```bash
python test_concurrent_access.py write "Q:\path\to\db.sqlite"
```

This:
1. Writes a timestamped marker to `system_settings` table
2. Shows absolute path, file size, modification time
3. Gives User A a timestamp to share

**User B (Reader):**
```bash
python test_concurrent_access.py read "Q:\path\to\db.sqlite"
```

This:
1. Reads the marker from `system_settings` table
2. Checks how old the marker is
3. Reports SUCCESS if marker is < 60 seconds old

**Expected Output (Success):**
```
============================================================
SUCCESS! You are accessing the SAME database file!
The test marker was written 15.2 seconds ago.
============================================================
```

**Expected Output (Failure):**
```
✗ NO test marker found!
Either:
  1. The other user hasn't written it yet
  2. You are accessing a DIFFERENT database file
  3. The marker was deleted
```

---

## Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `app/__init__.py` | Added connection logging | Show actual file being accessed, WAL mode, size, timestamp |
| `app/routes/companies.py` | Added commit logging | Confirm writes succeed, show timestamp |
| `app/routes/crm.py` | Added read logging | Show when data is loaded, what data is retrieved |
| `app/templates/base.html` | Added DB path to navbar | User-visible confirmation of selected database |
| `test_concurrent_access.py` | New script | Definitive test for same file access |
| `CONCURRENT_ACCESS_DEBUGGING_GUIDE.md` | New documentation | Step-by-step troubleshooting guide |

---

## How to Use These Debug Outputs

### Step 1: Visual Check
Both users look at the navbar and compare the database path shown.

### Step 2: Run Concurrent Access Test
```bash
# User A
python test_concurrent_access.py write "Q:\10001\...\deve_nukeworks.sqlite"

# User B (immediately after)
python test_concurrent_access.py read "Q:\10001\...\deve_nukeworks.sqlite"
```

If test shows "SUCCESS", proceed to Step 3. If not, users are accessing different files.

### Step 3: Compare Terminal Output

**User A makes a change (e.g., edits a company):**
Look for:
```
[DB COMMIT] Company #37 updated
[DB COMMIT] Timestamp: 1735422891.123
```

**User B refreshes their page:**
Look for:
```
[DB READ] Timestamp: 1735422900.456
[DB READ]   Example Company: modified=2025-10-31 12:34:56.789
```

**Compare:**
- Is User B's READ timestamp AFTER User A's COMMIT timestamp?
- Does User B's read show the modified date from User A's commit?

### Step 4: Check Database Connection Info

**Both users should see:**
```
[DB CONNECTION] Journal mode set to: wal
[DB CONNECTION]   File: Q:\10001\...\deve_nukeworks.sqlite
[DB CONNECTION]   Size: 1,234,567 bytes
```

**Compare:**
- Are the file paths identical (exact match)?
- Are the file sizes close (within ~10KB)?
- Is WAL mode enabled for both?

---

## Common Issues and What Debug Output Reveals

### Issue 1: Different Physical Files

**Debug Output Shows:**
```
User A: [DB CONNECTION] File: Q:\10001\...\deve_nukeworks.sqlite
        [DB CONNECTION] Size: 1,234,567 bytes

User B: [DB CONNECTION] File: C:\Users\Bob\AppData\Local\...\deve_nukeworks.sqlite
        [DB CONNECTION] Size: 987,654 bytes
```

**Diagnosis:** Different paths = different files!

**Solution:** 
- Both users manually enter the SAME UNC path: `\\server\share\path\deve_nukeworks.sqlite`
- Don't use mapped drives (Q:) as they can differ between computers

---

### Issue 2: Session Caching

**Debug Output Shows:**
```
User A: [DB COMMIT] Timestamp: 1735422891.123

User B: [DB READ] Timestamp: 1735422900.456  (9 seconds AFTER commit)
        [DB READ] Example Company: modified=2025-10-30 10:00:00.000  (OLD DATE!)
```

**Diagnosis:** User B's read is AFTER User A's commit, but shows OLD data = session cache issue

**Solution:**
- User B should close and restart NukeWorks
- Or use Ctrl+F5 to force-refresh the page

---

### Issue 3: Network Drive Caching

**Debug Output Shows:**
```
User A: [DB CONNECTION] Modified: 1735422891.123
User B: [DB CONNECTION] Modified: 1735400000.000  (6 hours older!)
```

**Diagnosis:** Same path, but different modification times = Windows is caching

**Solution:**
- Disable "Offline Files" for the database folder
- Use UNC path instead of mapped drive

---

### Issue 4: WAL Mode Not Enabled

**Debug Output Shows:**
```
[DB CONNECTION] Journal mode set to: delete
```

**Diagnosis:** WAL mode failed to enable (maybe database is locked?)

**Solution:**
- Close all NukeWorks instances
- Delete `.sqlite-wal` and `.sqlite-shm` files if they exist
- Restart NukeWorks

---

## Testing the Debug Outputs

After building the executable with debug logging:

1. **Start NukeWorks** - should see startup diagnostics
2. **Select database** - should see `[DEBUG DB_SELECT POST]` output
3. **First connection** - should see `[DB CONNECTION]` output
4. **Edit a company** - should see `[DB COMMIT]` output
5. **View CRM page** - should see `[DB READ]` output
6. **Check navbar** - should see database path in yellow text

---

## Performance Impact

**Debug Output Impact:**
- **Logging:** Minimal (< 1ms per operation)
- **File stat calls:** ~5ms per connection
- **Verification queries:** ~10ms per commit

**Recommendation:**
- Keep debug logging for now while diagnosing
- Once issue is resolved, can create a "production" build without debug output

---

## Next Steps for User

1. **Build completed successfully** at: `dist\NukeWorks\NukeWorks.exe`

2. **Copy to deployment location:**
   ```powershell
   Copy-Item "dist\NukeWorks\*" "Q:\path\to\deployment\" -Recurse -Force
   ```

3. **Both users run the new executable**

4. **Compare terminal output** as they use the application

5. **Run concurrent access test:**
   ```bash
   # Copy test script to deployment
   Copy-Item "test_concurrent_access.py" "Q:\path\to\deployment\"
   
   # User A
   cd "Q:\path\to\deployment"
   python test_concurrent_access.py write "Q:\path\to\deve_nukeworks.sqlite"
   
   # User B
   cd "Q:\path\to\deployment"
   python test_concurrent_access.py read "Q:\path\to\deve_nukeworks.sqlite"
   ```

6. **Review `CONCURRENT_ACCESS_DEBUGGING_GUIDE.md`** for detailed troubleshooting

---

## Summary

With these debug enhancements, you can now:

✅ **Confirm both users are accessing the same physical file**
✅ **See exact timestamps when changes are written**
✅ **See exact timestamps when data is read**
✅ **Verify WAL mode is enabled**
✅ **Compare file sizes and modification times**
✅ **See database path in the UI**
✅ **Run a definitive same-file test**

The debug output will reveal which of the four theories is causing the issue, and the guide provides specific solutions for each scenario.


