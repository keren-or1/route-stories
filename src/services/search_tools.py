"""
Search tools for finding videos, songs, and stories about locations.
Integrates with real APIs: YouTube, Wikipedia, Spotify, and DuckDuckGo.
"""

import requests
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger
from src.services.search_cache import SearchCache
from src.services.youtube_search import YouTubeSearch
from src.services.music_search import MusicSearch
from src.services.wikipedia_search import WikipediaSearch

logger = get_logger("search_tools")


class SearchTools:
    """Collection of search utilities for different content types."""

    def __init__(self):
        """Initialize search tools with API clients and cache."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.cache = SearchCache()

        # Initialize specialized search modules
        self.youtube_search = YouTubeSearch(self.cache)
        self.music_search = MusicSearch(self.cache)
        self.wikipedia_search = WikipediaSearch(self.cache)

        # Expose Spotify credentials for backward compatibility
        self.spotify_client_id = self.music_search.spotify_client_id
        self.spotify_client_secret = self.music_search.spotify_client_secret
        self.spotify_token = self.music_search.spotify_token

        logger.info("SearchTools initialized with real API integrations")

    def search_youtube_videos(
        self,
        location: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for real YouTube videos about a location."""
        return self.youtube_search.search_videos(location, max_results)

    def search_music(
        self,
        location: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for music/songs related to a location."""
        return self.music_search.search_music(location, max_results)

    def search_historical_stories(
        self,
        location: str,
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for real historical stories and facts using Wikipedia API."""
        return self.wikipedia_search.search_historical_stories(location, max_results)

    def fetch_url_content(self, url: str) -> Optional[str]:
        """Fetch content from a URL."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def enhance_search_query(self, location: str, content_type: str) -> str:
        """Build an enhanced search query for a specific content type."""
        queries = {
            "video": f"{location} travel guide tour documentary walking",
            "music": f"songs about {location} music soundtrack theme",
            "story": f"{location} history historical facts interesting stories"
        }
        return queries.get(content_type, location)

    # Backward compatibility methods for tests
    def _format_duration_ms(self, duration_ms: int) -> str:
        """Convert milliseconds to MM:SS format."""
        from src.services.music_search_utils import format_duration_ms
        return format_duration_ms(duration_ms)

    def _format_duration_seconds(self, duration_seconds) -> str:
        """Convert seconds to MM:SS format."""
        return self.youtube_search._format_duration_seconds(duration_seconds)

    def _format_views(self, view_count: int) -> str:
        """Format view count to human-readable format."""
        return self.youtube_search._format_views(view_count)

    def _mock_youtube_videos(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback mock YouTube data."""
        return self.youtube_search._mock_youtube_videos(location, max_results)

    def _mock_music(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback mock music data."""
        from src.services.music_search_utils import get_mock_music
        return get_mock_music(location, max_results)

    def _mock_historical_stories(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback mock historical data."""
        from src.services.wikipedia_search_utils import get_mock_historical_stories
        return get_mock_historical_stories(location, max_results)

    def _search_youtube_music(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Search YouTube for music."""
        return self.music_search._search_youtube_music(location, max_results)

    def _search_web_historical(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Search web for historical information."""
        return self.wikipedia_search._search_web_historical(location, max_results)
