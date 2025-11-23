#!/usr/bin/env python3
"""
Route Stories - Main Entry Point
AI-powered journey content curator using multi-agent system.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.utils import setup_logger, QueueManager
from src.services import GoogleMapsService, GeminiClient, SearchTools
from src.agents import VideoAgent, SongAgent, StoryAgent, JudgeAgent
from src.core import Orchestrator, Collector
from src.ui import CLI


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Route Stories - AI-powered journey content curator"
    )

    parser.add_argument(
        "--start",
        type=str,
        help="Starting location (if not provided, will prompt)"
    )

    parser.add_argument(
        "--end",
        type=str,
        help="Destination (if not provided, will prompt)"
    )

    parser.add_argument(
        "--max-points",
        type=int,
        help="Maximum number of waypoints to process"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--export",
        type=str,
        help="Export results to JSON file"
    )

    return parser.parse_args()


def main():
    """Main application entry point."""

    # Parse arguments
    args = parse_arguments()

    # Load configuration
    try:
        settings = get_settings()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file (copy from .env.example)")
        print("2. Added your GOOGLE_MAPS_API_KEY")
        print("3. Added your GEMINI_API_KEY")
        sys.exit(1)

    # Set log level
    log_level = "DEBUG" if args.verbose else settings.log_level

    # Setup logging
    logger = setup_logger(
        log_level=log_level,
        log_dir=settings.logs_dir,
        enable_console=True,
        enable_file=True
    )

    logger.info("="*80)
    logger.info("Route Stories - Starting Application")
    logger.info("="*80)

    try:
        # Initialize services
        logger.info("Initializing services...")
        google_maps = GoogleMapsService(settings.google_maps_api_key)
        gemini_client = GeminiClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            max_tokens=settings.gemini_max_tokens,
            temperature=settings.gemini_temperature
        )
        search_tools = SearchTools()

        # Initialize agents
        logger.info("Initializing agents...")
        video_agent = VideoAgent(gemini_client, search_tools)
        song_agent = SongAgent(gemini_client, search_tools)
        story_agent = StoryAgent(gemini_client, search_tools)
        judge_agent = JudgeAgent(gemini_client)

        # Initialize queue manager
        queue_manager = QueueManager()

        # Initialize orchestrator
        orchestrator = Orchestrator(
            video_agent=video_agent,
            song_agent=song_agent,
            story_agent=story_agent,
            judge_agent=judge_agent,
            queue_manager=queue_manager
        )

        # Initialize UI
        cli = CLI(orchestrator=None, collector=None)  # Temporary
        cli.display_welcome()

        # Get route input
        if args.start and args.end:
            start_location = args.start
            end_location = args.end
            print(f"\nRoute: {start_location} → {end_location}\n")
        else:
            start_location, end_location = cli.get_route_input()

        # Get route from Google Maps
        logger.info(f"Fetching route: {start_location} -> {end_location}")
        print("\nFetching route from Google Maps...")

        try:
            route = google_maps.get_route(
                origin=start_location,
                destination=end_location,
                max_waypoints=args.max_points or settings.max_waypoints
            )
        except Exception as e:
            logger.error(f"Failed to get route: {e}")
            print(f"\nError: Could not get route from Google Maps")
            print(f"Details: {e}")
            print("\nPlease check:")
            print("- Your Google Maps API key is valid")
            print("- The locations are correct")
            print("- You have enabled the Directions API")
            sys.exit(1)

        # Initialize collector with route
        collector = Collector(route_id=route.route_id, queue_manager=queue_manager)

        # Update CLI with collector
        cli.collector = collector
        cli.orchestrator = orchestrator

        # Run interactive session
        logger.info("Starting interactive session")
        cli.run_interactive_session(
            route=route,
            max_waypoints=args.max_points
        )

        # Export results if requested
        if args.export:
            export_path = Path(args.export)
            collector.export_to_json(export_path)
            cli.display_export_info(str(export_path))
        else:
            # Default export location
            default_export = settings.base_dir / "output" / f"route_{route.route_id}.json"
            collector.export_to_json(default_export)
            cli.display_export_info(str(default_export))

        # Cleanup
        logger.info("Shutting down...")
        orchestrator.shutdown()

        logger.info("Application completed successfully")
        print("\nThank you for using Route Stories!\n")

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n\nApplication interrupted. Goodbye!\n")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"Application error: {e}")
        print(f"\nAn error occurred: {e}")
        print("Check the log files for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
