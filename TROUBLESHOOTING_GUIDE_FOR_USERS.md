# NukeWorks Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "No database selected" or "User not found"

**Symptoms:**

- Browser opens to login page but login fails
- Terminal shows: `[DEBUG LOGIN] User 'admin' not found in database`
- Terminal shows: `[DEBUG LOGIN] Total users in database: 0`

**Cause:** The database file exists but has no users (not initialized)

**Solution:**

1. Note the database file path shown in terminal (look for `Session selected_db_path:`)
2. Close the application (CTRL+C in terminal)
3. Open command prompt/terminal in the NukeWorks folder
4. Run: `python -c "from app import create_app; from app.utils.db_init import init_database; app = create_app(); init_database(app.db_session)"`
5. You should see: `WARNING: Default admin user created with username 'admin' and password 'admin123'`
6. Restart NukeWorks.exe
7. Login with: admin / admin123

**Alternative:** Use a pre-initialized database file (if provided)

---

### Issue 2: "Selected database file not found"

**Symptoms:**

- Terminal shows: `[DEBUG LOGIN] CRITICAL: Selected database file does not exist!`
- Path shows location that doesn't exist on your computer

**Cause:** Database file was moved, deleted, or path is invalid on your system

**Solution:**

1. Browser will redirect to database selection page
2. Click "Browse" and navigate to a valid .sqlite database file
3. Or select from the "Recent Databases" list if available
4. Click "Select Database"

---

### Issue 3: Can't find database file to select

**Symptoms:**

- Database selection page is empty
- No databases shown in the list
- Don't know where database files are

**Cause:** No database files in default locations, or need to browse to network drive

**Solution:**

**Option A - Create new database:**

1. Note the working directory shown in terminal window
2. Create a new file in that directory: `my_database.sqlite`
3. Initialize it (see Issue 1 solution)
4. Refresh the database selection page
5. Select the newly created database

**Option B - Browse to existing database:**

1. On database selection page, click "Browse"
2. Navigate to where your .sqlite file is stored
3. Common locations:
   - `C:\Users\[YourName]\Documents\NukeWorks\`
   - Network drives: `\\server\share\databases\`
   - USB drives: `E:\NukeWorks\`
4. Select the .sqlite file
5. Click "Select Database"

---

### Issue 4: Wrong username or password

**Symptoms:**

- Terminal shows: `[DEBUG LOGIN] Password valid: False`
- Or shows: `[DEBUG LOGIN] Available user: 'someuser'` (different from what you tried)

**Cause:** Typing wrong credentials, or database has different users than expected

**Solution:**

1. Check terminal output for `[DEBUG LOGIN] Available user:` lines
2. These show the actual usernames in the selected database
3. Try those usernames with the password you know
4. If you don't know the password:
   - Contact whoever created the database
   - Or create a new database and initialize it with default admin user

---

### Issue 5: Port 5000 already in use

**Symptoms:**

- Terminal shows: `⚠️  Port 5000 is already in use (PID: 12345)`
- Application won't start

**Cause:** Another instance of NukeWorks (or another app) is using port 5000

**Solution:**

1. Application will ask: `[K]ill the existing process and start fresh` or `[C]ancel`
2. Press `K` to kill the other process and start NukeWorks
3. Or press `C` to cancel, then:
   - Close other NukeWorks instances manually
   - Check Task Manager for "NukeWorks.exe" and end it
   - Restart NukeWorks.exe

---

### Issue 6: Database error or corruption

**Symptoms:**

- Terminal shows: `[DEBUG LOGIN] CRITICAL: Failed to query User table`
- Error about missing tables or corrupted database

**Cause:** Database file is corrupted or missing required tables

**Solution:**

1. Try a different database file
2. If you have backups, restore from backup
3. Create a new database:
   - Create empty file: `new_database.sqlite`
   - Initialize it (see Issue 1 solution)
   - Re-enter your data

---

## Reading Debug Output

The terminal window shows detailed debug information. Look for these patterns:

### Successful Login Flow:

```
[DEBUG DB_SELECT] ========== DATABASE SELECTION PAGE ==========
[DEBUG DB_SELECT] Found 3 scanned databases
[DEBUG DB_SELECT] Normalized path: C:\Users\You\nukeworks.sqlite
[DEBUG DB_SELECT] Path exists: True
[DEBUG LOGIN] ========== LOGIN ATTEMPT ==========
[DEBUG LOGIN] Username: admin
[DEBUG LOGIN] DB exists: True
[DEBUG LOGIN] DB size: 245760 bytes
[DEBUG LOGIN] Querying User table for username='admin'
[DEBUG LOGIN] User 'admin' found, checking password
[DEBUG LOGIN] Password valid: True
```

### Failed Login - No Users:

```
[DEBUG LOGIN] User 'admin' not found in database
[DEBUG LOGIN] Total users in database: 0
[DEBUG LOGIN] CRITICAL: Database has NO users!
```

**→ Solution:** Initialize the database (see Issue 1)

### Failed Login - Wrong Username:

```
[DEBUG LOGIN] User 'admin' not found in database
[DEBUG LOGIN] Total users in database: 3
[DEBUG LOGIN]   - Username: 'john' | Active: True | Admin: True
[DEBUG LOGIN]   - Username: 'jane' | Active: True | Admin: False
[DEBUG LOGIN]   - Username: 'bob' | Active: False | Admin: False
```

**→ Solution:** Use one of the listed usernames (try 'john' with the password you know)

### Failed Login - Wrong Password:

```
[DEBUG LOGIN] User 'admin' found, checking password
[DEBUG LOGIN] Password valid: False
```

**→ Solution:** Check your password, or reset it (requires database access or admin help)

---

## Getting Help

When reporting issues, please include:

1. **Terminal output** (copy all the text from the terminal window)
2. **Database file path** (shown in `Session selected_db_path:`)
3. **What you clicked/typed** (step by step)
4. **Any error messages** shown in browser or terminal

Send this information to your technical support contact.

---

## Quick Start for First-Time Users

1. Run `NukeWorks.exe` → terminal window opens, browser opens
2. Browser shows **database selection page**
3. If you have a database file:
   - Click "Browse" → select your .sqlite file → "Select Database"
4. If starting fresh:
   - Note the working directory from terminal
   - Create file: `my_data.sqlite` in that directory
   - Close NukeWorks (CTRL+C)
   - Initialize database (see Issue 1 solution)
   - Restart NukeWorks.exe
5. Browser shows **login page**
6. Login with: **admin** / **admin123**
7. **IMPORTANT:** Change the default password immediately!

---

## Technical Details

### Database Requirements

- File format: SQLite 3
- Must contain these tables: users, system_settings, schema_versions
- Default admin credentials: admin / admin123 (created during initialization)

### File Locations

- Working directory: Shown in terminal on startup
- Session cache: `instance/db_selector.json`
- Logs: Terminal window (not saved to file by default)

### Network Drives

- Supported: Yes, browse to `\\server\share\path\file.sqlite`
- Must have read/write permissions
- May require mapping network drive first

---

## Still Having Issues?

1. Check terminal output for `[DEBUG]` and `[CRITICAL]` messages
2. Try with a fresh database file
3. Verify file permissions (read/write access)
4. Contact technical support with terminal output



