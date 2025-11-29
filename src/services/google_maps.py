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
        Filters out trivial turn-by-turn directions and focuses on meaningful locations.

        Args:
            step: Step dictionary from Google Maps API

        Returns:
            Address string or meaningful location name
        """
        import re

        # List of trivial direction keywords to filter out
        trivial_keywords = [
            'head', 'turn', 'continue', 'bear', 'go', 'keep', 'merge',
            'enter', 'exit', 'take', 'make', 'slight', 'sharp', 'right', 'left'
        ]

        # Try to extract from HTML instructions, but SKIP all turn-by-turn directions
        if 'html_instructions' in step:
            html = step['html_instructions']
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html)
            text_lower = text.lower().strip()

            # Check if this is a trivial direction (starts with direction verb)
            starts_with_direction = any(
                text_lower.startswith(keyword) for keyword in trivial_keywords
            )

            # Only use the instruction if it's NOT a direction and has meaningful length
            if not starts_with_direction and len(text) > 3:
                # Additional check: only use if it mentions actual places/landmarks
                # (not just roads, highways, etc.)
                return text

        # For trivial directions or no instructions, use reverse geocoding to get actual location
        try:
            loc = step['end_location']
            address = self.reverse_geocode(loc['lat'], loc['lng'])
            if address:
                # Extract just the main location (not full address)
                parts = address.split(',')
                # Prefer city/area name over street addresses
                if len(parts) >= 2:
                    # Try to get meaningful location (city, area, landmark)
                    return parts[0].strip() + ', ' + parts[1].strip()
                if parts[0].strip():
                    return parts[0].strip()
        except Exception as e:
            self.logger.debug(f"Reverse geocoding failed: {e}")
            pass

        # Fallback: use coordinates (better than bogus instructions)
        loc = step['end_location']
        return f"Location ({loc['lat']:.4f}, {loc['lng']:.4f})"

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
