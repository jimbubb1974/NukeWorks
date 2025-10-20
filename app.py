#!/usr/bin/env python3
"""
NukeWorks - Nuclear Project Management Database
Main application entry point
"""
import os
import sys
import webbrowser
from threading import Timer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the Flask application factory
from app import create_app

# Create Flask application
app = create_app()


def open_browser():
    """Open browser to application URL after short delay"""
    webbrowser.open_new('http://127.0.0.1:5000/')


if __name__ == '__main__':
    # Check if running from PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - open browser automatically
        Timer(1.5, open_browser).start()

    # Print startup information
    print("=" * 60)
    print("NukeWorks - Nuclear Project Management Database")
    print("=" * 60)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print("Database: [none selected yet — user will choose at /select-db]")
    print("Starting Flask server on http://127.0.0.1:5000/")
    print("=" * 60)
    print("\nPress CTRL+C to quit\n")

    # Start Flask server
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=app.config.get('DEBUG', False),
        use_reloader=False  # Disable reloader to prevent double-initialization
    )
