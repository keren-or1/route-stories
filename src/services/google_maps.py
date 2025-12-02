"""
Google Maps API service for route planning and waypoint extraction.
"""

import googlemaps
import uuid
from typing import List, Dict, Any, Optional, Tuple
from src.utils.logger import get_logger
from src.services.route_models import Waypoint, Route
from src.services.waypoint_extractor import extract_waypoints_from_legs


logger = get_logger("google_maps")


class GoogleMapsService:
    """Service for interacting with Google Maps Directions API."""

    def __init__(self, api_key: str):
        """Initialize Google Maps client."""
        self.client = googlemaps.Client(key=api_key)
        logger.info("GoogleMapsService initialized")

    def get_route(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        max_waypoints: Optional[int] = None
    ) -> Route:
        """Get route from origin to destination with waypoints."""
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
            route_id = str(uuid.uuid4())

            # Extract waypoints from the route
            waypoints = extract_waypoints_from_legs(
                legs,
                max_waypoints,
                self.reverse_geocode
            )

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

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates."""
        try:
            result = self.client.geocode(address)
            if result:
                location = result[0]['geometry']['location']
                return (location['lat'], location['lng'])
        except Exception as e:
            logger.error(f"Geocoding failed for '{address}': {e}")
        return None

    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """Convert coordinates to address."""
        try:
            result = self.client.reverse_geocode((lat, lng))
            if result:
                return result[0]['formatted_address']
        except Exception as e:
            logger.error(f"Reverse geocoding failed for ({lat}, {lng}): {e}")
        return None

    def _extract_waypoints(self, legs, max_waypoints):
        """Extract waypoints (backward compatibility)."""
        return extract_waypoints_from_legs(legs, max_waypoints, self.reverse_geocode)

    def _get_step_address(self, step):
        """Get step address (backward compatibility)."""
        from src.services.address_parser import parse_step_address
        return parse_step_address(step, self.reverse_geocode)
