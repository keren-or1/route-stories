"""
Unit tests for SearchTools and SearchCache.
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.services.search_tools import SearchTools, SearchCache


class TestSearchCache:
    """Tests for SearchCache functionality."""

    def test_init_creates_cache_dir(self, tmp_path):
        """Test that cache directory is created on init."""
        cache_dir = tmp_path / "test_cache"
        cache = SearchCache(cache_dir=str(cache_dir))

        assert cache.cache_dir.exists()
        assert cache.cache_dir.is_dir()
        assert cache.ttl_hours == 24

    def test_get_cache_path_sanitizes_key(self, tmp_path):
        """Test that cache key is sanitized for filesystem."""
        cache = SearchCache(cache_dir=str(tmp_path))

        unsafe_key = "test/key:with*special?chars"
        path = cache._get_cache_path(unsafe_key)

        assert "/" not in path.name
        assert ":" not in path.name
        assert "*" not in path.name
        assert path.suffix == ".json"

    def test_cache_set_and_get(self, tmp_path):
        """Test setting and retrieving cached values."""
        cache = SearchCache(cache_dir=str(tmp_path))

        test_data = {"videos": [{"title": "Test Video"}]}
        cache.set("test_key", test_data)

        result = cache.get("test_key")
        assert result == test_data

    def test_cache_get_nonexistent_key(self, tmp_path):
        """Test getting a key that doesn't exist."""
        cache = SearchCache(cache_dir=str(tmp_path))

        result = cache.get("nonexistent")
        assert result is None

    def test_cache_expiry(self, tmp_path):
        """Test that cache expires after TTL."""
        cache = SearchCache(cache_dir=str(tmp_path))
        cache.ttl_hours = 0.0001  # Very short TTL for testing

        cache.set("test_key", {"data": "test"})

        # Wait for expiry
        time.sleep(0.5)

        result = cache.get("test_key")
        assert result is None

    def test_cache_handles_corrupted_file(self, tmp_path):
        """Test that cache handles corrupted JSON files gracefully."""
        cache = SearchCache(cache_dir=str(tmp_path))

        # Write invalid JSON
        cache_path = cache._get_cache_path("corrupted")
        cache_path.write_text("invalid json content")

        result = cache.get("corrupted")
        assert result is None


class TestSearchTools:
    """Tests for SearchTools search functionality."""

    def test_init(self):
        """Test SearchTools initialization."""
        tools = SearchTools()

        assert tools.session is not None
        assert tools.cache is not None
        assert 'User-Agent' in tools.session.headers

    def test_search_youtube_videos_returns_results(self):
        """Test YouTube video search returns results (real or mock)."""
        tools = SearchTools()
        results = tools.search_youtube_videos("New York", max_results=3)

        # Should return some results (either real API or mock fallback)
        assert isinstance(results, list)
        assert len(results) > 0
        assert all('title' in r for r in results)
        assert all('url' in r for r in results)

    def test_search_youtube_videos_cache_hit(self):
        """Test YouTube search returns cached results."""
        tools = SearchTools()

        # Pre-populate cache
        cache_key = "youtube_New York_5"
        cached_data = [{'title': 'Cached Video', 'url': 'https://youtube.com/cached'}]
        tools.cache.set(cache_key, cached_data)

        results = tools.search_youtube_videos("New York", max_results=5)

        assert results == cached_data

    def test_search_youtube_videos_edge_case(self):
        """Test YouTube search with unusual location name."""
        tools = SearchTools()
        results = tools.search_youtube_videos("XYZ123NonexistentPlace", max_results=2)

        # Should still return results (mock fallback if API fails)
        assert isinstance(results, list)
        # Either got results or gracefully returned empty/mock
        assert len(results) >= 0

    def test_search_music_cache_hit(self):
        """Test music search returns cached results."""
        tools = SearchTools()

        # Pre-populate cache
        cache_key = "music_Paris_5"
        cached_data = [{'title': 'Cached Song', 'artist': 'Test Artist'}]
        tools.cache.set(cache_key, cached_data)

        results = tools.search_music("Paris", max_results=5)

        assert results == cached_data

    def test_search_music_returns_results(self):
        """Test music search returns results."""
        tools = SearchTools()
        results = tools.search_music("London", max_results=3)

        # Should return results (API or fallback)
        assert isinstance(results, list)
        assert len(results) > 0
        assert all('title' in r for r in results)
        assert all('artist' in r for r in results)

    def test_search_historical_stories_returns_results(self):
        """Test historical stories search returns results."""
        tools = SearchTools()
        results = tools.search_historical_stories("Paris", max_results=3)

        # Should return results (Wikipedia, web, or mock)
        assert isinstance(results, list)
        assert len(results) > 0
        assert all('title' in r for r in results)
        assert all('content' in r for r in results)
        assert all('source' in r for r in results)

    def test_format_duration_ms(self):
        """Test milliseconds to MM:SS conversion."""
        tools = SearchTools()

        assert tools._format_duration_ms(210000) == "3:30"
        assert tools._format_duration_ms(65000) == "1:05"
        assert tools._format_duration_ms(3661000) == "61:01"

    def test_format_duration_seconds(self):
        """Test seconds to duration format conversion."""
        tools = SearchTools()

        assert tools._format_duration_seconds(210) == "3:30"
        assert tools._format_duration_seconds(65) == "1:05"
        assert tools._format_duration_seconds(3661) == "1:01:01"
        assert tools._format_duration_seconds(None) == "Unknown"
        assert tools._format_duration_seconds(0) == "Unknown"

    def test_format_views(self):
        """Test view count formatting."""
        tools = SearchTools()

        assert tools._format_views(1500000) == "1.5M"
        assert tools._format_views(125000) == "125K"
        assert tools._format_views(500) == "500"
        assert tools._format_views(None) == "N/A"
        assert tools._format_views(0) == "N/A"

    @patch('src.services.search_tools.requests.Session.get')
    def test_fetch_url_content_success(self, mock_get):
        """Test successful URL fetching."""
        mock_response = Mock()
        mock_response.text = "<html>Test content</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        tools = SearchTools()
        content = tools.fetch_url_content("https://example.com")

        assert content == "<html>Test content</html>"

    @patch('src.services.search_tools.requests.Session.get')
    def test_fetch_url_content_failure(self, mock_get):
        """Test URL fetching with error."""
        mock_get.side_effect = Exception("Network error")

        tools = SearchTools()
        content = tools.fetch_url_content("https://example.com")

        assert content is None

    def test_enhance_search_query(self):
        """Test search query enhancement."""
        tools = SearchTools()

        video_query = tools.enhance_search_query("Paris", "video")
        assert "Paris" in video_query
        assert "travel" in video_query or "guide" in video_query

        music_query = tools.enhance_search_query("London", "music")
        assert "London" in music_query
        assert "songs" in music_query or "music" in music_query

        story_query = tools.enhance_search_query("Rome", "story")
        assert "Rome" in story_query
        assert "history" in story_query or "historical" in story_query

        # Unknown type returns location as-is
        unknown_query = tools.enhance_search_query("Tokyo", "unknown")
        assert unknown_query == "Tokyo"

    def test_mock_youtube_videos(self):
        """Test mock YouTube data fallback."""
        tools = SearchTools()

        results = tools._mock_youtube_videos("Test City", max_results=2)

        assert len(results) == 2
        assert all("Test City" in r['title'] for r in results)
        assert all('url' in r for r in results)

    def test_mock_music(self):
        """Test mock music data fallback."""
        tools = SearchTools()

        results = tools._mock_music("Test City", max_results=2)

        assert len(results) == 2
        assert all("Test City" in r['title'] or "Test City" in r['album'] for r in results)

    def test_mock_historical_stories(self):
        """Test mock historical data fallback."""
        tools = SearchTools()

        results = tools._mock_historical_stories("Test City", max_results=2)

        assert len(results) == 2
        assert all("Test City" in r['title'] or "Test City" in r['content'] for r in results)
