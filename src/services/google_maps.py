"""
Google Maps API service for route planning and waypoint extraction.
"""

import googlemaps
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from src.utils.logger import get_logger


logger = get_logger("google_maps")


@dataclass
class Waypoint:
    """Represents a waypoint along the route."""
    point_id: int
    address: str
    location: Dict[str, float]  # {'lat': ..., 'lng': ...}
    distance_from_start: Optional[int] = None  # meters
    duration_from_start: Optional[int] = None  # seconds

    def __repr__(self):
        return f"Waypoint(id={self.point_id}, address='{self.address}')"


@dataclass
class Route:
    """Represents a complete route with waypoints."""
    route_id: str
    origin: str
    destination: str
    waypoints: List[Waypoint]
    total_distance: int  # meters
    total_duration: int  # seconds

    def __repr__(self):
        return (f"Route(id={self.route_id}, origin='{self.origin}', "
                f"destination='{self.destination}', waypoints={len(self.waypoints)})")


class GoogleMapsService:
    """
    Service for interacting with Google Maps Directions API.
    Retrieves routes and extracts waypoints for content enrichment.
    """

    def __init__(self, api_key: str):
        """
        Initialize Google Maps client.

        Args:
            api_key: Google Maps API key
        """
        self.client = googlemaps.Client(key=api_key)
        logger.info("GoogleMapsService initialized")

    def get_route(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        max_waypoints: Optional[int] = None
    ) -> Route:
        """
        Get route from origin to destination with waypoints.

        Args:
            origin: Starting location (address or coordinates)
            destination: Ending location (address or coordinates)
            mode: Travel mode (driving, walking, bicycling, transit)
            max_waypoints: Maximum number of waypoints to extract

        Returns:
            Route object with waypoints

        Raises:
            Exception: If API call fails or no route found
        """
        logger.info(f"Requesting route: {origin} -> {destination}")

        try:
            # Get directions from Google Maps
            directions_result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                alternatives=False
            )

            if not directions_result:
                raise Exception("No route found")

            # Extract the first (best) route
            route_data = directions_result[0]
            legs = route_data['legs']

            # Generate unique route ID
            route_id = str(uuid.uuid4())

            # Extract waypoints from the route
            waypoints = self._extract_waypoints(legs, max_waypoints)

            # Calculate total distance and duration
            total_distance = sum(leg['distance']['value'] for leg in legs)
            total_duration = sum(leg['duration']['value'] for leg in legs)

            route = Route(
                route_id=route_id,
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                total_distance=total_distance,
                total_duration=total_duration
            )

            logger.info(f"Route created: {route}")
            return route

        except Exception as e:
            logger.error(f"Failed to get route: {e}")
            raise

    def _extract_waypoints(
        self,
        legs: List[Dict[str, Any]],
        max_waypoints: Optional[int]
    ) -> List[Waypoint]:
        """
        Extract waypoints from route legs.

        Args:
            legs: Route legs from Google Maps API
            max_waypoints: Maximum number of waypoints to extract

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
                    address = self._get_step_address(step)

                    # Skip waypoints with empty addresses (couldn't get meaningful location)
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

    def _get_step_address(self, step: Dict[str, Any]) -> str:
        """
        Extract meaningful address from a route step.
        Prioritizes location information from turn-by-turn directions,
        falls back to reverse geocoding, then returns street names as last resort.

        Args:
            step: Step dictionary from Google Maps API

        Returns:
            Address string or meaningful location name
        """
        import re

        # Direction keywords that indicate turn-by-turn instructions
        direction_keywords = [
            'head', 'turn', 'continue', 'bear', 'go', 'keep', 'merge',
            'enter', 'exit', 'take', 'make', 'slight', 'sharp', 'right', 'left'
        ]

        # Try to extract from HTML instructions
        if 'html_instructions' in step:
            html = step['html_instructions']
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html)
            text_lower = text.lower().strip()

            # Check if this is a trivial direction (starts with direction verb)
            starts_with_direction = any(
                text_lower.startswith(keyword) for keyword in direction_keywords
            )

            # If it's NOT a direction, use the full instruction as-is
            if not starts_with_direction and len(text) > 3:
                return text

            # If it IS a direction, extract the street/location name that comes after the verb
            # Pattern: "Head [left/right/straight] on [Street Name]" or "Turn [direction] onto [Street Name]"
            if starts_with_direction:
                # Extract everything after prepositions like "on", "onto", "to"
                match = re.search(r'\b(?:on|onto|to|toward)\s+([A-Z][^,]+)', text)
                if match:
                    street_name = match.group(1).strip()
                    # Only use if it looks like a real street name (has letters, reasonable length)
                    if len(street_name) > 2 and street_name not in ['right', 'left', 'straight']:
                        return street_name

        # Try reverse geocoding for more detailed location information
        try:
            loc = step['end_location']
            address = self.reverse_geocode(loc['lat'], loc['lng'])
            if address:
                # Extract just the main location (not full address)
                parts = address.split(',')
                # Prefer first meaningful part (usually street or area name)
                if len(parts) >= 2:
                    return parts[0].strip() + ', ' + parts[1].strip()
                if parts[0].strip():
                    return parts[0].strip()
        except Exception as e:
            logger.debug(f"Reverse geocoding failed: {e}")
            pass

        # Final fallback: try to extract any street name from the instruction
        if 'html_instructions' in step:
            html = step['html_instructions']
            text = re.sub(r'<[^>]+>', '', html)
            # Try to find a capitalized location/street name in the instruction
            match = re.search(r'\b([A-Z][a-zA-Z\s]+(?:St|Road|Ave|Blvd|Street|Highway|Drive|Lane|Rd|Av)\.?)\b', text)
            if match:
                return match.group(1).strip()

        # Only return empty string if absolutely no meaningful location found
        logger.debug(f"Could not extract meaningful address for step, skipping")
        return ""

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to coordinates.

        Args:
            address: Address string

        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        try:
            result = self.client.geocode(address)
            if result:
                location = result[0]['geometry']['location']
                return (location['lat'], location['lng'])
        except Exception as e:
            logger.error(f"Geocoding failed for '{address}': {e}")
        return None

    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert coordinates to address.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Address string or None if reverse geocoding fails
        """
        try:
            result = self.client.reverse_geocode((lat, lng))
            if result:
                return result[0]['formatted_address']
        except Exception as e:
            logger.error(f"Reverse geocoding failed for ({lat}, {lng}): {e}")
        return None
