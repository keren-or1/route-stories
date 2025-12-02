#!/usr/bin/env python3
"""
Route Stories - Main Entry Point
AI-powered journey content curator using multi-agent system.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.main_init import initialize_services
from src.main_runner import run_application


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Route Stories - AI-powered journey content curator"
    )

    parser.add_argument(
        "--start",
        type=str,
        help="Starting location (if not provided, will prompt)"
    )

    parser.add_argument(
        "--end",
        type=str,
        help="Destination (if not provided, will prompt)"
    )

    parser.add_argument(
        "--max-points",
        type=int,
        help="Maximum number of waypoints to process"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--export",
        type=str,
        help="Export results to JSON file"
    )

    return parser.parse_args()


def main():
    """Main application entry point."""
    # Parse arguments
    args = parse_arguments()

    # Load configuration
    try:
        settings = get_settings()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file (copy from .env.example)")
        print("2. Added your GOOGLE_MAPS_API_KEY")
        print("3. Added your GEMINI_API_KEY")
        sys.exit(1)

    # Set log level
    log_level = "DEBUG" if args.verbose else settings.log_level

    try:
        # Initialize services
        services = initialize_services(settings, log_level)

        # Run application
        run_application(services, args, settings)

    except KeyboardInterrupt:
        services['logger'].info("Application interrupted by user")
        print("\n\nApplication interrupted. Goodbye!\n")
        sys.exit(0)

    except Exception as e:
        if 'logger' in services:
            services['logger'].exception(f"Application error: {e}")
        print(f"\nAn error occurred: {e}")
        print("Check the log files for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
