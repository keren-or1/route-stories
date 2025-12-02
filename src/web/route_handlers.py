"""
Handler functions for Flask routes.
"""

import time
import threading
from flask import current_app, jsonify

from src.core import Collector
from src.web.route_session import RouteSession
from src.web.service_factory import create_services
from src.web.route_processor import process_route_background


def handle_process_route(data, session_manager, services=None):
    """Handle route processing request."""
    # Create services if not provided
    if services is None:
        settings = current_app.config['SETTINGS']
        services = create_services(settings)

    # Get route from Google Maps
    try:
        route = services['google_maps'].get_route(
            origin=data['start_location'],
            destination=data['end_location'],
            max_waypoints=data['max_points']
        )
    except Exception as e:
        current_app.logger.error(f"Failed to get route: {e}")
        raise

    # Initialize collector
    collector = Collector(
        route_id=route.route_id,
        queue_manager=services['queue_manager']
    )

    # Create session
    session = RouteSession(
        route_id=route.route_id,
        route=route,
        orchestrator=services['orchestrator'],
        collector=collector
    )

    # Store session
    session_manager.add_session(route.route_id, session)

    # Start processing in background thread
    thread = threading.Thread(
        target=process_route_background,
        args=(session,),
        daemon=True
    )
    thread.start()

    return {
        'route_id': route.route_id,
        'total_waypoints': len(route.waypoints),
        'origin': route.origin,
        'destination': route.destination
    }


def handle_get_progress(route_id, session_manager):
    """Handle progress request."""
    session = session_manager.get_session(route_id)

    if not session:
        return None, 'Route not found'

    elapsed_time = time.time() - session.start_time

    # Get current waypoint summary if available
    current_waypoint_info = None
    if session.current_waypoint > 0:
        waypoint_idx = session.current_waypoint - 1
        if waypoint_idx < len(session.route.waypoints):
            waypoint = session.route.waypoints[waypoint_idx]
            current_waypoint_info = {
                'point_id': waypoint.point_id,
                'address': waypoint.address
            }

    return {
        'route_id': route_id,
        'status': session.status,
        'current_waypoint': session.current_waypoint,
        'total_waypoints': session.total_waypoints,
        'progress_percentage': int((session.current_waypoint / session.total_waypoints) * 100),
        'elapsed_time': int(elapsed_time),
        'current_waypoint_info': current_waypoint_info,
        'errors': session.errors
    }, None


def handle_get_results(route_id, session_manager):
    """Handle results request."""
    session = session_manager.get_session(route_id)

    if not session:
        return None, 'Route not found'

    if session.status != 'completed':
        return None, 'Route processing not completed'

    # Get route summary from collector
    summary = session.collector.get_route_summary()

    return summary, None
