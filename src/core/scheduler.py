"""
Scheduler - Manages progression through route waypoints.
"""

from typing import List, Optional, Callable
from src.services.google_maps import Route, Waypoint
from src.utils.logger import get_logger


logger = get_logger("scheduler")


class Scheduler:
    """
    Manages the progression through route waypoints.
    Supports manual advancement (for initial version) and timer-based (future).
    """

    def __init__(self, route: Route):
        """
        Initialize scheduler with a route.

        Args:
            route: Route object with waypoints
        """
        self.route = route
        self.current_index = 0
        self.completed_indices = set()
        logger.info(f"Scheduler initialized for route {route.route_id} with {len(route.waypoints)} waypoints")

    def has_next(self) -> bool:
        """
        Check if there are more waypoints to process.

        Returns:
            True if there are unprocessed waypoints
        """
        return self.current_index < len(self.route.waypoints)

    def get_next(self) -> Optional[Waypoint]:
        """
        Get the next waypoint to process.

        Returns:
            Next Waypoint or None if all processed
        """
        if not self.has_next():
            return None

        waypoint = self.route.waypoints[self.current_index]
        logger.info(f"Next waypoint: {waypoint}")
        return waypoint

    def advance(self) -> bool:
        """
        Advance to the next waypoint.

        Returns:
            True if advanced, False if no more waypoints
        """
        if not self.has_next():
            return False

        self.completed_indices.add(self.current_index)
        self.current_index += 1

        logger.info(f"Advanced to index {self.current_index}")
        return True

    def get_progress(self) -> dict:
        """
        Get current progress information.

        Returns:
            Dictionary with progress stats
        """
        return {
            'current_index': self.current_index,
            'total_waypoints': len(self.route.waypoints),
            'completed': len(self.completed_indices),
            'remaining': len(self.route.waypoints) - self.current_index,
            'progress_percent': (len(self.completed_indices) / len(self.route.waypoints)) * 100
        }

    def reset(self):
        """Reset scheduler to beginning of route."""
        self.current_index = 0
        self.completed_indices.clear()
        logger.info("Scheduler reset")

    def run_manual(
        self,
        process_callback: Callable[[Waypoint], None],
        max_waypoints: Optional[int] = None
    ):
        """
        Run scheduler in manual mode with user confirmation.

        Args:
            process_callback: Function to call for each waypoint
            max_waypoints: Optional limit on number of waypoints to process
        """
        logger.info("Starting manual scheduler mode")

        processed = 0

        while self.has_next():
            waypoint = self.get_next()

            if waypoint is None:
                break

            # Process this waypoint
            process_callback(waypoint)

            # Mark as completed
            self.advance()
            processed += 1

            # Check max waypoints limit
            if max_waypoints and processed >= max_waypoints:
                logger.info(f"Reached max waypoints limit: {max_waypoints}")
                break

        logger.info(f"Manual scheduler completed. Processed {processed} waypoints")

    def get_all_waypoints(self) -> List[Waypoint]:
        """
        Get all waypoints in the route.

        Returns:
            List of all waypoints
        """
        return self.route.waypoints.copy()
