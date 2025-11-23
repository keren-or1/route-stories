"""
Flask routes for Route Stories web UI.
"""

import time
import uuid
import threading
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import datetime

from src.services import GoogleMapsService, ClaudeClient, SearchTools
from src.agents import VideoAgent, SongAgent, StoryAgent, JudgeAgent
from src.core import Orchestrator, Collector
from src.utils import QueueManager

main_bp = Blueprint('main', __name__)

# Global storage for active route processing sessions
active_sessions = {}
session_lock = threading.Lock()


class RouteSession:
    """Represents an active route processing session."""

    def __init__(self, route_id, route, orchestrator, collector):
        self.route_id = route_id
        self.route = route
        self.orchestrator = orchestrator
        self.collector = collector
        self.status = 'processing'
        self.current_waypoint = 0
        self.total_waypoints = len(route.waypoints)
        self.start_time = time.time()
        self.errors = []


@main_bp.route('/')
def index():
    """Render home page with route input form."""
    return render_template('index.html')


@main_bp.route('/api/process-route', methods=['POST'])
def process_route():
    """
    Start processing a route.

    Request JSON:
        {
            "start": "Start location",
            "end": "End location",
            "max_points": 5
        }

    Returns:
        JSON with route_id for tracking progress
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        start_location = data.get('start', '').strip()
        end_location = data.get('end', '').strip()
        max_points = data.get('max_points', 5)

        if not start_location or not end_location:
            return jsonify({'error': 'Start and end locations are required'}), 400

        # Validate max_points
        try:
            max_points = int(max_points)
            if max_points < 2 or max_points > 20:
                return jsonify({'error': 'Max waypoints must be between 2 and 20'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid max_points value'}), 400

        # Initialize services
        settings = current_app.config['SETTINGS']

        google_maps = GoogleMapsService(settings.google_maps_api_key)
        claude_client = ClaudeClient(
            api_key=settings.anthropic_api_key,
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens,
            temperature=settings.claude_temperature
        )
        search_tools = SearchTools()

        # Get route from Google Maps
        try:
            route = google_maps.get_route(
                origin=start_location,
                destination=end_location,
                max_waypoints=max_points
            )
        except Exception as e:
            current_app.logger.error(f"Failed to get route: {e}")
            return jsonify({'error': f'Failed to get route: {str(e)}'}), 500

        # Initialize agents
        video_agent = VideoAgent(claude_client, search_tools)
        song_agent = SongAgent(claude_client, search_tools)
        story_agent = StoryAgent(claude_client, search_tools)
        judge_agent = JudgeAgent(claude_client)

        # Initialize queue manager and orchestrator
        queue_manager = QueueManager()
        orchestrator = Orchestrator(
            video_agent=video_agent,
            song_agent=song_agent,
            story_agent=story_agent,
            judge_agent=judge_agent,
            queue_manager=queue_manager
        )

        # Initialize collector
        collector = Collector(route_id=route.route_id, queue_manager=queue_manager)

        # Create session
        session = RouteSession(
            route_id=route.route_id,
            route=route,
            orchestrator=orchestrator,
            collector=collector
        )

        # Store session
        with session_lock:
            active_sessions[route.route_id] = session

        # Start processing in background thread
        thread = threading.Thread(
            target=_process_route_background,
            args=(session,),
            daemon=True
        )
        thread.start()

        return jsonify({
            'route_id': route.route_id,
            'total_waypoints': len(route.waypoints),
            'origin': route.origin,
            'destination': route.destination
        })

    except Exception as e:
        current_app.logger.exception(f"Error processing route: {e}")
        return jsonify({'error': str(e)}), 500


def _process_route_background(session: RouteSession):
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


@main_bp.route('/api/progress/<route_id>')
def get_progress(route_id):
    """
    Get processing progress for a route.

    Args:
        route_id: Route identifier

    Returns:
        JSON with progress information
    """
    with session_lock:
        session = active_sessions.get(route_id)

    if not session:
        return jsonify({'error': 'Route not found'}), 404

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

    return jsonify({
        'route_id': route_id,
        'status': session.status,
        'current_waypoint': session.current_waypoint,
        'total_waypoints': session.total_waypoints,
        'progress_percentage': int((session.current_waypoint / session.total_waypoints) * 100),
        'elapsed_time': int(elapsed_time),
        'current_waypoint_info': current_waypoint_info,
        'errors': session.errors
    })


@main_bp.route('/api/results/<route_id>')
def get_results(route_id):
    """
    Get final results for a route.

    Args:
        route_id: Route identifier

    Returns:
        JSON with complete route results
    """
    with session_lock:
        session = active_sessions.get(route_id)

    if not session:
        return jsonify({'error': 'Route not found'}), 404

    if session.status != 'completed':
        return jsonify({'error': 'Route processing not completed'}), 400

    # Get route summary from collector
    summary = session.collector.get_route_summary()

    return jsonify(summary)


@main_bp.route('/results/<route_id>')
def show_results(route_id):
    """
    Display results page for a route.

    Args:
        route_id: Route identifier

    Returns:
        Rendered results page
    """
    with session_lock:
        session = active_sessions.get(route_id)

    if not session:
        return render_template('error.html', error='Route not found'), 404

    return render_template('results.html', route_id=route_id)


@main_bp.route('/processing/<route_id>')
def show_processing(route_id):
    """
    Display processing page for a route.

    Args:
        route_id: Route identifier

    Returns:
        Rendered processing page
    """
    with session_lock:
        session = active_sessions.get(route_id)

    if not session:
        return render_template('error.html', error='Route not found'), 404

    return render_template('processing.html', route_id=route_id)
