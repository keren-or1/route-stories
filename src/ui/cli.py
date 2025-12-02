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
from src.ui.session import process_waypoint, get_waypoints_to_process
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

    def run_interactive_session(
        self,
        route: Route,
        max_waypoints: Optional[int] = None
    ):
        """
        Run an interactive CLI session for the route.

        Args:
            route: Route to process
            max_waypoints: Optional limit on waypoints to process
        """
        # Display route info
        self.display_route_info(route)

        # Create scheduler
        scheduler = Scheduler(route)

        # Get waypoints to process
        waypoints_to_process = get_waypoints_to_process(route, max_waypoints)

        # Process each waypoint
        for index, waypoint in enumerate(waypoints_to_process):
            # Display waypoint info
            self.display_waypoint_info(waypoint, index, len(waypoints_to_process))

            # Display processing message
            self.display_processing(waypoint)

            # Process waypoint
            process_waypoint(waypoint, route.route_id, self.orchestrator, self.collector)

            # Display results
            self.display_waypoint_result(waypoint)

            # Check if there are more waypoints
            if index < len(waypoints_to_process) - 1:
                # Prompt to continue
                if not self.prompt_next():
                    print("\nSession ended by user.")
                    break

        # Display final summary
        self.display_final_summary()
