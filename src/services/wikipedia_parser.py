"""Wikipedia content parsing and formatting."""

from typing import Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger("wikipedia_parser")


def parse_wikipedia_content(summary: str, title: str, url: str) -> Dict[str, Any]:
    """Parse and format Wikipedia content into standard format."""
    # Truncate long summaries
    content = summary[:500] + "..." if len(summary) > 500 else summary

    return {
        "title": title,
        "content": content,
        "source": "Wikipedia",
        "url": url,
        "period": "Historical"
    }


def extract_location_context(location: str) -> str:
    """Extract relevant context from location for Wikipedia search."""
    # Remove common suffixes
    for suffix in [", USA", ", Canada", ", UK", " City", " County", " State"]:
        if location.endswith(suffix):
            return location[:-len(suffix)]
    return location
