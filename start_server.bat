@echo off
REM start_server.bat - Start the development server using the project's .venv on Windows (cmd.exe)
SETLOCAL ENABLEDELAYEDEXPANSION

REM Resolve repo root (directory of this script)
SET REPO_ROOT=%~dp0

REM Remove trailing backslash if present for consistency
IF "%REPO_ROOT:~-1%"=="\" SET REPO_ROOT=%REPO_ROOT:~0,-1%

SET VENV_PY=%REPO_ROOT%\.venv\Scripts\python.exe
SET ALT_VENV_PY=%REPO_ROOT%\.venv\bin\python.exe

IF EXIST "%VENV_PY%" (
  SET PY=%VENV_PY%
) ELSE (
  IF EXIST "%ALT_VENV_PY%" (
    SET PY=%ALT_VENV_PY%
  ) ELSE (
    ECHO No venv python found at %VENV_PY% or %ALT_VENV_PY%
    ECHO To create a venv and install requirements, run these commands in PowerShell or CMD:
    ECHO   python -m venv .venv
    ECHO   .venv\Scripts\pip.exe install -r requirements.txt
    ENDLOCAL
    EXIT /B 1
  )
)

ECHO Using python: "%PY%"
PUSHD "%REPO_ROOT%"
"%PY%" app.py
POPD
ENDLOCAL
