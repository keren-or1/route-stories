"""
Unit tests for Scheduler.
"""

import pytest
from unittest.mock import Mock
from src.core.scheduler import Scheduler
from src.services.google_maps import Route, Waypoint


class TestScheduler:
    """Tests for Scheduler."""

    @pytest.fixture
    def sample_route(self):
        """Create a sample route with waypoints."""
        waypoints = [
            Waypoint(0, "Start Location", {'lat': 40.0, 'lng': -74.0}, 0, 0),
            Waypoint(1, "Middle Location", {'lat': 40.1, 'lng': -74.1}, 1000, 120),
            Waypoint(2, "End Location", {'lat': 40.2, 'lng': -74.2}, 2000, 240),
        ]

        return Route(
            route_id="test-route-001",
            origin="Start Location",
            destination="End Location",
            waypoints=waypoints,
            total_distance=2000,
            total_duration=240
        )

    def test_init(self, sample_route):
        """Test scheduler initialization."""
        scheduler = Scheduler(sample_route)

        assert scheduler.route == sample_route
        assert scheduler.current_index == 0
        assert len(scheduler.completed_indices) == 0

    def test_has_next_at_start(self, sample_route):
        """Test has_next at beginning."""
        scheduler = Scheduler(sample_route)

        assert scheduler.has_next() is True

    def test_has_next_at_end(self, sample_route):
        """Test has_next when all waypoints processed."""
        scheduler = Scheduler(sample_route)
        scheduler.current_index = len(sample_route.waypoints)

        assert scheduler.has_next() is False

    def test_get_next_first_waypoint(self, sample_route):
        """Test getting first waypoint."""
        scheduler = Scheduler(sample_route)

        waypoint = scheduler.get_next()

        assert waypoint is not None
        assert waypoint.point_id == 0
        assert waypoint.address == "Start Location"

    def test_get_next_sequential(self, sample_route):
        """Test getting waypoints sequentially."""
        scheduler = Scheduler(sample_route)

        # Get first
        wp1 = scheduler.get_next()
        assert wp1.point_id == 0

        # Advance
        scheduler.advance()

        # Get second
        wp2 = scheduler.get_next()
        assert wp2.point_id == 1

        # Advance
        scheduler.advance()

        # Get third
        wp3 = scheduler.get_next()
        assert wp3.point_id == 2

    def test_get_next_returns_none_when_finished(self, sample_route):
        """Test get_next returns None when all processed."""
        scheduler = Scheduler(sample_route)
        scheduler.current_index = len(sample_route.waypoints)

        waypoint = scheduler.get_next()

        assert waypoint is None

    def test_advance_success(self, sample_route):
        """Test successful advance."""
        scheduler = Scheduler(sample_route)

        result = scheduler.advance()

        assert result is True
        assert scheduler.current_index == 1
        assert 0 in scheduler.completed_indices

    def test_advance_through_all_waypoints(self, sample_route):
        """Test advancing through all waypoints."""
        scheduler = Scheduler(sample_route)

        for i in range(len(sample_route.waypoints)):
            assert scheduler.has_next() is True
            result = scheduler.advance()
            assert result is True
            assert i in scheduler.completed_indices

        # Now should be at end
        assert scheduler.has_next() is False
        result = scheduler.advance()
        assert result is False

    def test_advance_when_finished(self, sample_route):
        """Test advance returns False when finished."""
        scheduler = Scheduler(sample_route)
        scheduler.current_index = len(sample_route.waypoints)

        result = scheduler.advance()

        assert result is False
        assert scheduler.current_index == len(sample_route.waypoints)

    def test_get_progress_at_start(self, sample_route):
        """Test progress information at start."""
        scheduler = Scheduler(sample_route)

        progress = scheduler.get_progress()

        assert progress['current_index'] == 0
        assert progress['total_waypoints'] == 3
        assert progress['completed'] == 0
        assert progress['remaining'] == 3
        assert progress['progress_percent'] == 0.0

    def test_get_progress_midway(self, sample_route):
        """Test progress information midway."""
        scheduler = Scheduler(sample_route)

        # Advance once
        scheduler.advance()

        progress = scheduler.get_progress()

        assert progress['current_index'] == 1
        assert progress['total_waypoints'] == 3
        assert progress['completed'] == 1
        assert progress['remaining'] == 2
        assert progress['progress_percent'] == pytest.approx(33.33, rel=0.1)

    def test_get_progress_at_end(self, sample_route):
        """Test progress information at end."""
        scheduler = Scheduler(sample_route)

        # Advance through all waypoints
        for _ in range(len(sample_route.waypoints)):
            scheduler.advance()

        progress = scheduler.get_progress()

        assert progress['current_index'] == 3
        assert progress['total_waypoints'] == 3
        assert progress['completed'] == 3
        assert progress['remaining'] == 0
        assert progress['progress_percent'] == 100.0

    def test_reset(self, sample_route):
        """Test resetting scheduler."""
        scheduler = Scheduler(sample_route)

        # Advance partway
        scheduler.advance()
        scheduler.advance()

        assert scheduler.current_index == 2
        assert len(scheduler.completed_indices) == 2

        # Reset
        scheduler.reset()

        assert scheduler.current_index == 0
        assert len(scheduler.completed_indices) == 0
        assert scheduler.has_next() is True

    def test_run_manual_all_waypoints(self, sample_route):
        """Test manual run through all waypoints."""
        scheduler = Scheduler(sample_route)

        processed = []

        def process_callback(waypoint):
            processed.append(waypoint.point_id)

        scheduler.run_manual(process_callback)

        assert len(processed) == 3
        assert processed == [0, 1, 2]
        assert scheduler.has_next() is False

    def test_run_manual_with_max_waypoints(self, sample_route):
        """Test manual run with max waypoints limit."""
        scheduler = Scheduler(sample_route)

        processed = []

        def process_callback(waypoint):
            processed.append(waypoint.point_id)

        scheduler.run_manual(process_callback, max_waypoints=2)

        assert len(processed) == 2
        assert processed == [0, 1]
        assert scheduler.has_next() is True  # One more remaining

    def test_run_manual_callback_execution(self, sample_route):
        """Test that callback is properly executed for each waypoint."""
        scheduler = Scheduler(sample_route)

        mock_callback = Mock()

        scheduler.run_manual(mock_callback)

        assert mock_callback.call_count == 3
        # Verify waypoints passed to callback
        call_args_list = mock_callback.call_args_list
        assert call_args_list[0][0][0].point_id == 0
        assert call_args_list[1][0][0].point_id == 1
        assert call_args_list[2][0][0].point_id == 2

    def test_run_manual_stops_at_limit(self, sample_route):
        """Test that manual run stops at max limit."""
        scheduler = Scheduler(sample_route)

        processed_count = 0

        def process_callback(waypoint):
            nonlocal processed_count
            processed_count += 1

        scheduler.run_manual(process_callback, max_waypoints=1)

        assert processed_count == 1
        assert scheduler.current_index == 1
        assert 0 in scheduler.completed_indices
        assert 1 not in scheduler.completed_indices

    def test_get_all_waypoints(self, sample_route):
        """Test getting all waypoints."""
        scheduler = Scheduler(sample_route)

        all_waypoints = scheduler.get_all_waypoints()

        assert len(all_waypoints) == 3
        assert all_waypoints[0].point_id == 0
        assert all_waypoints[1].point_id == 1
        assert all_waypoints[2].point_id == 2

    def test_get_all_waypoints_returns_copy(self, sample_route):
        """Test that get_all_waypoints returns a copy."""
        scheduler = Scheduler(sample_route)

        waypoints1 = scheduler.get_all_waypoints()
        waypoints2 = scheduler.get_all_waypoints()

        # Should be equal but different objects
        assert waypoints1 == waypoints2
        assert waypoints1 is not waypoints2

    def test_scheduler_with_single_waypoint(self):
        """Test scheduler with only one waypoint."""
        waypoints = [
            Waypoint(0, "Only Location", {'lat': 40.0, 'lng': -74.0}, 0, 0)
        ]

        route = Route(
            route_id="single-point",
            origin="Only Location",
            destination="Only Location",
            waypoints=waypoints,
            total_distance=0,
            total_duration=0
        )

        scheduler = Scheduler(route)

        assert scheduler.has_next() is True
        wp = scheduler.get_next()
        assert wp.point_id == 0

        scheduler.advance()

        assert scheduler.has_next() is False

    def test_scheduler_with_empty_route(self):
        """Test scheduler with no waypoints."""
        route = Route(
            route_id="empty-route",
            origin="Start",
            destination="End",
            waypoints=[],
            total_distance=0,
            total_duration=0
        )

        scheduler = Scheduler(route)

        assert scheduler.has_next() is False
        assert scheduler.get_next() is None
        assert scheduler.advance() is False

    def test_run_manual_with_exception_in_callback(self, sample_route):
        """Test manual run handles exceptions in callback."""
        scheduler = Scheduler(sample_route)

        def failing_callback(waypoint):
            if waypoint.point_id == 1:
                raise ValueError("Callback error")

        # Should raise the exception
        with pytest.raises(ValueError, match="Callback error"):
            scheduler.run_manual(failing_callback)

    def test_multiple_resets(self, sample_route):
        """Test multiple resets work correctly."""
        scheduler = Scheduler(sample_route)

        # First run
        scheduler.advance()
        scheduler.advance()
        assert scheduler.current_index == 2

        # First reset
        scheduler.reset()
        assert scheduler.current_index == 0

        # Second run
        scheduler.advance()
        assert scheduler.current_index == 1

        # Second reset
        scheduler.reset()
        assert scheduler.current_index == 0
        assert len(scheduler.completed_indices) == 0

    def test_completed_indices_tracking(self, sample_route):
        """Test that completed indices are properly tracked."""
        scheduler = Scheduler(sample_route)

        assert len(scheduler.completed_indices) == 0

        scheduler.advance()
        assert scheduler.completed_indices == {0}

        scheduler.advance()
        assert scheduler.completed_indices == {0, 1}

        scheduler.advance()
        assert scheduler.completed_indices == {0, 1, 2}

    def test_progress_percentage_calculation(self, sample_route):
        """Test accurate progress percentage calculation."""
        scheduler = Scheduler(sample_route)

        # At start: 0%
        assert scheduler.get_progress()['progress_percent'] == 0.0

        # After 1 of 3: 33.33%
        scheduler.advance()
        progress1 = scheduler.get_progress()['progress_percent']
        assert progress1 == pytest.approx(33.33, rel=0.1)

        # After 2 of 3: 66.67%
        scheduler.advance()
        progress2 = scheduler.get_progress()['progress_percent']
        assert progress2 == pytest.approx(66.67, rel=0.1)

        # After 3 of 3: 100%
        scheduler.advance()
        progress3 = scheduler.get_progress()['progress_percent']
        assert progress3 == 100.0
