@echo off
REM NukeWorks Uninstaller - Batch wrapper
REM This script runs the PowerShell uninstaller with proper permissions

echo ==========================================
echo NukeWorks Uninstaller
echo ==========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator - OK
) else (
    echo ERROR: This uninstaller must be run as Administrator.
    echo Please right-click and "Run as Administrator"
    pause
    exit /b 1
)

echo.
echo Starting NukeWorks uninstall...
echo.

REM Run the PowerShell uninstaller
powershell.exe -ExecutionPolicy Bypass -File "%~dp0uninstall_nukeworks.ps1"

echo.
echo Uninstall process completed.
pause

