"""
Unit tests for Collector.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime
from src.core.collector import Collector, WaypointSummary
from src.utils.queue_manager import QueueManager, AgentResult


class TestWaypointSummary:
    """Tests for WaypointSummary dataclass."""

    def test_waypoint_summary_creation(self):
        """Test creating a waypoint summary."""
        summary = WaypointSummary(
            point_id=1,
            address="Central Park",
            location={'lat': 40.7, 'lng': -74.0}
        )

        assert summary.point_id == 1
        assert summary.address == "Central Park"
        assert summary.location['lat'] == 40.7
        assert summary.errors == []

    def test_waypoint_summary_with_content(self):
        """Test waypoint summary with content."""
        video_content = {'title': 'Test Video', 'url': 'https://youtube.com/test'}

        summary = WaypointSummary(
            point_id=2,
            address="Times Square",
            location={'lat': 40.758, 'lng': -73.985},
            video=video_content,
            chosen_type='video',
            chosen_content=video_content,
            judge_reasoning="Best visual content",
            judge_score=90
        )

        assert summary.video == video_content
        assert summary.chosen_type == 'video'
        assert summary.judge_score == 90

    def test_waypoint_summary_with_errors(self):
        """Test waypoint summary with errors."""
        summary = WaypointSummary(
            point_id=3,
            address="Brooklyn Bridge",
            location={'lat': 40.7, 'lng': -74.0},
            errors=['video: No results found', 'song: API timeout']
        )

        assert len(summary.errors) == 2
        assert 'video' in summary.errors[0]


class TestCollector:
    """Tests for Collector."""

    def test_init(self):
        """Test collector initialization."""
        mock_queue = Mock(spec=QueueManager)

        collector = Collector(route_id="test-route", queue_manager=mock_queue)

        assert collector.route_id == "test-route"
        assert collector.queue_manager == mock_queue
        assert isinstance(collector.waypoint_summaries, dict)
        assert len(collector.waypoint_summaries) == 0

    def test_collect_waypoint_success(self):
        """Test collecting successful waypoint results."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        # Create mock results
        video_result = AgentResult(
            route_id="route-1",
            point_id=1,
            agent_type='video',
            content={'selected': {'title': 'Test Video', 'url': 'https://youtube.com/test'}},
            timestamp=datetime.now(),
            error=None
        )

        judge_result = AgentResult(
            route_id="route-1",
            point_id=1,
            agent_type='judge',
            content={
                'chosen_type': 'video',
                'chosen_content': {'title': 'Test Video'},
                'reasoning': 'Most engaging',
                'score': 85
            },
            timestamp=datetime.now(),
            error=None
        )

        results = {
            'video': video_result,
            'judge': judge_result
        }

        summary = collector.collect_waypoint(
            point_id=1,
            address="Test Location",
            location={'lat': 40.0, 'lng': -74.0},
            results=results
        )

        assert summary.point_id == 1
        assert summary.address == "Test Location"
        assert summary.video is not None
        assert summary.chosen_type == 'video'
        assert summary.judge_score == 85
        assert len(summary.errors) == 0

    def test_collect_waypoint_with_errors(self):
        """Test collecting waypoint with agent errors."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        # Create error results
        video_error = AgentResult(
            route_id="route-1",
            point_id=2,
            agent_type='video',
            content={},
            timestamp=datetime.now(),
            error="No videos found"
        )

        song_error = AgentResult(
            route_id="route-1",
            point_id=2,
            agent_type='song',
            content={},
            timestamp=datetime.now(),
            error="API timeout"
        )

        results = {
            'video': video_error,
            'song': song_error
        }

        summary = collector.collect_waypoint(
            point_id=2,
            address="Error Location",
            location={'lat': 41.0, 'lng': -75.0},
            results=results
        )

        assert len(summary.errors) == 2
        assert any('No videos found' in err for err in summary.errors)
        assert any('API timeout' in err for err in summary.errors)

    def test_collect_waypoint_partial_results(self):
        """Test collecting waypoint with partial results."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        # Only video succeeds, others fail
        video_result = AgentResult(
            route_id="route-1",
            point_id=3,
            agent_type='video',
            content={'selected': {'title': 'Video Title'}},
            timestamp=datetime.now(),
            error=None
        )

        results = {'video': video_result}

        summary = collector.collect_waypoint(
            point_id=3,
            address="Partial Location",
            location={'lat': 42.0, 'lng': -76.0},
            results=results
        )

        assert summary.video is not None
        assert summary.song is None
        assert summary.story is None

    def test_get_waypoint_summary(self):
        """Test retrieving a waypoint summary."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        # Add a summary manually
        summary = WaypointSummary(
            point_id=5,
            address="Test",
            location={'lat': 40.0, 'lng': -74.0}
        )
        collector.waypoint_summaries[5] = summary

        retrieved = collector.get_waypoint_summary(5)

        assert retrieved == summary
        assert retrieved.point_id == 5

    def test_get_waypoint_summary_not_found(self):
        """Test retrieving non-existent waypoint summary."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        result = collector.get_waypoint_summary(999)

        assert result is None

    def test_get_all_summaries_ordered(self):
        """Test retrieving all summaries in order."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        # Add summaries out of order
        for pid in [3, 1, 2]:
            summary = WaypointSummary(
                point_id=pid,
                address=f"Location {pid}",
                location={'lat': 40.0, 'lng': -74.0}
            )
            collector.waypoint_summaries[pid] = summary

        summaries = collector.get_all_summaries()

        assert len(summaries) == 3
        assert summaries[0].point_id == 1
        assert summaries[1].point_id == 2
        assert summaries[2].point_id == 3

    def test_get_route_summary(self):
        """Test getting complete route summary."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="test-route-123", queue_manager=mock_queue)

        # Add some summaries
        for i in range(3):
            summary = WaypointSummary(
                point_id=i,
                address=f"Location {i}",
                location={'lat': 40.0 + i, 'lng': -74.0},
                chosen_type='video' if i % 2 == 0 else 'song',
                judge_score=80 + i * 5
            )
            collector.waypoint_summaries[i] = summary

        route_summary = collector.get_route_summary()

        assert route_summary['route_id'] == "test-route-123"
        assert route_summary['total_waypoints'] == 3
        assert len(route_summary['waypoints']) == 3
        assert 'statistics' in route_summary

    def test_calculate_statistics(self):
        """Test statistics calculation."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        summaries = [
            WaypointSummary(
                point_id=1,
                address="A",
                location={'lat': 40.0, 'lng': -74.0},
                chosen_type='video',
                judge_score=90
            ),
            WaypointSummary(
                point_id=2,
                address="B",
                location={'lat': 41.0, 'lng': -75.0},
                chosen_type='song',
                judge_score=80
            ),
            WaypointSummary(
                point_id=3,
                address="C",
                location={'lat': 42.0, 'lng': -76.0},
                chosen_type='video',
                judge_score=85,
                errors=['song: Error']
            )
        ]

        stats = collector._calculate_statistics(summaries)

        assert stats['total_waypoints'] == 3
        assert stats['content_type_distribution']['video'] == 2
        assert stats['content_type_distribution']['song'] == 1
        assert stats['average_judge_score'] == (90 + 80 + 85) / 3
        assert stats['total_errors'] == 1

    def test_calculate_statistics_empty(self):
        """Test statistics with no summaries."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        stats = collector._calculate_statistics([])

        assert stats == {}

    def test_calculate_statistics_with_errors(self):
        """Test statistics with error waypoints."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        summaries = [
            WaypointSummary(
                point_id=1,
                address="A",
                location={'lat': 40.0, 'lng': -74.0},
                chosen_type=None,  # No choice made
                errors=['All agents failed']
            ),
            WaypointSummary(
                point_id=2,
                address="B",
                location={'lat': 41.0, 'lng': -75.0},
                chosen_type='video',
                judge_score=75
            )
        ]

        stats = collector._calculate_statistics(summaries)

        assert stats['content_type_distribution']['error'] == 1
        assert stats['total_errors'] == 1

    def test_export_to_json(self, tmp_path):
        """Test exporting results to JSON file."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="export-route", queue_manager=mock_queue)

        # Add a summary
        summary = WaypointSummary(
            point_id=1,
            address="Export Test",
            location={'lat': 40.0, 'lng': -74.0},
            chosen_type='video',
            judge_score=88
        )
        collector.waypoint_summaries[1] = summary

        # Export to temp file
        output_file = tmp_path / "output" / "results.json"
        collector.export_to_json(output_file)

        assert output_file.exists()

        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert data['route_id'] == "export-route"
        assert data['total_waypoints'] == 1
        assert len(data['waypoints']) == 1
        assert data['waypoints'][0]['point_id'] == 1

    def test_export_creates_parent_directory(self, tmp_path):
        """Test that export creates parent directories if needed."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="route-1", queue_manager=mock_queue)

        # Path with non-existent parent
        output_file = tmp_path / "deeply" / "nested" / "path" / "output.json"

        collector.export_to_json(output_file)

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_print_summary(self, capsys):
        """Test printing summary to console."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="print-route", queue_manager=mock_queue)

        # Add summaries
        summary1 = WaypointSummary(
            point_id=1,
            address="First Location",
            location={'lat': 40.0, 'lng': -74.0},
            chosen_type='video',
            chosen_content={'title': 'Video Title', 'channel': 'Test Channel', 'duration': '5:00', 'url': 'https://test.com'},
            judge_reasoning="Best choice",
            judge_score=90
        )

        summary2 = WaypointSummary(
            point_id=2,
            address="Second Location",
            location={'lat': 41.0, 'lng': -75.0},
            errors=['video: Failed', 'song: Timeout']
        )

        collector.waypoint_summaries[1] = summary1
        collector.waypoint_summaries[2] = summary2

        collector.print_summary()

        captured = capsys.readouterr()
        output = captured.out

        assert "print-route" in output
        assert "First Location" in output
        assert "Second Location" in output
        assert "SELECTED: VIDEO" in output
        assert "Best choice" in output
        assert "ERRORS:" in output

    def test_collect_multiple_waypoints(self):
        """Test collecting multiple waypoints sequentially."""
        mock_queue = Mock(spec=QueueManager)
        collector = Collector(route_id="multi-route", queue_manager=mock_queue)

        # Collect multiple waypoints
        for i in range(5):
            result = AgentResult(
                route_id="multi-route",
                point_id=i,
                agent_type='video',
                content={'selected': {'title': f'Video {i}'}},
                timestamp=datetime.now(),
                error=None
            )

            collector.collect_waypoint(
                point_id=i,
                address=f"Location {i}",
                location={'lat': 40.0 + i, 'lng': -74.0},
                results={'video': result}
            )

        assert len(collector.waypoint_summaries) == 5
        summaries = collector.get_all_summaries()
        assert len(summaries) == 5
        assert summaries[0].address == "Location 0"
        assert summaries[4].address == "Location 4"
