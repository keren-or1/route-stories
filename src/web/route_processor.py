"""
Background route processing logic.
Handles asynchronous route processing in separate threads.
Uses Scheduler to manage waypoint progression according to assignment specifications.
"""

from pathlib import Path
from flask import current_app
from src.core import Scheduler


def process_route_background(session):
    """
    Process route in background thread using Scheduler for waypoint management.

    According to assignment specification section 2.3, the Scheduler is responsible
    for progressing through waypoints one at a time and delivering them to the orchestrator.

    Args:
        session: RouteSession instance
    """
    try:
        route = session.route
        orchestrator = session.orchestrator
        collector = session.collector

        # Create scheduler to manage waypoint progression (per assignment spec)
        scheduler = Scheduler(route)

        # Process waypoints using scheduler
        while scheduler.has_next():
            # Get next waypoint from scheduler
            waypoint = scheduler.get_next()

            if waypoint is None:
                break

            # Update session progress using scheduler state
            progress = scheduler.get_progress()
            session.current_waypoint = progress['completed'] + 1

            # Process waypoint through orchestrator
            results = orchestrator.process_waypoint(
                route_id=route.route_id,
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

            # Advance to next waypoint (per scheduler protocol)
            scheduler.advance()

        # Mark as completed
        session.status = 'completed'

        # Export results
        results_dir = Path(__file__).parent.parent.parent / 'results'
        results_dir.mkdir(exist_ok=True)
        export_path = results_dir / f'route_{session.route_id}.json'
        collector.export_to_json(export_path)

    except Exception as e:
        current_app.logger.exception(f"Error in background processing: {e}")
        session.status = 'error'
        session.errors.append(str(e))
    finally:
        # Shutdown orchestrator
        try:
            orchestrator.shutdown()
        except:
            pass
