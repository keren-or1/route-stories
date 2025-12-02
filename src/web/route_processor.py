"""
Background route processing logic.
Handles asynchronous route processing in separate threads.
"""

from pathlib import Path
from flask import current_app


def process_route_background(session):
    """
    Process route in background thread.

    Args:
        session: RouteSession instance
    """
    try:
        route = session.route
        orchestrator = session.orchestrator
        collector = session.collector

        # Process each waypoint
        for idx, waypoint in enumerate(route.waypoints):
            session.current_waypoint = idx + 1

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
