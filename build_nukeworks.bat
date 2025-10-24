@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo NukeWorks Build Script
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist venv\ (
    echo ERROR: Virtual environment not found at venv\
    echo Please create it first:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check and install PyInstaller if needed
echo Checking for PyInstaller...
python -c "import PyInstaller" 2>nul
if !errorlevel! neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds (always clean for consistency)
echo Cleaning previous build artifacts...
if exist build\ rmdir /s /q build
if exist dist\ rmdir /s /q dist

REM Build the executable with best practices
echo.
echo ============================================================
echo Building NukeWorks executable...
echo ============================================================
python installer\build_executable.py
if !errorlevel! neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM Build the installer (comment out to skip)
REM echo.
REM echo ============================================================
REM echo Building Windows installer...
REM echo ============================================================
REM powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
REM if !errorlevel! neq 0 (
REM     echo ERROR: Installer build failed!
REM     pause
REM     exit /b 1
REM )

echo.
echo ============================================================
echo Build Complete!
echo ============================================================
echo Executable location: dist\NukeWorks\NukeWorks.exe
echo.
echo To test the executable, run:
echo   dist\NukeWorks\NukeWorks.exe
echo.
REM echo Installer location: installer\out\NukeWorks-1.0.0-Setup.exe
REM echo.

pause


