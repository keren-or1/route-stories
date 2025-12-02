"""
Request validation utilities for web routes.
Validates and parses incoming route requests.
"""

from typing import Tuple, Optional, Dict, Any


def validate_route_request(data: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate route processing request data.

    Args:
        data: Request JSON data

    Returns:
        Tuple of (is_valid, error_message, parsed_data)
    """
    if not data:
        return False, 'No data provided', {}

    start_location = data.get('start', '').strip()
    end_location = data.get('end', '').strip()
    max_points = data.get('max_points', 5)

    if not start_location or not end_location:
        return False, 'Start and end locations are required', {}

    # Validate max_points
    try:
        max_points = int(max_points)
        if max_points < 2 or max_points > 20:
            return False, 'Max waypoints must be between 2 and 20', {}
    except ValueError:
        return False, 'Invalid max_points value', {}

    parsed_data = {
        'start_location': start_location,
        'end_location': end_location,
        'max_points': max_points
    }

    return True, None, parsed_data
