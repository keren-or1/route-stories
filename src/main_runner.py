"""
Execution logic for main application.
"""

import sys
from pathlib import Path
from src.core import Collector
from src.ui import CLI


def get_route_input(args, cli):
    """Get route input from args or user."""
    if args.start and args.end:
        print(f"\nRoute: {args.start} → {args.end}\n")
        return args.start, args.end
    else:
        return cli.get_route_input()


def fetch_route(google_maps, start_location, end_location, max_points, settings, logger):
    """Fetch route from Google Maps."""
    logger.info(f"Fetching route: {start_location} -> {end_location}")
    print("\nFetching route from Google Maps...")

    try:
        return google_maps.get_route(
            origin=start_location,
            destination=end_location,
            max_waypoints=max_points or settings.max_waypoints
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


def export_results(collector, args, settings, route, cli):
    """Export results to JSON file."""
    if args.export:
        export_path = Path(args.export)
        collector.export_to_json(export_path)
        cli.display_export_info(str(export_path))
    else:
        # Default export location
        default_export = settings.base_dir / "output" / f"route_{route.route_id}.json"
        collector.export_to_json(default_export)
        cli.display_export_info(str(default_export))


def run_application(services, args, settings):
    """Run the main application flow."""
    logger = services['logger']
    google_maps = services['google_maps']
    orchestrator = services['orchestrator']
    queue_manager = services['queue_manager']

    # Initialize UI
    cli = CLI(orchestrator=None, collector=None)
    cli.display_welcome()

    # Get route input
    start_location, end_location = get_route_input(args, cli)

    # Get route from Google Maps
    route = fetch_route(google_maps, start_location, end_location, args.max_points, settings, logger)

    # Initialize collector with route
    collector = Collector(route_id=route.route_id, queue_manager=queue_manager)

    # Update CLI with collector
    cli.collector = collector
    cli.orchestrator = orchestrator

    # Run interactive session
    logger.info("Starting interactive session")
    cli.run_interactive_session(route=route, max_waypoints=args.max_points)

    # Export results
    export_results(collector, args, settings, route, cli)

    # Cleanup
    logger.info("Shutting down...")
    orchestrator.shutdown()

    logger.info("Application completed successfully")
    print("\nThank you for using Route Stories!\n")
