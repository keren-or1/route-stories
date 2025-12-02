"""
Utility functions for Wikipedia/historical search mock data.
"""

from typing import List, Dict, Any
from urllib.parse import quote
from src.utils.logger import get_logger

logger = get_logger("wikipedia_search_utils")


def get_mock_historical_stories(location: str, max_results: int) -> List[Dict[str, Any]]:
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
