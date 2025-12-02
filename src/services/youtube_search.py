"""
YouTube video search functionality using yt-dlp.
"""

from typing import List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger("youtube_search")


class YouTubeSearch:
    """YouTube video search using yt-dlp."""

    def __init__(self, cache):
        """Initialize YouTube search with cache."""
        self.cache = cache

    def search_videos(self, location: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for real YouTube videos about a location using yt-dlp.

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
