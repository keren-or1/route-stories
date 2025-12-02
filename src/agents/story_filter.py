"""
Story filtering and scoring utilities.
Filters and scores historical stories for relevance and quality.
"""

from typing import List, Tuple, Dict, Any


def filter_and_score_stories(location: str, stories: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], int]]:
    """
    Filter out low-quality stories and score remaining ones by relevance.

    Args:
        location: Location name
        stories: List of story dictionaries

    Returns:
        List of (story, score) tuples, filtered and scored
    """
    scored_stories = []
    location_lower = location.lower()

    for story in stories:
        # Extract metadata
        title = story.get('title', '').lower()
        content = story.get('content', '').lower()
        source = story.get('source', '').lower()
        period = story.get('period', '')
        category = story.get('category', '').lower()

        # Filter: Reject irrelevant help articles
        if _is_irrelevant_article(content, title, location_lower):
            continue

        # Calculate score
        score = _calculate_story_score(
            location_lower, title, content, source, period, category, story
        )

        # Minimum quality filter
        content_text = story.get('content', '')
        if score >= 40 and len(content_text) >= 50:
            scored_stories.append((story, score))

    return scored_stories


def _is_irrelevant_article(content: str, title: str, location: str) -> bool:
    """Check if article is irrelevant (help pages, tech support, etc.)."""
    # Filter: Reject Google/tech product help articles
    irrelevant_patterns = [
        'how to stop sharing', 'how to turn off', 'how to share',
        'share your real-time location', 'share location',
        'google maps help', 'google support', 'google account help',
        'android settings', 'iphone settings', 'app settings',
        'technical support', 'troubleshoot', 'manage location permissions',
        'manage permissions', 'enable location', 'disable location',
        'location services', 'privacy settings', 'app permissions',
        'turn on location', 'turn off location', 'location sharing',
        'real-time location',
    ]

    if any(pattern in content for pattern in irrelevant_patterns):
        return True

    # Reject help articles by title
    help_title_patterns = ['google', 'how to', 'manage', 'settings', 'permissions',
                           'enable', 'disable', 'turn', 'stop', 'share']

    is_help_title = (
        (all(pattern in title for pattern in ['google', 'help'])) or
        (all(pattern in title for pattern in ['google', 'maps']) and location not in title) or
        (any(pattern in title for pattern in help_title_patterns) and location not in title)
    )

    if is_help_title:
        return True

    # Reject Google product articles without location
    is_about_google = (
        any(kw in content for kw in ['google maps', 'google help', 'app feature',
                                      'phone settings', 'google account']) and
        location not in content[:300]
    )

    return is_about_google


def _calculate_story_score(
    location: str,
    title: str,
    content: str,
    source: str,
    period: str,
    category: str,
    story: Dict[str, Any]
) -> int:
    """Calculate relevance score for a story."""
    score = 50  # Base score

    # Location relevance (highest priority)
    if location in title:
        score += 25
    elif location in content[:200]:
        score += 20

    # Content quality (length indicates depth)
    content_text = story.get('content', '')
    if len(content_text) > 500:
        score += 10
    elif len(content_text) > 200:
        score += 5

    # Category appropriateness
    interesting_categories = ['history', 'culture', 'landmark', 'architecture',
                              'art', 'famous', 'notable']
    for cat in interesting_categories:
        if cat in category:
            score += 8
            break

    # Source credibility
    trusted_sources = ['wikipedia', 'bbc', 'national geographic', 'history',
                       'britannica', 'government']
    for trusted in trusted_sources:
        if trusted in source:
            score += 10
            break

    # Avoid low-quality sources
    poor_sources = ['random', 'unknown', 'unverified']
    for poor in poor_sources:
        if poor in source:
            score -= 15

    # Historical significance markers
    significant_keywords = ['ancient', 'historic', 'founded', 'built',
                            'established', 'famous', 'renowned', 'important']
    for keyword in significant_keywords:
        if keyword in content[:200]:
            score += 3

    # Period boost
    if period and period.lower() in ['ancient', 'medieval', 'renaissance',
                                      'colonial', 'modern']:
        score += 5

    return score
