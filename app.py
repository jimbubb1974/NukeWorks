#!/usr/bin/env python3
"""
NukeWorks - Nuclear Project Management Database
Main application entry point
"""
import os
import sys
import socket
import subprocess
from pathlib import Path
import webbrowser
from threading import Timer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# When running as a bundled executable, ensure the bundled Python libs directory
# is on sys.path so importlib.metadata can discover package metadata (e.g., Werkzeug)
if getattr(sys, 'frozen', False):
    try:
        base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).resolve().parent))
    except Exception:
        base_dir = Path(sys.executable).resolve().parent
    internal_dir = base_dir / '_internal'
    if internal_dir.exists() and str(internal_dir) not in sys.path:
        sys.path.insert(0, str(internal_dir))

# Import the Flask application factory
from app import create_app

# Create Flask application
app = create_app()


def is_port_in_use(port):
    """Check if a port is already in use. Returns (in_use, pid) tuple."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()

    if result == 0:  # Port is in use
        # Find the PID using the port on Windows
        try:
            output = subprocess.check_output(
                ['netstat', '-ano'],
                universal_newlines=True,
                stderr=subprocess.DEVNULL
            )
            for line in output.split('\n'):
                if f'127.0.0.1:{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        return True, pid
            return True, None
        except Exception:
            return True, None
    return False, None


def handle_port_conflict(port, pid):
    """Handle port conflict by asking user what to do."""
    print(f"\n⚠️  Port {port} is already in use (PID: {pid})")
    print("\nOptions:")
    print("  [K]ill the existing process and start fresh")
    print("  [C]ancel startup")

    while True:
        choice = input("\nYour choice (K/C): ").strip().upper()
        if choice == 'K':
            try:
                subprocess.run(
                    ['taskkill', '/PID', str(pid), '/F'],
                    check=True,
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL
                )
                print(f"✓ Process {pid} terminated. Starting Flask server...\n")
                return True
            except subprocess.CalledProcessError:
                print(f"✗ Failed to kill process {pid}. Please try manually.")
                return False
        elif choice == 'C':
            print("Startup cancelled.")
            return False
        else:
            print("Invalid choice. Please enter K or C.")


def open_browser():
    """Open browser to application URL after short delay"""
    webbrowser.open_new('http://127.0.0.1:5000/')


if __name__ == '__main__':
    # Check for port conflicts before starting
    port = 5000
    port_in_use, pid = is_port_in_use(port)

    if port_in_use:
        if pid:
            # Ask user what to do
            if not handle_port_conflict(port, pid):
                sys.exit(1)
        else:
            # Port is in use but we couldn't get the PID
            print(f"\n⚠️  Port {port} is already in use but PID could not be determined.")
            print("Please close the existing application or restart your system.")
            sys.exit(1)

    # Check if running from PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - open browser automatically
        Timer(1.5, open_browser).start()

    # Print startup information
    print("=" * 60)
    print("NukeWorks - Nuclear Project Management Database")
    print("=" * 60)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Executable: {sys.executable}")
    print(f"Frozen (PyInstaller): {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        print(f"Bundle Root (_MEIPASS): {getattr(sys, '_MEIPASS', 'N/A')}")
    print()
    print("⚠️  IMPORTANT: No default database connection")
    print("   You MUST select a database at /select-db before using the app")
    print("   This prevents accidental use of local cached databases")
    print()
    print("Database: [none selected yet — user will choose at /select-db]")
    print("Starting Flask server on http://127.0.0.1:5000/")
    print("=" * 60)
    print("\n📋 FIRST TIME SETUP:")
    print("   1. Browser will open to database selection page")
    print("   2. Select or browse to a .sqlite database file")
    print("   3. If database is empty, you'll need to initialize it")
    print("   4. Default login: admin / admin123")
    print("\nPress CTRL+C to quit\n")

    # Start Flask server
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=app.config.get('DEBUG', False),
        use_reloader=False  # Disable reloader to prevent double-initialization
    )
