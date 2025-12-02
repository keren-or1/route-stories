"""Music search functionality using Spotify and YouTube Music."""

import os
from typing import List, Dict, Any
from src.utils.logger import get_logger
from src.services.music_search_utils import get_mock_music
from src.services.spotify_search import SpotifyAuth, search_spotify_tracks

logger = get_logger("music_search")


class MusicSearch:
    """Music search using Spotify (primary) and YouTube Music (fallback)."""

    def __init__(self, cache):
        """Initialize music search with cache and Spotify credentials."""
        self.cache = cache
        self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.spotify_token = None

    def search_music(self, location: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for music/songs related to a location.
        Tries Spotify first (if credentials available), then YouTube Music fallback.
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
            logger.debug("Attempting Spotify search")
            results = self._search_spotify(location, max_results)
            if results:
                logger.info(f"Found {len(results)} results via Spotify")
                self.cache.set(cache_key, results)
                return results
            logger.debug("Spotify search returned no results, falling back to YouTube Music")
        else:
            logger.debug("No Spotify credentials, using YouTube Music")

        # Fallback to YouTube Music
        results = self._search_youtube_music(location, max_results)
        if results:
            self.cache.set(cache_key, results)
        return results

    def _search_spotify(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Spotify for songs about a location."""
        try:
            token = SpotifyAuth.get_token(self.spotify_client_id, self.spotify_client_secret)
            if not token:
                return []
            query = f"about {location}"
            return search_spotify_tracks(query, token, max_results)
        except Exception as e:
            logger.warning(f"Spotify search failed: {e}")
            return []

    def _search_youtube_music(self, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Search YouTube for music about a location (fallback)."""
        try:
            import yt_dlp
            query = f"ytsearch{max_results}:songs about {location} music"
            logger.debug(f"YouTube Music search query: {query}")

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'force_generic_extractor': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(query, download=False)

            results = []
            if search_results and 'entries' in search_results:
                for idx, video in enumerate(search_results['entries'][:max_results]):
                    if video:
                        result = {
                            "title": video.get('title', 'Untitled'),
                            "artist": video.get('uploader', 'Unknown'),
                            "url": f"https://youtube.com/watch?v={video.get('id', '')}",
                            "duration": str(video.get('duration', 0)),
                            "album": "YouTube Music",
                            "genre": "Various",
                            "source": "YouTube"
                        }
                        results.append(result)

            logger.info(f"Found {len(results)} YouTube music results for: {location}")
            return results

        except ImportError:
            logger.warning("yt-dlp not installed, using mock data")
            return get_mock_music(location, max_results)
        except Exception as e:
            logger.error(f"YouTube music search failed: {e}")
            return get_mock_music(location, max_results)
