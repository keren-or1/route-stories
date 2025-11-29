"""
Unit tests for GoogleMapsService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.google_maps import GoogleMapsService, Waypoint, Route


class TestWaypoint:
    """Tests for Waypoint dataclass."""

    def test_waypoint_creation(self):
        """Test creating a waypoint."""
        wp = Waypoint(
            point_id=1,
            address="123 Main St",
            location={'lat': 40.7, 'lng': -74.0},
            distance_from_start=1000,
            duration_from_start=300
        )

        assert wp.point_id == 1
        assert wp.address == "123 Main St"
        assert wp.location['lat'] == 40.7
        assert wp.distance_from_start == 1000
        assert wp.duration_from_start == 300

    def test_waypoint_repr(self):
        """Test waypoint string representation."""
        wp = Waypoint(
            point_id=5,
            address="Central Park",
            location={'lat': 40.7, 'lng': -74.0}
        )

        repr_str = repr(wp)
        assert "Waypoint" in repr_str
        assert "id=5" in repr_str
        assert "Central Park" in repr_str


class TestRoute:
    """Tests for Route dataclass."""

    def test_route_creation(self):
        """Test creating a route."""
        waypoints = [
            Waypoint(0, "Start", {'lat': 40.7, 'lng': -74.0}),
            Waypoint(1, "End", {'lat': 40.8, 'lng': -74.1})
        ]

        route = Route(
            route_id="test-123",
            origin="Start",
            destination="End",
            waypoints=waypoints,
            total_distance=5000,
            total_duration=600
        )

        assert route.route_id == "test-123"
        assert route.origin == "Start"
        assert route.destination == "End"
        assert len(route.waypoints) == 2
        assert route.total_distance == 5000
        assert route.total_duration == 600

    def test_route_repr(self):
        """Test route string representation."""
        route = Route(
            route_id="abc",
            origin="Point A",
            destination="Point B",
            waypoints=[],
            total_distance=1000,
            total_duration=100
        )

        repr_str = repr(route)
        assert "Route" in repr_str
        assert "id=abc" in repr_str
        assert "Point A" in repr_str
        assert "Point B" in repr_str


class TestGoogleMapsService:
    """Tests for GoogleMapsService."""

    @patch('src.services.google_maps.googlemaps.Client')
    def test_init(self, mock_gmaps_client):
        """Test service initialization."""
        service = GoogleMapsService(api_key="test_api_key")

        assert service.client is not None
        mock_gmaps_client.assert_called_once_with(key="test_api_key")

    @patch('src.services.google_maps.googlemaps.Client')
    def test_get_route_success(self, mock_gmaps_client):
        """Test successful route retrieval."""
        # Mock Google Maps API response
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client

        mock_client.directions.return_value = [
            {
                'legs': [
                    {
                        'start_address': 'New York, NY',
                        'end_address': 'Boston, MA',
                        'start_location': {'lat': 40.7128, 'lng': -74.0060},
                        'end_location': {'lat': 42.3601, 'lng': -71.0589},
                        'distance': {'value': 350000},
                        'duration': {'value': 14400},
                        'steps': [
                            {
                                'html_instructions': 'Head north on Broadway',
                                'end_location': {'lat': 40.72, 'lng': -74.0},
                                'distance': {'value': 1000},
                                'duration': {'value': 120}
                            }
                        ]
                    }
                ]
            }
        ]

        service = GoogleMapsService(api_key="test_key")
        route = service.get_route("New York, NY", "Boston, MA", max_waypoints=5)

        assert isinstance(route, Route)
        assert route.origin == "New York, NY"
        assert route.destination == "Boston, MA"
        assert len(route.waypoints) >= 2  # At least start and end
        assert route.total_distance == 350000
        assert route.total_duration == 14400

    @patch('src.services.google_maps.googlemaps.Client')
    def test_get_route_no_results(self, mock_gmaps_client):
        """Test route retrieval with no results."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.directions.return_value = []

        service = GoogleMapsService(api_key="test_key")

        with pytest.raises(Exception, match="No route found"):
            service.get_route("Invalid Origin", "Invalid Destination")

    @patch('src.services.google_maps.googlemaps.Client')
    def test_get_route_api_error(self, mock_gmaps_client):
        """Test route retrieval with API error."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.directions.side_effect = Exception("API Error")

        service = GoogleMapsService(api_key="test_key")

        with pytest.raises(Exception):
            service.get_route("New York", "Boston")

    @patch('src.services.google_maps.googlemaps.Client')
    def test_extract_waypoints_basic(self, mock_gmaps_client):
        """Test waypoint extraction from route legs."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client

        legs = [
            {
                'start_address': 'Start Point',
                'end_address': 'End Point',
                'start_location': {'lat': 40.0, 'lng': -74.0},
                'end_location': {'lat': 41.0, 'lng': -73.0},
                'distance': {'value': 10000},
                'duration': {'value': 600},
                'steps': [
                    {
                        'html_instructions': 'Head north on Main St',
                        'end_location': {'lat': 40.1, 'lng': -74.0},
                        'distance': {'value': 500},
                        'duration': {'value': 60}
                    },
                    {
                        'html_instructions': 'Turn right onto Elm St',
                        'end_location': {'lat': 40.2, 'lng': -73.9},
                        'distance': {'value': 800},
                        'duration': {'value': 90}
                    }
                ]
            }
        ]

        service = GoogleMapsService(api_key="test_key")
        waypoints = service._extract_waypoints(legs, max_waypoints=10)

        # Should have at least start and end waypoints
        assert len(waypoints) >= 2
        assert waypoints[0].address == 'Start Point'
        assert waypoints[-1].address == 'End Point'
        assert waypoints[0].distance_from_start == 0
        assert waypoints[0].duration_from_start == 0

    @patch('src.services.google_maps.googlemaps.Client')
    def test_extract_waypoints_respects_max(self, mock_gmaps_client):
        """Test that max_waypoints limit is respected."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client

        # Create many steps
        steps = [
            {
                'html_instructions': f'Step {i} on Street {i}',
                'end_location': {'lat': 40.0 + i * 0.01, 'lng': -74.0},
                'distance': {'value': 100},
                'duration': {'value': 10}
            }
            for i in range(50)
        ]

        legs = [
            {
                'start_address': 'Start',
                'end_address': 'End',
                'start_location': {'lat': 40.0, 'lng': -74.0},
                'end_location': {'lat': 41.0, 'lng': -73.0},
                'distance': {'value': 5000},
                'duration': {'value': 500},
                'steps': steps
            }
        ]

        service = GoogleMapsService(api_key="test_key")
        waypoints = service._extract_waypoints(legs, max_waypoints=5)

        # Should not exceed max_waypoints
        assert len(waypoints) <= 5

    @patch('src.services.google_maps.googlemaps.Client')
    def test_get_step_address_from_instruction(self, mock_gmaps_client):
        """Test extracting address from HTML instruction."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client

        service = GoogleMapsService(api_key="test_key")

        # Test with street name
        step = {
            'html_instructions': 'Turn right onto <b>Broadway</b>',
            'end_location': {'lat': 40.7, 'lng': -74.0}
        }

        address = service._get_step_address(step)
        assert address == "Broadway"

    @patch('src.services.google_maps.googlemaps.Client')
    def test_get_step_address_with_reverse_geocode(self, mock_gmaps_client):
        """Test address extraction using reverse geocoding."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.reverse_geocode.return_value = [
            {'formatted_address': '123 Main St, New York, NY 10001'}
        ]

        service = GoogleMapsService(api_key="test_key")

        step = {
            'html_instructions': 'Continue straight',
            'end_location': {'lat': 40.7, 'lng': -74.0}
        }

        address = service._get_step_address(step)
        assert address  # Should get something from reverse geocode

    @patch('src.services.google_maps.googlemaps.Client')
    def test_get_step_address_empty_for_direction_only(self, mock_gmaps_client):
        """Test that pure direction instructions return empty string."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.reverse_geocode.return_value = None

        service = GoogleMapsService(api_key="test_key")

        step = {
            'html_instructions': 'Turn left',
            'end_location': {'lat': 40.7, 'lng': -74.0}
        }

        with patch.object(service, 'reverse_geocode', return_value=None):
            address = service._get_step_address(step)
            # Should be empty or minimal since it's just a direction
            assert isinstance(address, str)

    @patch('src.services.google_maps.googlemaps.Client')
    def test_geocode_address_success(self, mock_gmaps_client):
        """Test geocoding an address to coordinates."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.geocode.return_value = [
            {
                'geometry': {
                    'location': {'lat': 40.7128, 'lng': -74.0060}
                }
            }
        ]

        service = GoogleMapsService(api_key="test_key")
        coords = service.geocode_address("New York, NY")

        assert coords == (40.7128, -74.0060)

    @patch('src.services.google_maps.googlemaps.Client')
    def test_geocode_address_no_results(self, mock_gmaps_client):
        """Test geocoding with no results."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.geocode.return_value = []

        service = GoogleMapsService(api_key="test_key")
        coords = service.geocode_address("Invalid Address")

        assert coords is None

    @patch('src.services.google_maps.googlemaps.Client')
    def test_geocode_address_error(self, mock_gmaps_client):
        """Test geocoding with API error."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.geocode.side_effect = Exception("API Error")

        service = GoogleMapsService(api_key="test_key")
        coords = service.geocode_address("New York")

        assert coords is None

    @patch('src.services.google_maps.googlemaps.Client')
    def test_reverse_geocode_success(self, mock_gmaps_client):
        """Test reverse geocoding coordinates to address."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.reverse_geocode.return_value = [
            {'formatted_address': 'Times Square, New York, NY 10036'}
        ]

        service = GoogleMapsService(api_key="test_key")
        address = service.reverse_geocode(40.758, -73.985)

        assert address == 'Times Square, New York, NY 10036'

    @patch('src.services.google_maps.googlemaps.Client')
    def test_reverse_geocode_no_results(self, mock_gmaps_client):
        """Test reverse geocoding with no results."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.reverse_geocode.return_value = []

        service = GoogleMapsService(api_key="test_key")
        address = service.reverse_geocode(0.0, 0.0)

        assert address is None

    @patch('src.services.google_maps.googlemaps.Client')
    def test_reverse_geocode_error(self, mock_gmaps_client):
        """Test reverse geocoding with API error."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client
        mock_client.reverse_geocode.side_effect = Exception("API Error")

        service = GoogleMapsService(api_key="test_key")
        address = service.reverse_geocode(40.7, -74.0)

        assert address is None

    @patch('src.services.google_maps.googlemaps.Client')
    def test_get_route_with_mode(self, mock_gmaps_client):
        """Test route retrieval with different travel modes."""
        mock_client = Mock()
        mock_gmaps_client.return_value = mock_client

        mock_client.directions.return_value = [
            {
                'legs': [
                    {
                        'start_address': 'A',
                        'end_address': 'B',
                        'start_location': {'lat': 40.0, 'lng': -74.0},
                        'end_location': {'lat': 41.0, 'lng': -73.0},
                        'distance': {'value': 5000},
                        'duration': {'value': 600},
                        'steps': []
                    }
                ]
            }
        ]

        service = GoogleMapsService(api_key="test_key")
        route = service.get_route("A", "B", mode="walking", max_waypoints=3)

        assert route.origin == "A"
        assert route.destination == "B"
        mock_client.directions.assert_called_once()
        call_kwargs = mock_client.directions.call_args[1]
        assert call_kwargs['mode'] == 'walking'
