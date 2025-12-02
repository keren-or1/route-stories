"""
Video filtering and scoring utilities.
Filters and scores videos for relevance and quality.
"""

from typing import List, Tuple, Dict, Any


def filter_and_score_videos(location: str, videos: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], int]]:
    """
    Filter out low-quality videos and score remaining ones by relevance.

    Args:
        location: Location name
        videos: List of video dictionaries

    Returns:
        List of (video, score) tuples, filtered and scored
    """
    scored_videos = []
    location_lower = location.lower()

    for video in videos:
        # Extract metadata
        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        views = video.get('views', 0) or 0
        duration = video.get('duration', '')

        # Initialize score
        score = 50  # Base score

        # Location relevance (most important)
        if location_lower in title:
            score += 25
        elif location_lower in description:
            score += 15

        # View count quality indicator
        if isinstance(views, int):
            if views > 1000000:
                score += 15
            elif views > 100000:
                score += 10
            elif views > 10000:
                score += 5

        # Duration preference (5-20 minutes is good for travel content)
        if duration:
            try:
                if ':' in str(duration):
                    parts = str(duration).split(':')
                    if len(parts) == 2:
                        mins = int(parts[0])
                        if 5 <= mins <= 20:
                            score += 10
                        elif 3 <= mins <= 25:
                            score += 5
            except:
                pass

        # Channel reputation (prefer larger channels)
        channel = video.get('channel', '').lower()
        if 'official' in channel or 'verified' in channel or video.get('channel_verified', False):
            score += 10

        # Recency bonus (prefer recent content)
        upload_date = video.get('upload_date', '')
        if upload_date and '2024' in str(upload_date):
            score += 5

        # Minimum quality filter
        if score >= 40:
            scored_videos.append((video, score))

    return scored_videos
