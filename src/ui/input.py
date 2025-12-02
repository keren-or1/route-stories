"""
User input utilities for CLI.
"""

import sys


def get_route_input() -> tuple[str, str]:
    """
    Get route start and end from user.

    Returns:
        Tuple of (start, end) locations
    """
    print("Please enter your route details:")
    print("-" * 80)

    start = input("Starting location: ").strip()
    if not start:
        print("Error: Starting location cannot be empty")
        sys.exit(1)

    end = input("Destination: ").strip()
    if not end:
        print("Error: Destination cannot be empty")
        sys.exit(1)

    return start, end


def prompt_next() -> bool:
    """
    Prompt user to continue to next waypoint.

    Returns:
        True if user wants to continue, False to stop
    """
    print("\n" + "-"*80)
    response = input("Press Enter to continue to next waypoint (or 'q' to quit): ").strip().lower()

    if response == 'q' or response == 'quit':
        return False

    return True
