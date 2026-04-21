# NukeWorks - Setup Instructions

## Quick Start (5 Minutes)

### Step 1: Run the Application

1. Double-click `NukeWorks.exe`
2. A terminal window will open (keep it visible - shows helpful debug info)
3. Your web browser will automatically open to the application

### Step 2: Select a Database

You'll see a **database selection page** (not a login page - this is correct!)

**Option A - If you have a database file:**

- Click "Browse" and navigate to your `.sqlite` file
- Click "Select Database"
- Skip to Step 3

**Option B - Create a new database:**

1. Note the "Working Directory" shown in the terminal window
2. Open File Explorer to that directory
3. Create a new text file, rename it to: `my_database.sqlite`
4. In the terminal, press CTRL+C to close NukeWorks
5. Run the database initialization (see "Creating a New Database" below)
6. Restart `NukeWorks.exe`
7. Select your newly created database

### Step 3: Login

- **Username:** `admin`
- **Password:** `admin123`

### Step 4: Change Password

⚠️ **IMPORTANT:** Change the default password immediately!

1. Click your username in the top-right corner
2. Select "Change Password"
3. Enter a secure new password

---

## Creating a New Database

### Method 1: Using Python Script (Recommended)

If Python is installed on your system:

```cmd
python create_database.py my_database.sqlite
```

Or just run:

```cmd
python create_database.py
```

(Creates `nukeworks.sqlite` in current directory)

The script will:

- Create the database file
- Set up all required tables
- Create default admin user (admin/admin123)

### Method 2: Manual Initialization

If you have a programming environment:

```cmd
python -c "import os; os.environ['NUKEWORKS_DB_PATH'] = 'my_database.sqlite'; from app import create_app; from app.utils.db_init import init_database; app = create_app(); init_database(app.db_session)"
```

Replace `my_database.sqlite` with your desired database path.

---

## Troubleshooting

### "User not found" Error

**What you see:**

- Login fails with "Invalid username or password"
- Terminal shows: `[DEBUG LOGIN] User 'admin' not found in database`
- Terminal shows: `[DEBUG LOGIN] Total users in database: 0`

**Problem:** Database file exists but has no users

**Solution:**

1. Check terminal for the database path (look for `Session selected_db_path:`)
2. Close NukeWorks (CTRL+C in terminal)
3. Initialize that database using Method 1 or 2 above
4. Restart NukeWorks

### Can't Find Database File

**Problem:** Don't have a .sqlite file or don't know where it is

**Solution:**

1. Create a new one (see "Creating a New Database" above)
2. Or ask whoever sent you the application for the database file
3. Database files typically have `.sqlite` or `.db` extension

### Database Shows Different Users

**What you see:**
Terminal shows:

```
[DEBUG LOGIN] Total users in database: 3
[DEBUG LOGIN]   - Username: 'john' | Active: True | Admin: True
[DEBUG LOGIN]   - Username: 'jane' | Active: True | Admin: False
```

**Solution:** Use one of those usernames (e.g., try `john` with the password you were given)

### Port Already in Use

**What you see:**

```
⚠️  Port 5000 is already in use (PID: 12345)
```

**Solution:**

- Application will ask if you want to kill the existing process
- Press `K` to kill it and start fresh
- Or press `C` to cancel, then manually close other NukeWorks instances

---

## Understanding the Terminal Output

Keep the terminal window visible - it shows helpful diagnostic information:

### Good Login Flow:

```
[DEBUG DB_SELECT] ========== DATABASE SELECTION PAGE ==========
[DEBUG DB_SELECT] Found 2 scanned databases
[DEBUG LOGIN] ========== LOGIN ATTEMPT ==========
[DEBUG LOGIN] Username: admin
[DEBUG LOGIN] DB size: 245760 bytes
[DEBUG LOGIN] User 'admin' found, checking password
[DEBUG LOGIN] Password valid: True
✓ Login successful
```

### Empty Database (No Users):

```
[DEBUG LOGIN] User 'admin' not found
[DEBUG LOGIN] Total users in database: 0
[DEBUG LOGIN] CRITICAL: Database has NO users!
```

→ **Fix:** Initialize the database

### Wrong Username:

```
[DEBUG LOGIN] User 'admin' not found
[DEBUG LOGIN] Total users in database: 2
[DEBUG LOGIN]   - Username: 'bob' | Active: True
[DEBUG LOGIN]   - Username: 'alice' | Active: True
```

→ **Fix:** Try username `bob` or `alice`

### Wrong Password:

```
[DEBUG LOGIN] User 'admin' found, checking password
[DEBUG LOGIN] Password valid: False
```

→ **Fix:** Check your password

---

## File Locations

### Application Files

- `NukeWorks.exe` - Main executable
- `_internal/` - Application dependencies (don't modify)
- `instance/` - Settings and cache (created on first run)
- `flask_sessions/` - Session data (created on first run)
- `logs/` - Debug logs (created on first run)

### Database Files

- Can be anywhere on your system
- Typically have `.sqlite` or `.db` extension
- Application remembers your last selection

### Network Drives

- ✅ Supported - browse to `\\server\share\database.sqlite`
- Must have read/write permissions
- May need to map network drive first (depends on your setup)

---

## Default Credentials

**Username:** `admin`  
**Password:** `admin123`

⚠️ **SECURITY WARNING:** Change this password immediately after first login!

---

## Features Overview

After logging in, you can:

- Manage nuclear projects
- Track vendors and suppliers
- Maintain company relationships
- Log client interactions
- Generate reports
- Manage users (admin only)
- Create database snapshots

---

## Getting Help

If you encounter issues:

1. **Check the terminal window** for `[DEBUG]` and `[CRITICAL]` messages
2. **Copy the terminal output** (select text, right-click, copy)
3. **Send to technical support** with:
   - Terminal output
   - Description of what you clicked
   - Any error messages from the browser

Detailed troubleshooting: See `TROUBLESHOOTING_GUIDE_FOR_USERS.md`

---

## System Requirements

- **Operating System:** Windows 10 or later
- **RAM:** 2GB minimum, 4GB recommended
- **Disk Space:** 500MB for application, plus space for your database
- **Network:** Internet not required (runs locally)
- **Python:** Not required (application is standalone)

---

## Security Notes

1. **Change default password immediately**
2. **Protect your database file** - contains all your data
3. **Make regular backups** - use the snapshot feature
4. **Don't share credentials** - create separate accounts for each user
5. **Use strong passwords** - minimum 8 characters, mix of letters/numbers/symbols

---

## Support

For technical support or questions:

- Check `TROUBLESHOOTING_GUIDE_FOR_USERS.md`
- Contact your system administrator
- Provide terminal output when reporting issues

---

**Version:** 1.0  
**Last Updated:** October 28, 2025

---

## Quick Reference

| Task                | Action                                          |
| ------------------- | ----------------------------------------------- |
| Start application   | Double-click `NukeWorks.exe`                    |
| Select database     | Browse to `.sqlite` file on first run           |
| Login               | Username: `admin`, Password: `admin123`         |
| Change password     | Click username → Change Password                |
| Create new database | Run `python create_database.py`                 |
| Switch database     | Click "Database" in top navigation              |
| View debug info     | Keep terminal window open                       |
| Close application   | CTRL+C in terminal, or close browser & terminal |
| Get help            | Read `TROUBLESHOOTING_GUIDE_FOR_USERS.md`       |



