"""
Command-line interface for Route Stories.
"""

import sys
from typing import Optional
from src.services.google_maps import Route, Waypoint
from src.core import Orchestrator, Scheduler, Collector
from src.utils.logger import get_logger


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
        print("\n" + "="*80)
        print(" "*25 + "ROUTE STORIES")
        print(" "*15 + "AI-Powered Journey Content Curator")
        print("="*80)
        print("\nWelcome! This system will find engaging content for each stop")
        print("along your route - videos, songs, and historical stories.\n")

    def get_route_input(self) -> tuple[str, str]:
        """
        Get route start and end from user.

        Returns:
            Tuple of (start, end) locations
        """
        print("Please enter your route details:")
        print("-" * 80)

        start = input("Starting location: ").strip()
        if not start:
            print("Error: Starting location cannot be empty")
            sys.exit(1)

        end = input("Destination: ").strip()
        if not end:
            print("Error: Destination cannot be empty")
            sys.exit(1)

        return start, end

    def display_route_info(self, route: Route):
        """
        Display route information.

        Args:
            route: Route object
        """
        print("\n" + "="*80)
        print("ROUTE INFORMATION")
        print("="*80)
        print(f"From: {route.origin}")
        print(f"To: {route.destination}")
        print(f"Total Distance: {route.total_distance / 1000:.1f} km")
        print(f"Estimated Duration: {route.total_duration / 60:.0f} minutes")
        print(f"Waypoints: {len(route.waypoints)}")
        print("="*80 + "\n")

    def display_waypoint_info(self, waypoint: Waypoint, index: int, total: int):
        """
        Display information about current waypoint.

        Args:
            waypoint: Waypoint object
            index: Current waypoint index (0-based)
            total: Total number of waypoints
        """
        print("\n" + "-"*80)
        print(f"WAYPOINT {index + 1} of {total}")
        print("-"*80)
        print(f"Location: {waypoint.address}")
        print(f"Coordinates: {waypoint.location['lat']:.6f}, {waypoint.location['lng']:.6f}")

        if waypoint.distance_from_start:
            print(f"Distance from start: {waypoint.distance_from_start / 1000:.1f} km")

        print("-"*80)

    def display_processing(self, waypoint: Waypoint):
        """
        Display processing message.

        Args:
            waypoint: Waypoint being processed
        """
        print(f"\nSearching for content about: {waypoint.address}")
        print("This may take a moment...")
        print("\nAgents working:")
        print("  [*] Video Agent - searching YouTube...")
        print("  [*] Song Agent - searching music...")
        print("  [*] Story Agent - searching historical facts...")
        print("  [*] Judge Agent - evaluating options...\n")

    def display_waypoint_result(self, waypoint: Waypoint):
        """
        Display results for a completed waypoint.

        Args:
            waypoint: Waypoint that was processed
        """
        summary = self.collector.get_waypoint_summary(waypoint.point_id)

        if not summary:
            print("\nError: No results collected for this waypoint\n")
            return

        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)

        if summary.errors:
            print("\nWarnings/Errors:")
            for error in summary.errors:
                print(f"  ⚠ {error}")

        if summary.chosen_type and summary.chosen_content:
            content = summary.chosen_content

            print(f"\n✓ SELECTED CONTENT: {summary.chosen_type.upper()}")
            print("-"*80)

            if summary.chosen_type == 'video':
                print(f"Title: {content.get('title', 'N/A')}")
                print(f"Channel: {content.get('channel', 'N/A')}")
                print(f"Duration: {content.get('duration', 'N/A')}")
                print(f"Views: {content.get('views', 'N/A')}")
                print(f"Description: {content.get('description', 'N/A')[:150]}...")
                print(f"URL: {content.get('url', 'N/A')}")

            elif summary.chosen_type == 'song':
                print(f"Title: {content.get('title', 'N/A')}")
                print(f"Artist: {content.get('artist', 'N/A')}")
                print(f"Genre: {content.get('genre', 'N/A')}")
                print(f"Duration: {content.get('duration', 'N/A')}")
                print(f"Album: {content.get('album', 'N/A')}")
                print(f"URL: {content.get('url', 'N/A')}")

            elif summary.chosen_type == 'story':
                print(f"Title: {content.get('title', 'N/A')}")
                print(f"Content: {content.get('content', 'N/A')}")
                print(f"Source: {content.get('source', 'N/A')}")
                print(f"Period: {content.get('period', 'N/A')}")
                print(f"URL: {content.get('url', 'N/A')}")

            print()

            if summary.judge_reasoning:
                print(f"Judge's Reasoning: {summary.judge_reasoning}")

            if summary.judge_score is not None:
                print(f"Confidence Score: {summary.judge_score}/100")

        else:
            print("\n✗ No content selected (processing failed)")

        print("="*80)

    def prompt_next(self) -> bool:
        """
        Prompt user to continue to next waypoint.

        Returns:
            True if user wants to continue, False to stop
        """
        print("\n" + "-"*80)
        response = input("Press Enter to continue to next waypoint (or 'q' to quit): ").strip().lower()

        if response == 'q' or response == 'quit':
            return False

        return True

    def display_final_summary(self):
        """Display final summary of all waypoints."""
        print("\n\n" + "="*80)
        print(" "*25 + "JOURNEY COMPLETE")
        print("="*80)

        self.collector.print_summary()

    def display_export_info(self, filepath: str):
        """
        Display information about exported results.

        Args:
            filepath: Path to exported file
        """
        print(f"\nResults exported to: {filepath}")
        print("You can review the complete journey data in this file.\n")

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

        # Determine how many waypoints to process
        waypoints_to_process = route.waypoints
        if max_waypoints and max_waypoints < len(waypoints_to_process):
            waypoints_to_process = waypoints_to_process[:max_waypoints]
            print(f"Processing first {max_waypoints} waypoints only.\n")

        # Process each waypoint
        for index, waypoint in enumerate(waypoints_to_process):
            # Display waypoint info
            self.display_waypoint_info(waypoint, index, len(waypoints_to_process))

            # Display processing message
            self.display_processing(waypoint)

            # Process waypoint with orchestrator
            results = self.orchestrator.process_waypoint(
                route_id=route.route_id,
                point_id=waypoint.point_id,
                address=waypoint.address,
                location=waypoint.location
            )

            # Collect results
            self.collector.collect_waypoint(
                point_id=waypoint.point_id,
                address=waypoint.address,
                location=waypoint.location,
                results=results
            )

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
