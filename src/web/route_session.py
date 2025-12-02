"""
Route session management for web interface.
Handles active route processing sessions and their state.
"""

import time
import threading


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


class SessionManager:
    """Thread-safe manager for active route sessions."""

    def __init__(self):
        self.active_sessions = {}
        self.lock = threading.Lock()

    def add_session(self, route_id, session):
        """Add a new session."""
        with self.lock:
            self.active_sessions[route_id] = session

    def get_session(self, route_id):
        """Get a session by ID."""
        with self.lock:
            return self.active_sessions.get(route_id)

    def remove_session(self, route_id):
        """Remove a session."""
        with self.lock:
            if route_id in self.active_sessions:
                del self.active_sessions[route_id]
