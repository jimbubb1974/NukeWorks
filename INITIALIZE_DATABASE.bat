@echo off
REM ============================================================
REM NukeWorks Database Initialization Helper
REM This script creates a new database with default admin user
REM ============================================================

echo.
echo ============================================================
echo NukeWorks Database Initialization
echo ============================================================
echo.
echo This will create a new database file with:
echo   - All required tables
echo   - Default admin user (username: admin, password: admin123)
echo   - Default system settings
echo.

REM Get database file path from user
set /p DB_PATH="Enter the database file path (e.g., my_database.sqlite): "

if "%DB_PATH%"=="" (
    echo ERROR: No path provided
    pause
    exit /b 1
)

REM Check if file already exists
if exist "%DB_PATH%" (
    echo.
    echo WARNING: File already exists: %DB_PATH%
    echo.
    set /p CONFIRM="Overwrite existing file? This will DELETE all existing data! (yes/no): "
    if /i not "%CONFIRM%"=="yes" (
        echo Operation cancelled.
        pause
        exit /b 1
    )
    del "%DB_PATH%"
)

echo.
echo Creating database: %DB_PATH%
echo.

REM Create empty database file
type nul > "%DB_PATH%"

if not exist "%DB_PATH%" (
    echo ERROR: Failed to create database file
    echo Check that you have write permissions to this location
    pause
    exit /b 1
)

REM Initialize database using Python
echo Initializing database tables and default user...
echo.

REM Try to use bundled Python or system Python
set PYTHON_CMD=python
if exist "NukeWorks.exe" (
    REM Running alongside the executable - use system Python
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found in system PATH
        echo Please install Python or run this from the development environment
        pause
        exit /b 1
    )
)

REM Set environment variable to point to this database
set NUKEWORKS_DB_PATH=%DB_PATH%

REM Run initialization script
python -c "import os; os.environ['NUKEWORKS_DB_PATH'] = r'%DB_PATH%'; from app import create_app; from app.utils.db_init import init_database; app = create_app(); init_database(app.db_session); print('\n=== Database initialized successfully! ==='); print('Location: %DB_PATH%'); print('Default login: admin / admin123'); print('\nYou can now start NukeWorks and select this database.')"

if errorlevel 1 (
    echo.
    echo ERROR: Database initialization failed
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS!
echo ============================================================
echo Database created at: %DB_PATH%
echo Default username: admin
echo Default password: admin123
echo.
echo IMPORTANT: Change the admin password after first login!
echo ============================================================
echo.
pause




