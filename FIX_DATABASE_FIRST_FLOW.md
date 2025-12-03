# Database-First Authentication Flow - Fix Applied

## Problem

The executable was redirecting users to `/select-db` but that route required `@login_required`, creating a circular dependency:

1. User tries to access app → redirected to `/select-db` (no database selected)
2. `/select-db` requires login → redirected to `/auth/login`
3. Login tries to authenticate → **fails because no database is selected** (no User table to query)
4. User stuck in loop

## Root Cause

Line 22 of `app/routes/db_select.py` had `@login_required` decorator on the GET route:

```python
@bp.route('/select-db', methods=['GET'])
@login_required  # ← THIS WAS THE PROBLEM
def select_database():
```

This contradicted the **Database-First Architecture** design documented in:

- `docs/DB_SELECTION_SPEC.md` (lines 84-115)
- `app/__init__.py` middleware comments (lines 612-639)

## Solution Applied

**Removed** `@login_required` from the database selection GET route:

```python
@bp.route('/select-db', methods=['GET'])
def select_database():
    """
    Show database selector page
    Displays scanned databases and allows browsing

    NOTE: No @login_required - this MUST be accessible before login
    This is the entry point for unauthenticated users to select a database
    """
```

## Correct Flow (After Fix)

### For First-Time Users (No Database Selected)

1. User runs `NukeWorks.exe` → Flask starts
2. User navigates to `http://127.0.0.1:5000/`
3. Middleware detects no `session['selected_db_path']` → **redirects to `/select-db`**
4. User sees database selection page (unauthenticated, no login required)
5. User selects a database file (e.g., `dev_nukeworks.sqlite`)
6. POST to `/select-db` validates database and sets `session['selected_db_path']`
7. **Now redirects to `/auth/login`** (because `current_user.is_authenticated == False`)
8. User enters credentials (which are now queryable from the selected database)
9. Login succeeds → redirect to dashboard

### For Authenticated Users Switching Databases

1. User clicks "Database" link in navigation (while logged in)
2. Sees `/select-db` page with current selection and other options
3. Selects different database → validates → switches
4. Stays logged in, redirects to dashboard with new database

## Files Modified

- `app/routes/db_select.py` (line 20-27) - Removed `@login_required` decorator and added explanatory comment

## Testing Instructions

1. **Delete** `instance/db_selector.json` (to clear cached database selection)
2. Run `dist\NukeWorks\NukeWorks.exe`
3. Navigate to `http://127.0.0.1:5000/`
4. Should see **database selection page** (NOT login page)
5. Browse to a database file (e.g., `dev_nukeworks.sqlite`)
6. Click "Select Database"
7. Should now see **login page**
8. Enter credentials: `admin` / `admin123` (or whatever is in the selected database)
9. Should successfully log in and see dashboard

## Important Notes

- The database MUST have the `users` table with at least one user
- First-time setup: use `flask init-db-cmd` to create default admin user
- For distribution: include a sample database with default credentials in the `databases/` directory
- The POST route to `/select-db` does NOT require authentication (allows anonymous users to select DB before login)

## Related Files

- `app/__init__.py` - Middleware that enforces database selection (lines 527-669)
- `app/routes/db_select.py` - Database selection routes
- `docs/DB_SELECTION_SPEC.md` - Architecture specification
- `docs/DB_SELECTION_IMPLEMENTATION.md` - Implementation details

## Build Date

- Fix applied: October 28, 2025
- Rebuilt executable: `dist\NukeWorks\NukeWorks.exe`



