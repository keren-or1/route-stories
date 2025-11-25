"""
Search tools for finding videos, songs, and stories about locations.
Integrates with real APIs: YouTube, Wikipedia, Spotify, and DuckDuckGo.
"""

import os
import time
import json
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from datetime import datetime, timedelta
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger("search_tools")


class SearchCache:
    """Simple file-based cache for search results (24-hour TTL)."""

    def __init__(self, cache_dir: str = ".cache"):
        """Initialize cache with directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_hours = 24

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if it exists and is not expired."""
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if cache is expired
            cached_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cached_time > timedelta(hours=self.ttl_hours):
                cache_path.unlink()  # Delete expired cache
                return None

            logger.debug(f"Cache hit for key: {key}")
            return data['value']

        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Cache a value with current timestamp."""
        cache_path = self._get_cache_path(key)

        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'value': value
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Cached result for key: {key}")

        except Exception as e:
            logger.warning(f"Cache write error: {e}")


class SearchTools:
    """
    Collection of search utilities for different content types.
    Uses real APIs: YouTube, Wikipedia, Spotify, and DuckDuckGo.
    """

    def __init__(self):
        """Initialize search tools with API clients and cache."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.cache = SearchCache()

        # Load optional Spotify credentials from environment
        self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.spotify_token = None

        logger.info("SearchTools initialized with real API integrations")

    def search_youtube_videos(
        self,
        location: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for real YouTube videos about a location using youtubesearchpython.

        Args:
            location: Location name or address
            max_results: Maximum number of results

        Returns:
            List of video dictionaries with title, url, description, duration, etc.
        """
        logger.info(f"Searching YouTube for: {location} (max_results={max_results})")

        # Check cache first
        cache_key = f"youtube_{location}_{max_results}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"Returning {len(cached)} cached YouTube results for: {location}")
            return cached

        try:
            import yt_dlp

            # Build search query
            query = f"ytsearch{max_results}:{location} travel guide documentary"
            logger.debug(f"YouTube search query: {query}")

            # yt-dlp options for search
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'force_generic_extractor': False,
            }

            # Search YouTube
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(query, download=False)

            # Convert to our format
            results = []
            if search_results and 'entries' in search_results:
                logger.debug(f"Raw YouTube entries found: {len(search_results['entries'])}")
                for idx, video in enumerate(search_results['entries'][:max_results]):
                    if video:
                        result = {
                            "title": video.get('title', 'Untitled'),
                            "url": f"https://youtube.com/watch?v={video.get('id', '')}",
                            "description": video.get('description', '')[:200] if video.get('description') else '',
                            "duration": self._format_duration_seconds(video.get('duration', 0)),
                            "views": self._format_views(video.get('view_count', 0)),
                            "channel": video.get('uploader', 'Unknown')
                        }
                        results.append(result)
                        logger.debug(f"  Video {idx+1}: {result['title'][:50]}...")
            else:
                logger.warning(f"No entries in YouTube search results for: {location}")

            logger.info(f"Successfully found {len(results)} YouTube videos for: {location}")

            # Cache results if we have any
            if results:
                self.cache.set(cache_key, results)
            else:
                logger.warning(f"No YouTube results to cache for: {location}")

            return results

        except ImportError:
            logger.warning("yt-dlp not installed, falling back to mock data")
            return self._mock_youtube_videos(location, max_results)

        except Exception as e:
            logger.error(f"YouTube search failed for '{location}': {type(e).__name__}: {e}")
            logger.debug("YouTube search exception details:", exc_info=True)
            return self._mock_youtube_videos(location, max_results)

    def search_music(
        self,
        location: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for music/songs related to a location.
        Tries Spotify first (if credentials available), then YouTube Music fallback.

        Args:
            location: Location name or address
            max_results: Maximum number of results

        Returns:
            List of song dictionaries with title, artist, url, etc.
        """
        logger.info(f"Searching music for: {location} (max_results={max_results})")

        # Check cache first
        cache_key = f"music_{location}_{max_results}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"Returning {len(cached)} cached music results for: {location}")
            return cached

        # Try Spotify if credentials are available
        if self.spotify_client_id and self.spotify_client_secret:
            logger.debug("Attempting Spotify search (credentials available)")
            results = self._search_spotify(location, max_results)
            if results:
                logger.info(f"Found {len(results)} results via Spotify")
                self.cache.set(cache_key, results)
                return results
            else:
                logger.debug("Spotify search returned no results, falling back to YouTube Music")
        else:
            logger.debug("No Spotify credentials, using YouTube Music")

        # Fallback to YouTube Music search
        results = self._search_youtube_music(location, max_results)

        # Cache results if we have any
        if results:
            self.cache.set(cache_key, results)
        else:
            logger.warning(f"No music results to cache for: {location}")

        return results

    def _search_spotify(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Spotify for songs about a location."""
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials

            # Authenticate
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.spotify_client_id,
                client_secret=self.spotify_client_secret
            )
            sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

            # Search for tracks
            query = f"about {location}"
            results_raw = sp.search(q=query, type='track', limit=max_results)

            # Convert to our format
            results = []
            for track in results_raw['tracks']['items']:
                result = {
                    "title": track['name'],
                    "artist": ", ".join([artist['name'] for artist in track['artists']]),
                    "url": track['external_urls']['spotify'],
                    "duration": self._format_duration_ms(track['duration_ms']),
                    "album": track['album']['name'],
                    "genre": "Spotify",  # Spotify doesn't always return genre in search
                    "source": "Spotify"
                }
                results.append(result)

            logger.info(f"Found {len(results)} Spotify tracks for: {location}")
            return results

        except ImportError:
            logger.warning("spotipy not installed, skipping Spotify search")
            return []

        except Exception as e:
            logger.warning(f"Spotify search failed: {e}")
            return []

    def _search_youtube_music(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Search YouTube for music about a location (fallback)."""
        try:
            import yt_dlp

            # Build music-specific search query
            query = f"ytsearch{max_results}:songs about {location} music"
            logger.debug(f"YouTube Music search query: {query}")

            # yt-dlp options for search
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'force_generic_extractor': False,
            }

            # Search YouTube
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(query, download=False)

            # Convert to our format
            results = []
            if search_results and 'entries' in search_results:
                logger.debug(f"Raw YouTube Music entries found: {len(search_results['entries'])}")
                for idx, video in enumerate(search_results['entries'][:max_results]):
                    if video:
                        result = {
                            "title": video.get('title', 'Untitled'),
                            "artist": video.get('uploader', 'Unknown'),
                            "url": f"https://youtube.com/watch?v={video.get('id', '')}",
                            "duration": self._format_duration_seconds(video.get('duration', 0)),
                            "album": "YouTube Music",
                            "genre": "Various",
                            "source": "YouTube"
                        }
                        results.append(result)
                        logger.debug(f"  Song {idx+1}: {result['title'][:50]}...")
            else:
                logger.warning(f"No entries in YouTube Music search results for: {location}")

            logger.info(f"Successfully found {len(results)} YouTube music results for: {location}")
            return results

        except ImportError:
            logger.warning("yt-dlp not installed, falling back to mock data")
            return self._mock_music(location, max_results)

        except Exception as e:
            logger.error(f"YouTube music search failed for '{location}': {type(e).__name__}: {e}")
            logger.debug("YouTube music search exception details:", exc_info=True)
            return self._mock_music(location, max_results)

    def search_historical_stories(
        self,
        location: str,
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for real historical stories and facts using Wikipedia API.

        Args:
            location: Location name or address
            max_results: Maximum number of results

        Returns:
            List of story dictionaries with title, content, source, url
        """
        logger.info(f"Searching historical stories for: {location} (max_results={max_results})")

        # Check cache first
        cache_key = f"history_{location}_{max_results}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"Returning {len(cached)} cached historical results for: {location}")
            return cached

        try:
            import wikipediaapi

            # Initialize Wikipedia API
            wiki = wikipediaapi.Wikipedia(
                language='en',
                user_agent='RouteStories/1.0 (https://github.com/your-repo)'
            )

            # Search for the location page
            logger.debug(f"Querying Wikipedia for page: {location}")
            page = wiki.page(location)

            results = []

            if page.exists():
                logger.debug(f"Wikipedia page found: {page.title} ({page.fullurl})")

                # Main article
                summary = page.summary[:500] + "..." if len(page.summary) > 500 else page.summary

                results.append({
                    "title": f"About {location}",
                    "content": summary,
                    "source": "Wikipedia",
                    "url": page.fullurl,
                    "period": "Historical",
                    "category": "Overview"
                })
                logger.debug(f"  Added main article: About {location}")

                # Get sections for more details
                sections = list(page.sections)[:max_results - 1]
                logger.debug(f"  Total sections available: {len(list(page.sections))}")

                for idx, section in enumerate(sections):
                    if section.text and len(section.text.strip()) > 100:
                        content = section.text[:400] + "..." if len(section.text) > 400 else section.text

                        results.append({
                            "title": section.title,
                            "content": content,
                            "source": "Wikipedia",
                            "url": page.fullurl + "#" + section.title.replace(" ", "_"),
                            "period": "Historical",
                            "category": section.title
                        })
                        logger.debug(f"  Added section: {section.title}")

                        if len(results) >= max_results:
                            break

            else:
                # If exact page doesn't exist, try web search fallback
                logger.warning(f"Wikipedia page not found for: {location}, trying web search fallback")
                results = self._search_web_historical(location, max_results)

            logger.info(f"Successfully found {len(results)} historical stories for: {location}")

            # Cache results if we have any
            if results:
                self.cache.set(cache_key, results)
            else:
                logger.warning(f"No historical results to cache for: {location}")

            return results[:max_results]

        except ImportError:
            logger.warning("wikipediaapi not installed, falling back to web search")
            return self._search_web_historical(location, max_results)

        except Exception as e:
            logger.error(f"Wikipedia search failed for '{location}': {type(e).__name__}: {e}")
            logger.debug("Wikipedia search exception details:", exc_info=True)
            return self._search_web_historical(location, max_results)

    def _search_web_historical(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Search web for historical information using DuckDuckGo (fallback)."""
        try:
            from duckduckgo_search import DDGS

            # Search for historical information
            query = f"{location} history historical facts"
            logger.debug(f"DuckDuckGo search query: {query}")

            with DDGS() as ddgs:
                results_raw = list(ddgs.text(query, max_results=max_results))

            # Convert to our format
            results = []
            logger.debug(f"Raw DuckDuckGo results found: {len(results_raw)}")
            for idx, item in enumerate(results_raw):
                result = {
                    "title": item.get('title', 'Untitled'),
                    "content": item.get('body', ''),
                    "source": "Web Search",
                    "url": item.get('href', ''),
                    "period": "Various",
                    "category": "Historical Information"
                }
                results.append(result)
                logger.debug(f"  Result {idx+1}: {result['title'][:50]}...")

            logger.info(f"Successfully found {len(results)} web search results for: {location}")
            return results

        except ImportError:
            logger.warning("duckduckgo-search not installed, falling back to mock data")
            return self._mock_historical_stories(location, max_results)

        except Exception as e:
            logger.error(f"Web search failed for '{location}': {type(e).__name__}: {e}")
            logger.debug("Web search exception details:", exc_info=True)
            return self._mock_historical_stories(location, max_results)

    # Mock data fallbacks (if all APIs fail)

    def _mock_youtube_videos(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback mock YouTube data."""
        logger.info(f"Using mock YouTube data for: {location}")

        results = [
            {
                "title": f"Exploring {location} - Travel Guide",
                "url": f"https://youtube.com/watch?v=mock_video_1",
                "description": f"A comprehensive travel guide to {location}, showcasing the best attractions and hidden gems.",
                "duration": "10:24",
                "views": "125K",
                "channel": "Travel Explorer"
            },
            {
                "title": f"{location} in 4K - Drone Footage",
                "url": f"https://youtube.com/watch?v=mock_video_2",
                "description": f"Breathtaking aerial views of {location} captured in stunning 4K quality.",
                "duration": "5:18",
                "views": "89K",
                "channel": "Aerial World"
            },
            {
                "title": f"History of {location} - Documentary",
                "url": f"https://youtube.com/watch?v=mock_video_3",
                "description": f"Discover the rich history and cultural significance of {location}.",
                "duration": "22:45",
                "views": "203K",
                "channel": "History Channel"
            }
        ]

        return results[:max_results]

    def _mock_music(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback mock music data."""
        logger.info(f"Using mock music data for: {location}")

        results = [
            {
                "title": f"Streets of {location}",
                "artist": "Local Artists Collective",
                "url": f"https://spotify.com/track/mock_song_1",
                "duration": "3:45",
                "genre": "Folk",
                "album": f"Sounds of {location}",
                "source": "Mock"
            },
            {
                "title": f"{location} Nights",
                "artist": "The Wanderers",
                "url": f"https://spotify.com/track/mock_song_2",
                "duration": "4:12",
                "genre": "Indie Rock",
                "album": "City Stories",
                "source": "Mock"
            },
            {
                "title": f"Memories of {location}",
                "artist": "Traditional Ensemble",
                "url": f"https://spotify.com/track/mock_song_3",
                "duration": "5:30",
                "genre": "Traditional",
                "album": "Heritage Collection",
                "source": "Mock"
            }
        ]

        return results[:max_results]

    def _mock_historical_stories(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback mock historical data."""
        logger.info(f"Using mock historical data for: {location}")

        results = [
            {
                "title": f"The Founding of {location}",
                "content": f"{location} was established in the early centuries and has a rich history of cultural development. The area was known for its strategic importance and vibrant marketplace.",
                "source": "Historical Archives",
                "url": f"https://wikipedia.org/wiki/{quote(location)}",
                "period": "Historical",
                "category": "Founding Story"
            },
            {
                "title": f"Famous Figures from {location}",
                "content": f"Many notable personalities have connections to {location}, including artists, scientists, and political leaders who shaped the region's identity.",
                "source": "Biography Database",
                "url": f"https://history.com/places/{quote(location)}",
                "period": "Various",
                "category": "People"
            },
            {
                "title": f"Architectural Heritage of {location}",
                "content": f"The architectural landscape of {location} reflects centuries of cultural influences, from ancient structures to modern landmarks.",
                "source": "Architecture Journal",
                "url": f"https://architecture.org/places/{quote(location)}",
                "period": "Multi-era",
                "category": "Architecture"
            }
        ]

        return results[:max_results]

    # Utility methods

    def _format_duration_ms(self, duration_ms: int) -> str:
        """Convert milliseconds to MM:SS format."""
        seconds = duration_ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def _format_duration_seconds(self, duration_seconds) -> str:
        """Convert seconds to MM:SS format."""
        if not duration_seconds:
            return "Unknown"
        # Convert to int if it's a float
        duration_seconds = int(duration_seconds)
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def _format_views(self, view_count: int) -> str:
        """Format view count to human-readable format."""
        if not view_count:
            return "N/A"
        if view_count >= 1000000:
            return f"{view_count / 1000000:.1f}M"
        elif view_count >= 1000:
            return f"{view_count / 1000:.0f}K"
        return str(view_count)

    def fetch_url_content(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL.

        Args:
            url: URL to fetch

        Returns:
            Content text or None if fetch fails
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def enhance_search_query(self, location: str, content_type: str) -> str:
        """
        Build an enhanced search query for a specific content type.

        Args:
            location: Location name
            content_type: Type of content (video, music, story)

        Returns:
            Enhanced search query string
        """
        queries = {
            "video": f"{location} travel guide tour documentary walking",
            "music": f"songs about {location} music soundtrack theme",
            "story": f"{location} history historical facts interesting stories"
        }

        return queries.get(content_type, location)
