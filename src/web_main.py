#!/usr/bin/env python3
"""
Route Stories - Web UI Entry Point
Starts the Flask web server for the Route Stories application.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.web import create_app


def main():
    """
    Start the Flask web server.
    """
    print("=" * 80)
    print("Route Stories - Web UI")
    print("=" * 80)
    print("\nStarting Flask web server...")
    print("\nAccess the application at: http://localhost:5000")
    print("\nPress CTRL+C to stop the server\n")
    print("=" * 80)

    # Create Flask app
    app = create_app()

    # Run development server
    # Note: In production, use a WSGI server like Gunicorn or uWSGI
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutting down server... Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting server: {e}")
        print("Please check your configuration and try again.\n")
        sys.exit(1)
