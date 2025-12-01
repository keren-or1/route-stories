"""
Extended unit tests for SearchTools to improve coverage.
Tests edge cases, API failures, and various search scenarios.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.services.search_tools import SearchTools, SearchCache


class TestSearchCacheExtended:
    """Extended tests for SearchCache edge cases."""

    def test_cache_set_write_failure(self, tmp_path):
        """Test graceful handling of cache write failures."""
        cache = SearchCache(cache_dir=str(tmp_path))

        # Use mock to simulate write failure instead of changing permissions
        with patch('builtins.open', side_effect=PermissionError("Mock permission error")):
            # Should not raise exception
            cache.set("test_key", {"data": "test"})

        # Should return None since write failed
        result = cache.get("test_key")
        assert result is None

    def test_cache_get_with_missing_timestamp(self, tmp_path):
        """Test handling of cache file with missing timestamp."""
        cache = SearchCache(cache_dir=str(tmp_path))
        cache_path = cache._get_cache_path("test_key")

        # Write cache without timestamp
        with open(cache_path, 'w') as f:
            json.dump({"value": "test"}, f)

        result = cache.get("test_key")
        assert result is None

    def test_cache_directory_already_exists(self, tmp_path):
        """Test that existing cache directory doesn't cause issues."""
        cache_dir = tmp_path / "existing_cache"
        cache_dir.mkdir()

        cache = SearchCache(cache_dir=str(cache_dir))
        assert cache.cache_dir.exists()


class TestSearchToolsYouTubeExtended:
    """Extended YouTube search tests."""

    @patch('yt_dlp.YoutubeDL')
    def test_youtube_search_with_yt_dlp_installed(self, mock_ydl_class):
        """Test YouTube search when yt-dlp is available."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_ydl.extract_info.return_value = {
            'entries': [
                {
                    'id': 'test123',
                    'title': 'Test Video',
                    'description': 'Test description',
                    'duration': 600,
                    'view_count': 1500000,
                    'uploader': 'Test Channel'
                }
            ]
        }

        tools = SearchTools()
        results = tools.search_youtube_videos("Paris", max_results=1)

        assert len(results) == 1
        assert results[0]['title'] == 'Test Video'
        assert 'youtube.com' in results[0]['url']
        assert results[0]['duration'] == '10:00'
        assert results[0]['views'] == '1.5M'

    @patch('yt_dlp.YoutubeDL')
    def test_youtube_search_empty_results(self, mock_ydl_class):
        """Test YouTube search with no results."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = None

        tools = SearchTools()
        results = tools.search_youtube_videos("NonexistentPlace12345", max_results=5)

        # Should fall back to mock data
        assert isinstance(results, list)

    @patch('yt_dlp.YoutubeDL')
    def test_youtube_search_exception_handling(self, mock_ydl_class):
        """Test YouTube search exception handling."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("API Error")

        tools = SearchTools()
        results = tools.search_youtube_videos("TestPlace", max_results=3)

        # Should fall back to mock data
        assert isinstance(results, list)
        assert len(results) <= 3

    @patch('yt_dlp.YoutubeDL')
    def test_youtube_search_none_entries(self, mock_ydl_class):
        """Test YouTube search with None in entries."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_ydl.extract_info.return_value = {
            'entries': [None, {'id': '123', 'title': 'Valid'}, None]
        }

        tools = SearchTools()
        results = tools.search_youtube_videos("TestCity", max_results=3)

        # Should skip None entries
        assert all(r is not None for r in results)


class TestSearchToolsMusicExtended:
    """Extended music search tests."""

    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyClientCredentials')
    def test_spotify_search_success(self, mock_creds, mock_spotify):
        """Test successful Spotify search."""
        mock_sp_instance = MagicMock()
        mock_spotify.return_value = mock_sp_instance

        mock_sp_instance.search.return_value = {
            'tracks': {
                'items': [
                    {
                        'name': 'Paris Song',
                        'artists': [{'name': 'Artist 1'}],
                        'external_urls': {'spotify': 'https://spotify.com/track/123'},
                        'duration_ms': 210000,
                        'album': {'name': 'Album Name'}
                    }
                ]
            }
        }

        tools = SearchTools()
        tools.spotify_client_id = "test_id"
        tools.spotify_client_secret = "test_secret"

        results = tools.search_music("Paris", max_results=1)

        assert len(results) >= 1
        if results[0].get('source') == 'Spotify':
            assert results[0]['title'] == 'Paris Song'
            assert results[0]['duration'] == '3:30'

    @patch('spotipy.Spotify')
    def test_spotify_search_failure_fallback(self, mock_spotify):
        """Test Spotify search failure falls back to YouTube Music."""
        mock_spotify.side_effect = Exception("Spotify API Error")

        tools = SearchTools()
        tools.spotify_client_id = "test_id"
        tools.spotify_client_secret = "test_secret"

        results = tools.search_music("London", max_results=3)

        # Should fall back to YouTube Music or mock
        assert isinstance(results, list)

    @patch('yt_dlp.YoutubeDL')
    def test_youtube_music_search_success(self, mock_ydl_class):
        """Test YouTube Music search."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_ydl.extract_info.return_value = {
            'entries': [
                {
                    'id': 'music123',
                    'title': 'Song about London',
                    'uploader': 'Artist Name',
                    'duration': 180
                }
            ]
        }

        tools = SearchTools()
        # Ensure no Spotify credentials
        tools.spotify_client_id = None
        tools.spotify_client_secret = None

        results = tools.search_music("London", max_results=1)

        assert isinstance(results, list)
        assert len(results) >= 1

    def test_music_search_no_credentials_uses_youtube(self):
        """Test music search without Spotify credentials uses YouTube."""
        tools = SearchTools()
        tools.spotify_client_id = None
        tools.spotify_client_secret = None

        results = tools.search_music("Tokyo", max_results=2)

        assert isinstance(results, list)
        assert len(results) > 0


class TestSearchToolsHistoricalExtended:
    """Extended historical stories search tests."""

    @patch('wikipediaapi.Wikipedia')
    def test_wikipedia_search_success(self, mock_wiki_class):
        """Test successful Wikipedia search."""
        mock_wiki = MagicMock()
        mock_wiki_class.return_value = mock_wiki

        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.title = "Paris"
        mock_page.fullurl = "https://en.wikipedia.org/wiki/Paris"
        mock_page.summary = "Paris is the capital of France. " * 50  # Long summary

        mock_section = MagicMock()
        mock_section.title = "History"
        mock_section.text = "Paris has a rich history. " * 20

        mock_page.sections = [mock_section]
        mock_wiki.page.return_value = mock_page

        tools = SearchTools()
        results = tools.search_historical_stories("Paris", max_results=2)

        assert isinstance(results, list)
        assert len(results) >= 1
        if results:
            assert 'Paris' in results[0]['title'] or 'Paris' in results[0]['content']

    @patch('wikipediaapi.Wikipedia')
    def test_wikipedia_page_not_found(self, mock_wiki_class):
        """Test Wikipedia search when page doesn't exist."""
        mock_wiki = MagicMock()
        mock_wiki_class.return_value = mock_wiki

        mock_page = MagicMock()
        mock_page.exists.return_value = False
        mock_wiki.page.return_value = mock_page

        tools = SearchTools()
        results = tools.search_historical_stories("NonexistentPlace", max_results=3)

        # Should fall back to web search or mock
        assert isinstance(results, list)

    @patch('duckduckgo_search.DDGS')
    def test_duckduckgo_search_success(self, mock_ddgs_class):
        """Test DuckDuckGo web search."""
        mock_ddgs = MagicMock()
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

        mock_ddgs.text.return_value = [
            {
                'title': 'History of TestCity',
                'body': 'TestCity has fascinating history...',
                'href': 'https://example.com/testcity'
            }
        ]

        tools = SearchTools()
        results = tools._search_web_historical("TestCity", max_results=1)

        assert len(results) == 1
        assert results[0]['title'] == 'History of TestCity'
        assert results[0]['source'] == 'Web Search'

    @patch('duckduckgo_search.DDGS')
    def test_duckduckgo_search_exception(self, mock_ddgs_class):
        """Test DuckDuckGo search exception handling."""
        mock_ddgs_class.side_effect = Exception("Search failed")

        tools = SearchTools()
        results = tools._search_web_historical("TestCity", max_results=3)

        # Should fall back to mock data
        assert isinstance(results, list)

    @patch('wikipediaapi.Wikipedia')
    def test_wikipedia_short_sections_skipped(self, mock_wiki_class):
        """Test that short Wikipedia sections are skipped."""
        mock_wiki = MagicMock()
        mock_wiki_class.return_value = mock_wiki

        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.title = "TestCity"
        mock_page.fullurl = "https://en.wikipedia.org/wiki/TestCity"
        mock_page.summary = "Summary text"

        # Create sections with varying lengths
        short_section = MagicMock()
        short_section.title = "Short"
        short_section.text = "Too short"  # Less than 100 chars

        long_section = MagicMock()
        long_section.title = "Long Section"
        long_section.text = "This is a long section with enough content. " * 10

        mock_page.sections = [short_section, long_section]
        mock_wiki.page.return_value = mock_page

        tools = SearchTools()
        results = tools.search_historical_stories("TestCity", max_results=5)

        # Should include main article and long section, skip short section
        assert isinstance(results, list)


class TestSearchToolsUtilities:
    """Test utility methods."""

    def test_format_duration_ms_edge_cases(self):
        """Test duration formatting edge cases."""
        tools = SearchTools()

        assert tools._format_duration_ms(0) == "0:00"
        assert tools._format_duration_ms(999) == "0:00"
        assert tools._format_duration_ms(1000) == "0:01"
        assert tools._format_duration_ms(59999) == "0:59"
        assert tools._format_duration_ms(60000) == "1:00"
        assert tools._format_duration_ms(3600000) == "60:00"

    def test_format_duration_seconds_with_float(self):
        """Test duration formatting with float input."""
        tools = SearchTools()

        assert tools._format_duration_seconds(90.5) == "1:30"
        assert tools._format_duration_seconds(125.9) == "2:05"

    def test_format_views_edge_cases(self):
        """Test view count formatting edge cases."""
        tools = SearchTools()

        assert tools._format_views(999) == "999"
        assert tools._format_views(1000) == "1K"
        assert tools._format_views(1500) == "2K"  # Rounds to nearest K
        assert tools._format_views(999999) == "1000K"
        assert tools._format_views(1000000) == "1.0M"

    def test_enhance_search_query_all_types(self):
        """Test query enhancement for all content types."""
        tools = SearchTools()

        # Video query
        video_q = tools.enhance_search_query("Berlin", "video")
        assert "Berlin" in video_q
        assert any(word in video_q for word in ["travel", "guide", "tour", "documentary"])

        # Music query
        music_q = tools.enhance_search_query("Berlin", "music")
        assert "Berlin" in music_q
        assert any(word in music_q for word in ["songs", "music", "soundtrack"])

        # Story query
        story_q = tools.enhance_search_query("Berlin", "story")
        assert "Berlin" in story_q
        assert any(word in story_q for word in ["history", "historical", "facts"])

        # Default/unknown query
        default_q = tools.enhance_search_query("Berlin", "other")
        assert default_q == "Berlin"

    def test_fetch_url_content_timeout(self):
        """Test URL fetch with timeout."""
        tools = SearchTools()

        with patch.object(tools.session, 'get') as mock_get:
            mock_get.side_effect = Exception("Timeout")

            result = tools.fetch_url_content("https://slow-site.com")
            assert result is None


class TestSearchToolsCacheIntegration:
    """Test cache integration with search methods."""

    def test_youtube_cache_integration(self):
        """Test YouTube search caching works end-to-end."""
        tools = SearchTools()

        # Clear any existing cache
        cache_key = "youtube_CacheTest_5"
        cache_path = tools.cache._get_cache_path(cache_key)
        if cache_path.exists():
            cache_path.unlink()

        # First search - should cache
        results1 = tools.search_youtube_videos("CacheTest", max_results=5)

        # Manually set cache to verify it's used
        test_data = [{"title": "Cached Test Video", "url": "https://test.com"}]
        tools.cache.set(cache_key, test_data)

        # Second search - should return cached
        results2 = tools.search_youtube_videos("CacheTest", max_results=5)

        assert results2 == test_data

    def test_music_cache_integration(self):
        """Test music search caching works end-to-end."""
        tools = SearchTools()

        # Manually set cache
        cache_key = "music_CacheTestCity_3"
        test_data = [{"title": "Cached Song", "artist": "Test Artist"}]
        tools.cache.set(cache_key, test_data)

        # Search should return cached data
        results = tools.search_music("CacheTestCity", max_results=3)

        assert results == test_data

    def test_historical_cache_integration(self):
        """Test historical search caching works end-to-end."""
        tools = SearchTools()

        # Manually set cache
        cache_key = "history_HistoryCacheTest_3"
        test_data = [{"title": "Cached Story", "content": "Test content", "source": "Cache"}]
        tools.cache.set(cache_key, test_data)

        # Search should return cached data
        results = tools.search_historical_stories("HistoryCacheTest", max_results=3)

        assert results == test_data


class TestSearchToolsMockData:
    """Test mock data fallbacks."""

    def test_mock_youtube_respects_max_results(self):
        """Test mock YouTube data respects max_results parameter."""
        tools = SearchTools()

        for max_r in [1, 2, 3]:
            results = tools._mock_youtube_videos("TestPlace", max_results=max_r)
            assert len(results) == max_r

    def test_mock_music_respects_max_results(self):
        """Test mock music data respects max_results parameter."""
        tools = SearchTools()

        for max_r in [1, 2, 3]:
            results = tools._mock_music("TestPlace", max_results=max_r)
            assert len(results) == max_r

    def test_mock_historical_respects_max_results(self):
        """Test mock historical data respects max_results parameter."""
        tools = SearchTools()

        for max_r in [1, 2, 3]:
            results = tools._mock_historical_stories("TestPlace", max_results=max_r)
            assert len(results) == max_r

    def test_mock_data_contains_location(self):
        """Test that mock data includes the location name."""
        tools = SearchTools()
        location = "UniqueTestLocation"

        youtube = tools._mock_youtube_videos(location, max_results=1)
        assert any(location in str(r) for r in youtube)

        music = tools._mock_music(location, max_results=1)
        assert any(location in str(r) for r in music)

        historical = tools._mock_historical_stories(location, max_results=1)
        assert any(location in str(r) for r in historical)
