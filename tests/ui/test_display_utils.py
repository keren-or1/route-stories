"""Tests for UI display utilities."""

import pytest
from src.ui.display_utils import (
    format_route_display,
    format_waypoint_header,
    format_content_item,
    SEPARATOR_LONG,
    SEPARATOR_SHORT
)


class TestFormatRouteDisplay:
    """Test route display formatting."""

    def test_format_route_display_basic(self):
        """Test basic route display formatting."""
        result = format_route_display(
            origin="Tel Aviv",
            destination="Jerusalem",
            distance_m=65000,
            duration_s=3600,
            num_waypoints=5
        )

        assert "Tel Aviv" in result
        assert "Jerusalem" in result
        assert "65.0 km" in result
        assert "60 minutes" in result
        assert "5" in result
        assert SEPARATOR_LONG in result

    def test_format_route_display_formatting(self):
        """Test that route display includes proper formatting."""
        result = format_route_display(
            origin="A",
            destination="B",
            distance_m=10000,
            duration_s=600,
            num_waypoints=2
        )

        lines = result.split("\n")
        assert len(lines) > 5
        assert "ROUTE INFORMATION" in result


class TestFormatWaypointHeader:
    """Test waypoint header formatting."""

    def test_format_waypoint_header_basic(self):
        """Test basic waypoint header formatting."""
        result = format_waypoint_header(
            index=0,
            total=5,
            address="Tel Aviv",
            lat=32.0853,
            lng=34.7818
        )

        assert "WAYPOINT 1 of 5" in result
        assert "Tel Aviv" in result
        assert "32.085300" in result
        assert "34.781800" in result
        assert SEPARATOR_SHORT in result

    def test_format_waypoint_header_multiple_waypoints(self):
        """Test waypoint header with different indices."""
        result = format_waypoint_header(
            index=2,
            total=10,
            address="Jerusalem",
            lat=31.7683,
            lng=35.2137
        )

        assert "WAYPOINT 3 of 10" in result
        assert "Jerusalem" in result


class TestFormatContentItem:
    """Test content item formatting."""

    def test_format_content_item_with_url(self):
        """Test content item formatting with URL."""
        result = format_content_item(
            title="Amazing Video",
            source="YouTube",
            url="https://youtube.com/watch?v=123"
        )

        assert "Amazing Video" in result
        assert "YouTube" in result
        assert "https://youtube.com/watch?v=123" in result
        assert "Title:" in result
        assert "Source:" in result
        assert "URL:" in result

    def test_format_content_item_without_url(self):
        """Test content item formatting without URL."""
        result = format_content_item(
            title="A Story",
            source="Wikipedia",
            url=None
        )

        assert "A Story" in result
        assert "Wikipedia" in result
        assert "URL:" not in result

    def test_format_content_item_empty_url(self):
        """Test content item with empty string URL."""
        result = format_content_item(
            title="Song",
            source="Spotify",
            url=""
        )

        assert "Song" in result
        assert "Spotify" in result
        # Empty string is falsy, so URL should not be included
        assert "URL:" not in result
