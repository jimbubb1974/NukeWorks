# Concurrent Access Debugging Guide

## Problem: Users Can't See Each Other's Changes

When two users are running separate instances of NukeWorks.exe and connecting to the same database, they should see each other's changes. If they don't, this guide will help diagnose why.

---

## Quick Diagnosis Steps

### Step 1: Verify You're Actually Using the Same Database File

**In each user's NukeWorks application:**

1. Look at the **navbar** (top of the page) - you'll see a database icon with the last 60 characters of the database path
2. **Compare the paths** between both users - they should be IDENTICAL

Example what you should see:
```
🗄️ ...10001\PS05DNED\Uncontrolled Documents\5 - Reference Info\Projects Database\deve_nukeworks.sqlite
```

**Important:** Even if paths LOOK the same, Windows might resolve them differently:
- `Q:\folder\db.sqlite` ≠ `\\server\share\folder\db.sqlite`
- Mapped drives (Q:) can point to different locations on different computers
- UNC paths (\\server\share) are more reliable

---

### Step 2: Run the Concurrent Access Test

Use the provided test script to confirm both users are accessing the same physical file.

**User A (the writer):**
```powershell
cd "C:\path\to\NukeWorks"
python test_concurrent_access.py write "Q:\10001\PS05DNED\...\deve_nukeworks.sqlite"
```

This will:
- Write a timestamped marker to the database
- Show you the absolute path being accessed
- Display file size and modification time
- Give you a timestamp to share with User B

**User B (the reader):**
```powershell
cd "C:\path\to\NukeWorks"
python test_concurrent_access.py read "Q:\10001\PS05DNED\...\deve_nukeworks.sqlite"
```

This will:
- Read the marker User A wrote
- Show if the marker is recent (< 60 seconds = SUCCESS)
- Display the same file info for comparison

**Expected Success Result:**
```
SUCCESS! You are accessing the SAME database file!
The test marker was written 15.2 seconds ago.
```

**Failure Scenarios:**
1. **"NO test marker found"** → You're accessing different database files
2. **"Test marker is 3600 seconds old"** → Stale marker, re-run the test
3. **"Database file does not exist"** → Path is wrong

---

## Debug Output in Terminal

The new build includes extensive debug output. Here's what to look for:

### At Startup

```
============================================================
NukeWorks - Nuclear Project Management Database
============================================================
Environment: development
Python Version: 3.13.2
Working Directory: C:\path\to\NukeWorks
Executable: C:\path\to\NukeWorks\NukeWorks.exe
Frozen (PyInstaller): True
Bundle Root (_MEIPASS): C:\Temp\...\
Database: [none selected yet — user will choose at /select-db]
Starting Flask server on http://127.0.0.1:5000/
============================================================
```

### When Database is Selected

```
============================================================
[DEBUG DB_SELECT POST] ========== DATABASE SELECTION POST ==========
[DEBUG DB_SELECT POST] All form data received:
[DEBUG DB_SELECT POST]   manual_db_path = 'Q:\10001\PS05DNED\...\deve_nukeworks.sqlite'
[DEBUG DB_SELECT POST]   custom_name = ''
============================================================
[DEBUG DB_SELECT POST] Using MANUAL PATH
[DEBUG DB_SELECT POST] Extracted values:
[DEBUG DB_SELECT POST]   manual_path: 'Q:\10001\PS05DNED\...\deve_nukeworks.sqlite'
[DEBUG DB_SELECT POST]   radio_path: ''
[DEBUG DB_SELECT POST]   final db_path: 'Q:\10001\PS05DNED\...\deve_nukeworks.sqlite'
[DEBUG DB_SELECT POST]   custom_name: ''
[DEBUG DB_SELECT POST]   apply_migration: False
[DEBUG DB_SELECT POST] Original path: 'Q:\10001\PS05DNED\...\deve_nukeworks.sqlite'
[DEBUG DB_SELECT POST] Normalized (absolute) path: 'Q:\10001\PS05DNED\...\deve_nukeworks.sqlite'
[DEBUG DB_SELECT POST] File exists: True
[DEBUG DB_SELECT POST] Validating database file...
[DEBUG DB_SELECT POST] Validation result:
[DEBUG DB_SELECT POST]   valid: True
[DEBUG DB_SELECT POST]   error: None
[DEBUG DB_SELECT POST]   schema_version: 12
```

**Check these values between both users:**
- `final db_path` should be IDENTICAL (character-for-character)
- `Normalized (absolute) path` should be IDENTICAL
- `File exists` should be True for both

### When First Connecting to Database

```
[DB CONNECTION] Journal mode set to: wal
[DB CONNECTION] Connected to database:
[DB CONNECTION]   File: Q:\10001\PS05DNED\...\deve_nukeworks.sqlite
[DB CONNECTION]   Size: 1,234,567 bytes
[DB CONNECTION]   Modified: 1735422891.123456
```

**What to check:**
1. **Journal mode** should be `wal` (Write-Ahead Logging for concurrency)
2. **File path** - compare between users
3. **File size** - should be similar (within a few KB)
4. **Modified timestamp** - this is a Unix timestamp (seconds since 1970)

### When User Makes a Change (e.g., Edit Company)

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

**What this tells you:**
- The change was successfully committed
- The timestamp shows WHEN it happened
- The verify query confirms it's in the database

### When Loading Data (e.g., CRM Dashboard)

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

**Compare timestamps:**
- If User A commits at timestamp `1735422891.123`
- And User B reads at timestamp `1735422900.456`
- User B's read is ~9 seconds AFTER User A's commit
- User B SHOULD see User A's changes

---

## Common Problems and Solutions

### Problem 1: Different Mapped Drive Letters

**Symptom:**
- User A uses `Q:\folder\db.sqlite`
- User B uses `R:\folder\db.sqlite`
- Paths look different but might point to the same network share

**Diagnosis:**
```powershell
# Run on each computer
net use
```

This shows what each drive letter maps to:
```
Q:        \\server\share1\path
R:        \\server\share1\path   ← SAME!
```

**Solution:**
Use the **UNC path** (\\server\share) instead of drive letters:
```
\\server\share1\path\folder\db.sqlite
```

---

### Problem 2: Cached Local Copies

**Symptom:**
- Database paths look identical
- File sizes are different
- Timestamps are very different

**Diagnosis:**
Look at the `[DB CONNECTION] Size` values:
- User A: `1,234,567 bytes`
- User B: `987,654 bytes` ← DIFFERENT!

**Solution:**
1. Both users close NukeWorks
2. Navigate to the database file in File Explorer
3. Right-click → Properties → Check "Always available offline" is UNCHECKED
4. Restart NukeWorks

---

### Problem 3: Database Locks (Less Likely with WAL Mode)

**Symptom:**
- Users see: "Database is locked" errors
- One user can't save changes

**Diagnosis:**
Check for `.sqlite-wal` and `.sqlite-shm` files in the same folder as your database:
```
deve_nukeworks.sqlite
deve_nukeworks.sqlite-wal    ← Should exist
deve_nukeworks.sqlite-shm    ← Should exist
```

**Solution:**
1. Ensure all three files are on the SAME network share
2. Ensure users have Read/Write permissions
3. Check `[DB CONNECTION] Journal mode` is `wal` not `delete`

---

### Problem 4: Session/Cache Not Refreshing

**Symptom:**
- Timestamps show User B read AFTER User A wrote
- But User B still sees old data
- `[DB READ]` timestamps don't show recent changes

**Diagnosis:**
This is a SQLAlchemy session cache issue.

**Solution:**
1. User B should completely close and restart NukeWorks
2. Or refresh the page (this should trigger a fresh query)
3. If problem persists, check if `[DB VERIFY]` shows correct data after `[DB COMMIT]`

---

## Advanced: Comparing Timestamps

Unix timestamps are seconds since Jan 1, 1970. To convert:

**Windows PowerShell:**
```powershell
# Convert Unix timestamp to human-readable
$timestamp = 1735422891.123
$origin = Get-Date "1970-01-01 00:00:00"
$date = $origin.AddSeconds($timestamp)
$date
```

**Online:** Use https://www.unixtimestamp.com/

**Example:**
```
User A [DB COMMIT] Timestamp: 1735422891.123
         = 2025-10-31 12:34:51

User B [DB READ] Timestamp: 1735422900.456  
         = 2025-10-31 12:35:00

User B's read is 9.3 seconds AFTER User A's commit
→ User B SHOULD see the changes
```

---

## Still Not Working?

### Collect Full Diagnostic Info

1. **Both users:** Copy ALL terminal output to a text file
2. **Both users:** Note the database path shown in the navbar
3. **Both users:** Run the concurrent access test and save output
4. **Both users:** Run this command:
   ```powershell
   Get-Item "Q:\path\to\db.sqlite" | Format-List FullName, Length, LastWriteTime
   ```

5. Compare:
   - Are the `FullName` paths identical?
   - Are the `Length` (file sizes) within 10KB of each other?
   - Are the `LastWriteTime` values close (within minutes)?

### Check Network Drive Health

```powershell
# Test read/write speed
Measure-Command { Copy-Item "Q:\path\to\db.sqlite" "C:\Temp\test.db" }
Measure-Command { Copy-Item "C:\Temp\test.db" "Q:\path\to\test_write.db" }
Remove-Item "C:\Temp\test.db"
Remove-Item "Q:\path\to\test_write.db"
```

If these are VERY slow (> 10 seconds), your network drive may have issues.

---

## Technical Background

### How SQLite WAL Mode Works

**Write-Ahead Logging (WAL) enables concurrent access:**

1. **Writers** write changes to a `.wal` file (not the main `.sqlite` file)
2. **Readers** can read from the main `.sqlite` file without blocking
3. Periodically, changes are "checkpointed" from `.wal` to `.sqlite`

**This means:**
- Multiple readers can access simultaneously
- One writer can write while others read
- But only ONE writer at a time

**For this to work:**
- All files (`.sqlite`, `.wal`, `.shm`) MUST be on the same filesystem
- Network filesystem MUST support file locking (SMB/CIFS does)
- Users MUST have read/write permissions on ALL three files

### What the Debug Outputs Show

| Debug Line | What It Tells You |
|-----------|-------------------|
| `[DB CONNECTION] Journal mode set to: wal` | Concurrent access is enabled |
| `[DB CONNECTION] File: path` | Actual file being accessed |
| `[DB CONNECTION] Size: X bytes` | Helps detect if different files |
| `[DB CONNECTION] Modified: timestamp` | When file was last changed |
| `[DB COMMIT] Timestamp: X` | When a change was saved |
| `[DB VERIFY] Re-queried ...` | Confirms change is in database |
| `[DB READ] Timestamp: X` | When data was loaded |
| `[DB READ] Sample company modified dates` | Shows what data was retrieved |

### Expected Behavior

```
Timeline:
T=0   User A edits Company #37
T=1   [DB COMMIT] Company #37 updated (User A's terminal)
T=2   User B refreshes CRM page
T=3   [DB READ] Loading companies (User B's terminal)
T=3   [DB READ] Company #37: modified=<T=1 timestamp>
      → User B SEES User A's changes ✓
```

---

## Summary Checklist

- [ ] Database paths in navbar are IDENTICAL between users
- [ ] `test_concurrent_access.py` shows "SUCCESS! Same database file"
- [ ] `[DB CONNECTION] File` paths are identical (not just similar)
- [ ] `[DB CONNECTION] Size` values are close (within 10KB)
- [ ] `[DB CONNECTION] Journal mode` is `wal` (not `delete`)
- [ ] File exists at UNC path (not just mapped drive)
- [ ] Both users have Read/Write permissions on database folder
- [ ] `.sqlite-wal` and `.sqlite-shm` files exist in same folder
- [ ] Network drive is accessible and responsive
- [ ] User B's `[DB READ] Timestamp` is AFTER User A's `[DB COMMIT] Timestamp`

If all checks pass but you still can't see changes, restart both NukeWorks instances.


