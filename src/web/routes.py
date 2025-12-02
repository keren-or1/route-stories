"""
Flask routes for Route Stories web UI.
"""

import threading
from flask import Blueprint, render_template, request, jsonify, current_app

from src.web.route_session import SessionManager
from src.web.request_validator import validate_route_request
from src.web.route_handlers import (
    handle_process_route,
    handle_get_progress,
    handle_get_results
)
from src.web.service_factory import create_services

main_bp = Blueprint('main', __name__)

# Global session manager
session_manager = SessionManager()


@main_bp.route('/')
def index():
    """Render home page with route input form."""
    return render_template('index.html')


@main_bp.route('/api/process-route', methods=['POST'])
def process_route():
    """Start processing a route."""
    try:
        data = request.get_json()

        # Validate request
        is_valid, error_msg, parsed_data = validate_route_request(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Create services (for test mocking compatibility)
        settings = current_app.config['SETTINGS']
        services = create_services(settings)

        # Process route
        result = handle_process_route(parsed_data, session_manager, services)
        return jsonify(result)

    except Exception as e:
        current_app.logger.exception(f"Error processing route: {e}")
        error_msg = f"Failed to get route: {e}" if "Maps API error" in str(e) else str(e)
        return jsonify({'error': error_msg}), 500


@main_bp.route('/api/progress/<route_id>')
def get_progress(route_id):
    """Get processing progress for a route."""
    result, error = handle_get_progress(route_id, session_manager)

    if error:
        return jsonify({'error': error}), 404 if error == 'Route not found' else 400

    return jsonify(result)


@main_bp.route('/api/results/<route_id>')
def get_results(route_id):
    """Get final results for a route."""
    result, error = handle_get_results(route_id, session_manager)

    if error:
        return jsonify({'error': error}), 404 if error == 'Route not found' else 400

    return jsonify(result)


@main_bp.route('/results/<route_id>')
def show_results(route_id):
    """Display results page for a route."""
    session = session_manager.get_session(route_id)

    if not session:
        return render_template('error.html', error='Route not found'), 404

    return render_template('results.html', route_id=route_id)


@main_bp.route('/processing/<route_id>')
def show_processing(route_id):
    """Display processing page for a route."""
    session = session_manager.get_session(route_id)

    if not session:
        return render_template('error.html', error='Route not found'), 404

    return render_template('processing.html', route_id=route_id)
