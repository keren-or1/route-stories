"""Tests for collector printer utilities."""

import pytest
from io import StringIO
from unittest.mock import patch
from src.core.collector_printer import (
    print_waypoint_summary,
    print_statistics,
    print_full_summary,
    _print_video_content,
    _print_song_content,
    _print_story_content
)
from src.core.collector_models import WaypointSummary


class TestPrintWaypointSummary:
    """Test waypoint summary printing."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_waypoint_with_video(self, mock_stdout):
        """Test printing waypoint with video content."""
        summary = WaypointSummary(
            point_id=1,
            address="Test Location",
            location={"lat": 0, "lng": 0},
            chosen_type="video",
            chosen_content={
                "title": "Test Video",
                "channel": "Test Channel",
                "duration": "5:30",
                "url": "https://youtube.com/test"
            },
            judge_reasoning="Good match",
            judge_score=85.0
        )

        print_waypoint_summary(summary)

        output = mock_stdout.getvalue()
        assert "Waypoint 1" in output
        assert "Test Location" in output
        assert "VIDEO" in output
        assert "Test Video" in output
        assert "Good match" in output
        assert "85.0" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_waypoint_with_song(self, mock_stdout):
        """Test printing waypoint with song content."""
        summary = WaypointSummary(
            point_id=2,
            address="Test Place",
            location={"lat": 0, "lng": 0},
            chosen_type="song",
            chosen_content={
                "title": "Test Song",
                "artist": "Test Artist",
                "genre": "Pop",
                "url": "https://spotify.com/test"
            }
        )

        print_waypoint_summary(summary)

        output = mock_stdout.getvalue()
        assert "SONG" in output
        assert "Test Song" in output
        assert "Test Artist" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_waypoint_with_story(self, mock_stdout):
        """Test printing waypoint with story content."""
        summary = WaypointSummary(
            point_id=3,
            address="Historic Site",
            location={"lat": 0, "lng": 0},
            chosen_type="story",
            chosen_content={
                "title": "Historical Fact",
                "content": "This is a long story about the place " * 10,
                "source": "Wikipedia"
            }
        )

        print_waypoint_summary(summary)

        output = mock_stdout.getvalue()
        assert "STORY" in output
        assert "Historical Fact" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_waypoint_with_errors(self, mock_stdout):
        """Test printing waypoint with errors."""
        summary = WaypointSummary(
            point_id=4,
            address="Error Location",
            location={"lat": 0, "lng": 0},
            errors=["Error 1", "Error 2"]
        )

        print_waypoint_summary(summary)

        output = mock_stdout.getvalue()
        assert "ERRORS" in output
        assert "Error 1" in output
        assert "Error 2" in output


class TestPrintStatistics:
    """Test statistics printing."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_statistics(self, mock_stdout):
        """Test printing statistics."""
        stats = {
            "total_waypoints": 5,
            "content_type_distribution": {"video": 2, "song": 2, "story": 1},
            "average_judge_score": 82.5,
            "total_errors": 0
        }

        print_statistics(stats)

        output = mock_stdout.getvalue()
        assert "STATISTICS" in output
        assert "5" in output
        assert "82.5" in output


class TestPrintFullSummary:
    """Test full summary printing."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_full_summary(self, mock_stdout):
        """Test printing full route summary."""
        summaries = [
            WaypointSummary(
                point_id=1,
                address="Location 1",
                location={"lat": 0, "lng": 0},
                chosen_type="video",
                chosen_content={"title": "Video 1"}
            ),
            WaypointSummary(
                point_id=2,
                address="Location 2",
                location={"lat": 0, "lng": 0},
                chosen_type="song",
                chosen_content={"title": "Song 1"}
            )
        ]
        stats = {
            "total_waypoints": 2,
            "content_type_distribution": {"video": 1, "song": 1},
            "average_judge_score": 80.0,
            "total_errors": 0
        }

        print_full_summary("route123", summaries, stats)

        output = mock_stdout.getvalue()
        assert "ROUTE SUMMARY - route123" in output
        assert "Location 1" in output
        assert "Location 2" in output
        assert "STATISTICS" in output


class TestContentPrinters:
    """Test individual content type printers."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_video_content(self, mock_stdout):
        """Test printing video content."""
        content = {
            "title": "Video Title",
            "channel": "Channel Name",
            "duration": "10:00",
            "url": "https://youtube.com/test"
        }

        _print_video_content(content)

        output = mock_stdout.getvalue()
        assert "Video Title" in output
        assert "Channel Name" in output
        assert "10:00" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_song_content(self, mock_stdout):
        """Test printing song content."""
        content = {
            "title": "Song Title",
            "artist": "Artist Name",
            "genre": "Rock",
            "url": "https://spotify.com/test"
        }

        _print_song_content(content)

        output = mock_stdout.getvalue()
        assert "Song Title" in output
        assert "Artist Name" in output
        assert "Rock" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_story_content(self, mock_stdout):
        """Test printing story content."""
        content = {
            "title": "Story Title",
            "content": "Story content text" * 20,
            "source": "Wikipedia"
        }

        _print_story_content(content)

        output = mock_stdout.getvalue()
        assert "Story Title" in output
        assert "Wikipedia" in output
