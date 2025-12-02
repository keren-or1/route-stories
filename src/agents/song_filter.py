"""
Song filtering and scoring utilities.
Filters and scores songs for relevance and quality.
"""

from typing import List, Tuple, Dict, Any


def filter_and_score_songs(location: str, songs: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], int]]:
    """
    Filter out low-quality songs and score remaining ones by relevance.

    Args:
        location: Location name
        songs: List of song dictionaries

    Returns:
        List of (song, score) tuples, filtered and scored
    """
    scored_songs = []
    location_lower = location.lower()

    for song in songs:
        # Extract metadata
        title = song.get('title', '').lower()
        artist = song.get('artist', '').lower()
        genre = song.get('genre', '').lower()
        album = song.get('album', '').lower()

        # Initialize score
        score = 50  # Base score

        # Location/place relevance (highest priority)
        if location_lower in title:
            score += 25
        elif location_lower in artist:
            score += 10
        elif location_lower in album:
            score += 15

        # Genre appropriateness for travel
        travel_friendly_genres = ['pop', 'indie', 'world', 'folk', 'acoustic',
                                   'alternative', 'rock']
        for friendly_genre in travel_friendly_genres:
            if friendly_genre in genre:
                score += 8
                break

        # Avoid overly niche or heavy genres
        heavy_genres = ['death', 'thrash', 'black metal', 'harsh', 'extreme']
        for heavy_genre in heavy_genres:
            if heavy_genre in genre:
                score -= 20

        # Production quality indicators
        if 'official' in title.lower() or 'official' in artist.lower():
            score += 5

        # Duration preference (3-5 minutes is ideal)
        duration = song.get('duration', '')
        if duration:
            try:
                if ':' in str(duration):
                    parts = str(duration).split(':')
                    if len(parts) == 2:
                        mins = int(parts[0])
                        if 3 <= mins <= 5:
                            score += 10
                        elif 2 <= mins <= 7:
                            score += 5
            except:
                pass

        # Recency bonus for contemporary music
        year = song.get('year')
        if year:
            try:
                year_int = int(year)
                if 2020 <= year_int <= 2024:
                    score += 5
            except:
                pass

        # Minimum quality filter
        if score >= 40:
            scored_songs.append((song, score))

    return scored_songs
