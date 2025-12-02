"""
Data models for routes and waypoints.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Waypoint:
    """Represents a waypoint along the route."""
    point_id: int
    address: str
    location: Dict[str, float]
    distance_from_start: Optional[int] = None
    duration_from_start: Optional[int] = None

    def __repr__(self):
        return f"Waypoint(id={self.point_id}, address='{self.address}')"


@dataclass
class Route:
    """Represents a complete route with waypoints."""
    route_id: str
    origin: str
    destination: str
    waypoints: List[Waypoint]
    total_distance: int
    total_duration: int

    def __repr__(self):
        return (f"Route(id={self.route_id}, origin='{self.origin}', "
                f"destination='{self.destination}', waypoints={len(self.waypoints)})")
