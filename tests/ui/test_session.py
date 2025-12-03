"""Tests for session management."""

import pytest
from unittest.mock import Mock
from src.ui.session import process_waypoint, get_waypoints_to_process
from src.services.route_models import Route, Waypoint


class TestProcessWaypoint:
    """Test waypoint processing."""

    def test_process_waypoint_success(self):
        """Test successful waypoint processing."""
        waypoint = Waypoint(
            point_id=1,
            address="Tel Aviv",
            location={"lat": 32.0853, "lng": 34.7818}
        )
        orchestrator = Mock()
        orchestrator.process_waypoint.return_value = {"video": {}, "song": {}, "story": {}}
        collector = Mock()

        process_waypoint(waypoint, "route123", orchestrator, collector)

        orchestrator.process_waypoint.assert_called_once_with(
            route_id="route123",
            point_id=1,
            address="Tel Aviv",
            location=waypoint.location
        )
        collector.collect_waypoint.assert_called_once()

    def test_process_waypoint_passes_results(self):
        """Test that results are passed to collector."""
        waypoint = Waypoint(
            point_id=2,
            address="Test",
            location={"lat": 0, "lng": 0}
        )
        mock_results = {"video": {"title": "Test"}, "song": {}, "story": {}}
        orchestrator = Mock()
        orchestrator.process_waypoint.return_value = mock_results
        collector = Mock()

        process_waypoint(waypoint, "route456", orchestrator, collector)

        collector.collect_waypoint.assert_called_once_with(
            point_id=2,
            address="Test",
            location=waypoint.location,
            results=mock_results
        )


class TestGetWaypointsToProcess:
    """Test waypoint selection."""

    def test_get_waypoints_no_limit(self):
        """Test getting waypoints with no limit."""
        waypoints = [
            Waypoint(point_id=1, address="A", location={"lat": 0, "lng": 0}),
            Waypoint(point_id=2, address="B", location={"lat": 1, "lng": 1}),
            Waypoint(point_id=3, address="C", location={"lat": 2, "lng": 2})
        ]
        route = Route(
            route_id="test",
            origin="A",
            destination="C",
            total_distance=1000,
            total_duration=600,
            waypoints=waypoints
        )

        result = get_waypoints_to_process(route, None)

        assert len(result) == 3
        assert result == waypoints

    def test_get_waypoints_with_limit(self):
        """Test getting waypoints with limit."""
        waypoints = [
            Waypoint(point_id=1, address="A", location={"lat": 0, "lng": 0}),
            Waypoint(point_id=2, address="B", location={"lat": 1, "lng": 1}),
            Waypoint(point_id=3, address="C", location={"lat": 2, "lng": 2}),
            Waypoint(point_id=4, address="D", location={"lat": 3, "lng": 3})
        ]
        route = Route(
            route_id="test",
            origin="A",
            destination="D",
            total_distance=2000,
            total_duration=1200,
            waypoints=waypoints
        )

        result = get_waypoints_to_process(route, 2)

        assert len(result) == 2
        assert result[0].point_id == 1
        assert result[1].point_id == 2

    def test_get_waypoints_limit_exceeds_total(self):
        """Test limit greater than total waypoints."""
        waypoints = [
            Waypoint(point_id=1, address="A", location={"lat": 0, "lng": 0}),
            Waypoint(point_id=2, address="B", location={"lat": 1, "lng": 1})
        ]
        route = Route(
            route_id="test",
            origin="A",
            destination="B",
            total_distance=500,
            total_duration=300,
            waypoints=waypoints
        )

        result = get_waypoints_to_process(route, 10)

        assert len(result) == 2
        assert result == waypoints
