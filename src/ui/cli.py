"""
Command-line interface for Route Stories.
"""

from typing import Optional
from src.services.route_models import Route, Waypoint
from src.core import Orchestrator, Scheduler, Collector
from src.utils.logger import get_logger
from src.ui.display import (
    display_welcome,
    display_route_info,
    display_waypoint_info,
    display_processing,
    display_waypoint_result,
    display_final_summary_header,
    display_export_info
)
from src.ui.session import process_waypoint
from src.ui.input import get_route_input, prompt_next


logger = get_logger("cli")


class CLI:
    """
    Command-line interface for Route Stories application.
    Handles user interaction and displays results.
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        collector: Collector
    ):
        """
        Initialize CLI.

        Args:
            orchestrator: Orchestrator for processing waypoints
            collector: Collector for organizing results
        """
        self.orchestrator = orchestrator
        self.collector = collector
        logger.info("CLI initialized")

    def display_welcome(self):
        """Display welcome message and instructions."""
        display_welcome()

    def get_route_input(self) -> tuple[str, str]:
        """Get route start and end from user."""
        return get_route_input()

    def display_route_info(self, route: Route):
        """Display route information."""
        display_route_info(route)

    def display_waypoint_info(self, waypoint: Waypoint, index: int, total: int):
        """Display information about current waypoint."""
        display_waypoint_info(waypoint, index, total)

    def display_processing(self, waypoint: Waypoint):
        """Display processing message."""
        display_processing(waypoint)

    def display_waypoint_result(self, waypoint: Waypoint):
        """Display results for a completed waypoint."""
        summary = self.collector.get_waypoint_summary(waypoint.point_id)
        display_waypoint_result(summary)

    def prompt_next(self) -> bool:
        """Prompt user to continue to next waypoint."""
        return prompt_next()

    def display_final_summary(self):
        """Display final summary of all waypoints."""
        display_final_summary_header()
        self.collector.print_summary()

    def display_export_info(self, filepath: str):
        """Display information about exported results."""
        display_export_info(filepath)

    def run_interactive_session(self, route: Route, max_waypoints: Optional[int] = None):
        """Run interactive CLI session for the route using the Scheduler."""
        self.display_route_info(route)
        scheduler = Scheduler(route)
        processed_count = 0

        while scheduler.has_next():
            waypoint = scheduler.get_next()
            if waypoint is None:
                break

            progress = scheduler.get_progress()
            self.display_waypoint_info(waypoint, progress['completed'], progress['total_waypoints'])
            self.display_processing(waypoint)
            process_waypoint(waypoint, route.route_id, self.orchestrator, self.collector)
            self.display_waypoint_result(waypoint)

            scheduler.advance()
            processed_count += 1

            if max_waypoints and processed_count >= max_waypoints:
                logger.info(f"Reached max waypoints limit: {max_waypoints}")
                break

            if scheduler.has_next() and not self.prompt_next():
                logger.info("Session ended by user")
                print("\nSession ended by user.")
                break

        self.display_final_summary()
