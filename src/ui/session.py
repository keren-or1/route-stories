"""
Interactive session management for CLI.
"""

from typing import Optional
from src.services.route_models import Route, Waypoint
from src.core import Orchestrator, Collector


def process_waypoint(
    waypoint: Waypoint,
    route_id: str,
    orchestrator: Orchestrator,
    collector: Collector
) -> None:
    """
    Process a single waypoint.

    Args:
        waypoint: Waypoint to process
        route_id: Route identifier
        orchestrator: Orchestrator for processing
        collector: Collector for results
    """
    # Process waypoint with orchestrator
    results = orchestrator.process_waypoint(
        route_id=route_id,
        point_id=waypoint.point_id,
        address=waypoint.address,
        location=waypoint.location
    )

    # Collect results
    collector.collect_waypoint(
        point_id=waypoint.point_id,
        address=waypoint.address,
        location=waypoint.location,
        results=results
    )


def get_waypoints_to_process(
    route: Route,
    max_waypoints: Optional[int]
) -> list[Waypoint]:
    """
    Get list of waypoints to process.

    Args:
        route: Route object
        max_waypoints: Optional limit

    Returns:
        List of waypoints to process
    """
    waypoints = route.waypoints

    if max_waypoints and max_waypoints < len(waypoints):
        waypoints = waypoints[:max_waypoints]
        print(f"Processing first {max_waypoints} waypoints only.\n")

    return waypoints
