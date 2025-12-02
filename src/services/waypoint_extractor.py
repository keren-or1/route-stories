"""
Waypoint extraction logic from Google Maps route legs.
"""

from typing import List, Dict, Any, Optional
from src.services.route_models import Waypoint
from src.services.address_parser import parse_step_address
from src.utils.logger import get_logger


logger = get_logger("waypoint_extractor")


def extract_waypoints_from_legs(
    legs: List[Dict[str, Any]],
    max_waypoints: Optional[int],
    reverse_geocode_fn: callable
) -> List[Waypoint]:
    """
    Extract waypoints from route legs.

    Args:
        legs: Route legs from Google Maps API
        max_waypoints: Maximum number of waypoints to extract
        reverse_geocode_fn: Function to reverse geocode coordinates

    Returns:
        List of Waypoint objects
    """
    waypoints = []
    point_id = 0
    cumulative_distance = 0
    cumulative_duration = 0

    for leg in legs:
        # Add start location of leg
        if point_id == 0:
            waypoints.append(Waypoint(
                point_id=point_id,
                address=leg['start_address'],
                location=leg['start_location'],
                distance_from_start=0,
                duration_from_start=0
            ))
            point_id += 1

        # Extract intermediate steps as waypoints
        steps = leg.get('steps', [])

        # Determine step interval to stay within max_waypoints
        if max_waypoints and len(steps) > max_waypoints - len(waypoints):
            step_interval = max(1, len(steps) // (max_waypoints - len(waypoints)))
        else:
            step_interval = max(1, len(steps) // 5)  # Default: ~5 waypoints per leg

        for i, step in enumerate(steps):
            if i % step_interval == 0:
                cumulative_distance += step['distance']['value']
                cumulative_duration += step['duration']['value']

                # Try to get a meaningful address for the waypoint
                address = parse_step_address(step, reverse_geocode_fn)

                # Skip waypoints with empty addresses
                if not address or not address.strip():
                    logger.debug("Skipping waypoint with empty address")
                    continue

                waypoints.append(Waypoint(
                    point_id=point_id,
                    address=address,
                    location=step['end_location'],
                    distance_from_start=cumulative_distance,
                    duration_from_start=cumulative_duration
                ))
                point_id += 1

                if max_waypoints and len(waypoints) >= max_waypoints - 1:
                    break

        if max_waypoints and len(waypoints) >= max_waypoints - 1:
            break

    # Always add the final destination
    final_leg = legs[-1]
    waypoints.append(Waypoint(
        point_id=point_id,
        address=final_leg['end_address'],
        location=final_leg['end_location'],
        distance_from_start=cumulative_distance + final_leg['distance']['value'],
        duration_from_start=cumulative_duration + final_leg['duration']['value']
    ))

    logger.info(f"Extracted {len(waypoints)} waypoints")
    return waypoints
