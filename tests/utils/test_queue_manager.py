"""
Unit tests for QueueManager.
"""

import pytest
from datetime import datetime
from src.utils.queue_manager import QueueManager, AgentResult


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_result_creation_success(self):
        """Test creating a successful result."""
        result = AgentResult(
            route_id="route-1",
            point_id=5,
            agent_type="video",
            content={"title": "Test Video"},
            timestamp=datetime.now(),
            error=None
        )

        assert result.route_id == "route-1"
        assert result.point_id == 5
        assert result.agent_type == "video"
        assert result.content == {"title": "Test Video"}
        assert result.error is None

    def test_result_creation_error(self):
        """Test creating an error result."""
        result = AgentResult(
            route_id="route-2",
            point_id=3,
            agent_type="song",
            content={},
            timestamp=datetime.now(),
            error="API timeout"
        )

        assert result.error == "API timeout"

    def test_result_repr(self):
        """Test result string representation."""
        # Success case
        success_result = AgentResult(
            route_id="r1",
            point_id=1,
            agent_type="story",
            content={"data": "test"},
            timestamp=datetime.now(),
            error=None
        )
        repr_str = repr(success_result)
        assert "story" in repr_str
        assert "SUCCESS" in repr_str

        # Error case
        error_result = AgentResult(
            route_id="r1",
            point_id=1,
            agent_type="video",
            content={},
            timestamp=datetime.now(),
            error="Failed"
        )
        repr_str = repr(error_result)
        assert "ERROR" in repr_str


class TestQueueManager:
    """Tests for QueueManager."""

    def test_init(self):
        """Test queue manager initialization."""
        queue = QueueManager()

        assert queue.results_queue is not None
        assert queue.get_queue_size() == 0

    def test_put_result(self):
        """Test adding a result to the queue."""
        queue = QueueManager()

        result = AgentResult(
            route_id="route-1",
            point_id=1,
            agent_type="video",
            content={"title": "Test"},
            timestamp=datetime.now(),
            error=None
        )

        queue.put_result(result)

        assert queue.get_queue_size() == 1

    def test_get_result(self):
        """Test retrieving a result from the queue."""
        queue = QueueManager()

        result = AgentResult(
            route_id="route-1",
            point_id=1,
            agent_type="video",
            content={"data": "test"},
            timestamp=datetime.now(),
            error=None
        )

        queue.put_result(result)
        retrieved = queue.get_result(timeout=1.0)

        assert retrieved is not None
        assert retrieved.route_id == "route-1"
        assert retrieved.agent_type == "video"

    def test_get_result_timeout(self):
        """Test getting result with timeout on empty queue."""
        queue = QueueManager()

        result = queue.get_result(timeout=0.1)

        assert result is None

    def test_get_point_results(self):
        """Test retrieving results for a specific point."""
        queue = QueueManager()

        # Add multiple results for same point
        for agent_type in ["video", "song", "story"]:
            result = AgentResult(
                route_id="route-1",
                point_id=1,
                agent_type=agent_type,
                content={agent_type: "data"},
                timestamp=datetime.now(),
                error=None
            )
            queue.put_result(result)

        point_results = queue.get_point_results("route-1", 1)

        assert len(point_results) == 3
        assert "video" in point_results
        assert "song" in point_results
        assert "story" in point_results

    def test_get_point_results_empty(self):
        """Test getting results for non-existent point."""
        queue = QueueManager()

        results = queue.get_point_results("nonexistent-route", 999)

        assert len(results) == 0

    def test_has_all_content_results_true(self):
        """Test checking for all content results."""
        queue = QueueManager()

        # Add all three content agent results
        for agent_type in ["video", "song", "story"]:
            result = AgentResult(
                route_id="route-1",
                point_id=1,
                agent_type=agent_type,
                content={},
                timestamp=datetime.now(),
                error=None
            )
            queue.put_result(result)

        has_all = queue.has_all_content_results("route-1", 1)

        assert has_all is True

    def test_has_all_content_results_false(self):
        """Test when not all content results are present."""
        queue = QueueManager()

        # Add only two content agent results
        for agent_type in ["video", "song"]:
            result = AgentResult(
                route_id="route-1",
                point_id=1,
                agent_type=agent_type,
                content={},
                timestamp=datetime.now(),
                error=None
            )
            queue.put_result(result)

        has_all = queue.has_all_content_results("route-1", 1)

        assert has_all is False

    def test_get_all_results_for_route(self):
        """Test getting all results for an entire route."""
        queue = QueueManager()

        # Add results for multiple points
        for point_id in [1, 2, 3]:
            result = AgentResult(
                route_id="route-1",
                point_id=point_id,
                agent_type="video",
                content={},
                timestamp=datetime.now(),
                error=None
            )
            queue.put_result(result)

        route_results = queue.get_all_results_for_route("route-1")

        assert len(route_results) == 3
        assert 1 in route_results
        assert 2 in route_results
        assert 3 in route_results

    def test_clear_route_results(self):
        """Test clearing results for a specific route."""
        queue = QueueManager()

        # Add results for route
        result = AgentResult(
            route_id="route-1",
            point_id=1,
            agent_type="video",
            content={},
            timestamp=datetime.now(),
            error=None
        )
        queue.put_result(result)

        # Verify results exist
        assert len(queue.get_all_results_for_route("route-1")) == 1

        # Clear
        queue.clear_route_results("route-1")

        # Verify cleared
        assert len(queue.get_all_results_for_route("route-1")) == 0

    def test_multiple_routes(self):
        """Test managing results for multiple routes."""
        queue = QueueManager()

        # Add results for different routes
        for route_id in ["route-1", "route-2", "route-3"]:
            result = AgentResult(
                route_id=route_id,
                point_id=1,
                agent_type="video",
                content={},
                timestamp=datetime.now(),
                error=None
            )
            queue.put_result(result)

        # Verify each route has results
        assert len(queue.get_all_results_for_route("route-1")) == 1
        assert len(queue.get_all_results_for_route("route-2")) == 1
        assert len(queue.get_all_results_for_route("route-3")) == 1

    def test_wait_for_results_success(self):
        """Test waiting for results successfully."""
        queue = QueueManager()

        # Add expected results
        for agent_type in ["video", "song"]:
            result = AgentResult(
                route_id="route-1",
                point_id=1,
                agent_type=agent_type,
                content={},
                timestamp=datetime.now(),
                error=None
            )
            queue.put_result(result)

        # Wait for those results
        success = queue.wait_for_results(
            "route-1",
            1,
            ["video", "song"],
            timeout=1.0,
            poll_interval=0.05
        )

        assert success is True

    def test_wait_for_results_timeout(self):
        """Test waiting for results with timeout."""
        queue = QueueManager()

        # Don't add any results
        success = queue.wait_for_results(
            "route-1",
            1,
            ["video", "song", "story"],
            timeout=0.2,
            poll_interval=0.05
        )

        assert success is False

    def test_queue_size_tracking(self):
        """Test queue size tracking."""
        queue = QueueManager()

        assert queue.get_queue_size() == 0

        # Add 3 results
        for i in range(3):
            result = AgentResult(
                route_id="route-1",
                point_id=i,
                agent_type="video",
                content={},
                timestamp=datetime.now(),
                error=None
            )
            queue.put_result(result)

        assert queue.get_queue_size() == 3

        # Get one result
        queue.get_result()

        assert queue.get_queue_size() == 2

    def test_error_results_stored(self):
        """Test that error results are properly stored."""
        queue = QueueManager()

        error_result = AgentResult(
            route_id="route-1",
            point_id=1,
            agent_type="video",
            content={},
            timestamp=datetime.now(),
            error="API failed"
        )

        queue.put_result(error_result)

        point_results = queue.get_point_results("route-1", 1)

        assert "video" in point_results
        assert point_results["video"].error == "API failed"
