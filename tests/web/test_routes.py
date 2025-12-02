"""
Comprehensive tests for Flask web routes.
Tests all endpoints: /, /api/process-route, /api/progress, /api/results, /results, /processing
"""

import pytest
import json
import time
from unittest.mock import Mock, MagicMock, patch
from flask import Flask
from src.web.routes import main_bp, session_manager
from src.web.route_session import RouteSession
from src.services.google_maps import Route, Waypoint


@pytest.fixture
def app():
    """Create Flask test app."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SETTINGS'] = Mock(
        google_maps_api_key='test-key',
        gemini_api_key='test-gemini-key',
        gemini_model='gemini-pro',
        gemini_max_tokens=1024,
        gemini_temperature=0.7
    )
    app.register_blueprint(main_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_route():
    """Sample route for testing."""
    waypoints = [
        Waypoint(
            point_id=1,
            address="New York, NY",
            location={'lat': 40.7128, 'lng': -74.0060},
            distance_from_start=0,
            duration_from_start=0
        ),
        Waypoint(
            point_id=2,
            address="Philadelphia, PA",
            location={'lat': 39.9526, 'lng': -75.1652},
            distance_from_start=150000,
            duration_from_start=7200
        )
    ]

    return Route(
        route_id="test-route-123",
        origin="New York, NY",
        destination="Philadelphia, PA",
        total_distance=150000,
        total_duration=7200,
        waypoints=waypoints
    )


class TestIndexRoute:
    """Tests for home page route (/)."""

    def test_index_renders_successfully(self, client):
        """Test that index page renders."""
        with patch('src.web.routes.render_template') as mock_render:
            mock_render.return_value = "mocked template"
            response = client.get('/')
            assert response.status_code == 200
            mock_render.assert_called_once_with('index.html')

    def test_index_accepts_get_only(self, client):
        """Test that index only accepts GET requests."""
        response = client.post('/')
        assert response.status_code == 405  # Method Not Allowed


class TestProcessRouteAPI:
    """Tests for /api/process-route endpoint."""

    @patch('src.web.routes.create_services')
    @patch('src.web.routes.threading.Thread')
    def test_process_route_success(
        self, mock_thread, mock_create_services,
        client, sample_route
    ):
        """Test successful route processing initiation."""
        # Setup mocks
        mock_google_maps = Mock()
        mock_google_maps.get_route.return_value = sample_route
        mock_orchestrator = Mock()
        mock_queue_manager = Mock()

        mock_create_services.return_value = {
            'google_maps': mock_google_maps,
            'orchestrator': mock_orchestrator,
            'queue_manager': mock_queue_manager
        }

        # Make request
        response = client.post('/api/process-route',
            json={
                'start': 'New York, NY',
                'end': 'Philadelphia, PA',
                'max_points': 5
            }
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'route_id' in data
        assert data['total_waypoints'] == 2
        assert data['origin'] == 'New York, NY'
        assert data['destination'] == 'Philadelphia, PA'

        # Verify thread was started
        mock_thread.assert_called_once()
        thread_instance = mock_thread.return_value
        thread_instance.start.assert_called_once()

    def test_process_route_missing_data(self, client):
        """Test error when no JSON data provided."""
        response = client.post('/api/process-route')
        assert response.status_code in [400, 500]  # Accept either error code
        data = json.loads(response.data)
        assert 'error' in data

    def test_process_route_missing_start(self, client):
        """Test error when start location is missing."""
        response = client.post('/api/process-route',
            json={'end': 'Philadelphia, PA', 'max_points': 5}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'required' in data['error'].lower()

    def test_process_route_missing_end(self, client):
        """Test error when end location is missing."""
        response = client.post('/api/process-route',
            json={'start': 'New York, NY', 'max_points': 5}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'required' in data['error'].lower()

    def test_process_route_empty_start(self, client):
        """Test error when start is empty string."""
        response = client.post('/api/process-route',
            json={'start': '  ', 'end': 'Philadelphia, PA', 'max_points': 5}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_process_route_invalid_max_points_low(self, client):
        """Test error when max_points is too low."""
        response = client.post('/api/process-route',
            json={'start': 'New York, NY', 'end': 'Philadelphia, PA', 'max_points': 1}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'between 2 and 20' in data['error']

    def test_process_route_invalid_max_points_high(self, client):
        """Test error when max_points is too high."""
        response = client.post('/api/process-route',
            json={'start': 'New York, NY', 'end': 'Philadelphia, PA', 'max_points': 25}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'between 2 and 20' in data['error']

    def test_process_route_invalid_max_points_type(self, client):
        """Test error when max_points is not a number."""
        response = client.post('/api/process-route',
            json={'start': 'New York, NY', 'end': 'Philadelphia, PA', 'max_points': 'abc'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid' in data['error']

    @patch('src.web.routes.create_services')
    def test_process_route_maps_failure(self, mock_create_services, client):
        """Test error when Google Maps fails."""
        mock_google_maps = Mock()
        mock_google_maps.get_route.side_effect = Exception("Maps API error")

        mock_create_services.return_value = {
            'google_maps': mock_google_maps,
            'orchestrator': Mock(),
            'queue_manager': Mock()
        }

        response = client.post('/api/process-route',
            json={'start': 'New York, NY', 'end': 'Philadelphia, PA', 'max_points': 5}
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Failed to get route' in data['error']

    @patch('src.web.routes.create_services')
    def test_process_route_default_max_points(self, mock_create_services, client):
        """Test that max_points defaults to 5."""
        mock_google_maps = Mock()
        mock_route = Mock()
        mock_route.route_id = "test-123"
        mock_route.origin = "New York"
        mock_route.destination = "Philly"
        mock_route.waypoints = [Mock(), Mock()]
        mock_google_maps.get_route.return_value = mock_route

        mock_create_services.return_value = {
            'google_maps': mock_google_maps,
            'orchestrator': Mock(),
            'queue_manager': Mock()
        }

        with patch('src.web.routes.threading.Thread'):
            response = client.post('/api/process-route',
                json={'start': 'New York, NY', 'end': 'Philadelphia, PA'}
            )

            # Check that max_waypoints was called with default value
            call_args = mock_google_maps.get_route.call_args
            assert call_args.kwargs['max_waypoints'] == 5


class TestProgressAPI:
    """Tests for /api/progress/<route_id> endpoint."""

    def test_get_progress_not_found(self, client):
        """Test error when route_id doesn't exist."""
        response = client.get('/api/progress/nonexistent-route')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_get_progress_success(self, client, sample_route):
        """Test successful progress retrieval."""
        # Create a mock session
        mock_orchestrator = Mock()
        mock_collector = Mock()
        session = RouteSession(
            route_id=sample_route.route_id,
            route=sample_route,
            orchestrator=mock_orchestrator,
            collector=mock_collector
        )
        session.current_waypoint = 1
        session.status = 'processing'

        # Add to active sessions
        session_manager.add_session(sample_route.route_id, session)

        try:
            # Get progress
            response = client.get(f'/api/progress/{sample_route.route_id}')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['route_id'] == sample_route.route_id
            assert data['status'] == 'processing'
            assert data['current_waypoint'] == 1
            assert data['total_waypoints'] == 2
            assert data['progress_percentage'] == 50
            assert 'elapsed_time' in data
            assert 'errors' in data
        finally:
            # Cleanup
            session_manager.remove_session(sample_route.route_id)

    def test_get_progress_with_waypoint_info(self, client, sample_route):
        """Test progress includes current waypoint info."""
        mock_orchestrator = Mock()
        mock_collector = Mock()
        session = RouteSession(
            route_id=sample_route.route_id,
            route=sample_route,
            orchestrator=mock_orchestrator,
            collector=mock_collector
        )
        session.current_waypoint = 1

        session_manager.add_session(sample_route.route_id, session)

        try:
            response = client.get(f'/api/progress/{sample_route.route_id}')
            data = json.loads(response.data)

            assert 'current_waypoint_info' in data
            assert data['current_waypoint_info'] is not None
            assert 'point_id' in data['current_waypoint_info']
            assert 'address' in data['current_waypoint_info']
        finally:
            session_manager.remove_session(sample_route.route_id)


class TestResultsAPI:
    """Tests for /api/results/<route_id> endpoint."""

    def test_get_results_not_found(self, client):
        """Test error when route_id doesn't exist."""
        response = client.get('/api/results/nonexistent-route')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_results_not_completed(self, client, sample_route):
        """Test error when route processing not completed."""
        mock_orchestrator = Mock()
        mock_collector = Mock()
        session = RouteSession(
            route_id=sample_route.route_id,
            route=sample_route,
            orchestrator=mock_orchestrator,
            collector=mock_collector
        )
        session.status = 'processing'

        session_manager.add_session(sample_route.route_id, session)

        try:
            response = client.get(f'/api/results/{sample_route.route_id}')
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert 'not completed' in data['error'].lower()
        finally:
            session_manager.remove_session(sample_route.route_id)

    def test_get_results_success(self, client, sample_route):
        """Test successful results retrieval."""
        mock_orchestrator = Mock()
        mock_collector = Mock()
        mock_collector.get_route_summary.return_value = {
            'route_id': sample_route.route_id,
            'waypoints': []
        }

        session = RouteSession(
            route_id=sample_route.route_id,
            route=sample_route,
            orchestrator=mock_orchestrator,
            collector=mock_collector
        )
        session.status = 'completed'

        session_manager.add_session(sample_route.route_id, session)

        try:
            response = client.get(f'/api/results/{sample_route.route_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'route_id' in data
            mock_collector.get_route_summary.assert_called_once()
        finally:
            session_manager.remove_session(sample_route.route_id)


class TestShowResultsPage:
    """Tests for /results/<route_id> page endpoint."""

    def test_show_results_not_found(self, client):
        """Test error page when route not found."""
        with patch('src.web.routes.render_template') as mock_render:
            mock_render.return_value = "error page"
            response = client.get('/results/nonexistent-route')
            assert response.status_code == 404
            mock_render.assert_called_once_with('error.html', error='Route not found')

    def test_show_results_success(self, client, sample_route):
        """Test results page renders successfully."""
        mock_orchestrator = Mock()
        mock_collector = Mock()
        session = RouteSession(
            route_id=sample_route.route_id,
            route=sample_route,
            orchestrator=mock_orchestrator,
            collector=mock_collector
        )

        session_manager.add_session(sample_route.route_id, session)

        try:
            with patch('src.web.routes.render_template') as mock_render:
                mock_render.return_value = "results page"
                response = client.get(f'/results/{sample_route.route_id}')
                assert response.status_code == 200
                mock_render.assert_called_once_with('results.html', route_id=sample_route.route_id)
        finally:
            session_manager.remove_session(sample_route.route_id)


class TestShowProcessingPage:
    """Tests for /processing/<route_id> page endpoint."""

    def test_show_processing_not_found(self, client):
        """Test error page when route not found."""
        with patch('src.web.routes.render_template') as mock_render:
            mock_render.return_value = "error page"
            response = client.get('/processing/nonexistent-route')
            assert response.status_code == 404
            mock_render.assert_called_once_with('error.html', error='Route not found')

    def test_show_processing_success(self, client, sample_route):
        """Test processing page renders successfully."""
        mock_orchestrator = Mock()
        mock_collector = Mock()
        session = RouteSession(
            route_id=sample_route.route_id,
            route=sample_route,
            orchestrator=mock_orchestrator,
            collector=mock_collector
        )

        session_manager.add_session(sample_route.route_id, session)

        try:
            with patch('src.web.routes.render_template') as mock_render:
                mock_render.return_value = "processing page"
                response = client.get(f'/processing/{sample_route.route_id}')
                assert response.status_code == 200
                mock_render.assert_called_once_with('processing.html', route_id=sample_route.route_id)
        finally:
            session_manager.remove_session(sample_route.route_id)


class TestRouteSession:
    """Tests for RouteSession class."""

    def test_route_session_initialization(self, sample_route):
        """Test RouteSession initializes correctly."""
        mock_orchestrator = Mock()
        mock_collector = Mock()

        session = RouteSession(
            route_id=sample_route.route_id,
            route=sample_route,
            orchestrator=mock_orchestrator,
            collector=mock_collector
        )

        assert session.route_id == sample_route.route_id
        assert session.route == sample_route
        assert session.orchestrator == mock_orchestrator
        assert session.collector == mock_collector
        assert session.status == 'processing'
        assert session.current_waypoint == 0
        assert session.total_waypoints == 2
        assert isinstance(session.errors, list)
        assert len(session.errors) == 0
        assert session.start_time > 0


class TestBackgroundProcessing:
    """Tests for background route processing."""

    @patch('src.web.route_processor.Path')
    def test_process_route_background_success(self, mock_path, sample_route):
        """Test successful background processing."""
        from src.web.route_processor import process_route_background

        # Setup mocks
        mock_orchestrator = Mock()
        mock_collector = Mock()
        mock_orchestrator.process_waypoint.return_value = {'video': {}}
        mock_collector.get_route_summary.return_value = {}

        # Setup Path mock
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.parent.parent = Mock()
        results_dir = Mock()
        mock_path_instance.parent.parent.parent.__truediv__ = Mock(return_value=results_dir)
        results_dir.__truediv__ = Mock(return_value=Mock())

        session = RouteSession(
            route_id=sample_route.route_id,
            route=sample_route,
            orchestrator=mock_orchestrator,
            collector=mock_collector
        )

        # Run background processing
        process_route_background(session)

        # Verify processing occurred
        assert session.status == 'completed'
        assert mock_orchestrator.process_waypoint.call_count == 2
        assert mock_collector.collect_waypoint.call_count == 2
        mock_orchestrator.shutdown.assert_called_once()

    def test_process_route_background_error(self, app, sample_route):
        """Test error handling in background processing."""
        from src.web.route_processor import process_route_background

        # Setup mocks to raise error
        mock_orchestrator = Mock()
        mock_collector = Mock()
        mock_orchestrator.process_waypoint.side_effect = Exception("Processing error")

        session = RouteSession(
            route_id=sample_route.route_id,
            route=sample_route,
            orchestrator=mock_orchestrator,
            collector=mock_collector
        )

        # Run background processing within app context
        with app.app_context(), \
             patch('src.web.route_processor.Path'):
            process_route_background(session)

        # Verify error was handled
        assert session.status == 'error'
        assert len(session.errors) > 0
        assert 'Processing error' in session.errors[0]
        mock_orchestrator.shutdown.assert_called_once()
