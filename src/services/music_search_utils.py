"""
Utility functions for music search formatting and mock data.
"""

from typing import List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger("music_search_utils")


def format_duration_ms(duration_ms: int) -> str:
    """Convert milliseconds to MM:SS format."""
    seconds = duration_ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"


def format_duration_seconds(duration_seconds) -> str:
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


def get_mock_music(location: str, max_results: int) -> List[Dict[str, Any]]:
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
