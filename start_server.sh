#!/usr/bin/env bash
# start_server.sh
# Simple helper to run the development server using the project's virtualenv
# Works in Git Bash on Windows, and in Unix-like shells.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd -W)"
VENV_PY="$REPO_ROOT/.venv/Scripts/python"
ALT_VENV_PY="$REPO_ROOT/.venv/bin/python"

# Prefer Windows venv Python (Scripts) for Git Bash; fall back to .venv/bin/python
if [ -x "$VENV_PY" ]; then
  PYTHON="$VENV_PY"
elif [ -x "$ALT_VENV_PY" ]; then
  PYTHON="$ALT_VENV_PY"
else
  echo "No venv python found at $VENV_PY or $ALT_VENV_PY"
  echo "Please create a virtualenv named .venv and install requirements:"
  echo "  python -m venv .venv"
  echo "  .venv/Scripts/pip.exe install -r requirements.txt   # on Windows"
  exit 1
fi

# Run the app
echo "Using python: $PYTHON"
cd "$REPO_ROOT"
"$PYTHON" app.py
