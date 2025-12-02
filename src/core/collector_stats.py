"""
Statistics calculation for Collector.
"""

from typing import List, Dict, Any


def calculate_statistics(summaries: List) -> Dict[str, Any]:
    """
    Calculate statistics for the route.

    Args:
        summaries: List of WaypointSummary objects

    Returns:
        Dictionary with statistics
    """
    total = len(summaries)

    if total == 0:
        return {}

    chosen_counts = {'video': 0, 'song': 0, 'story': 0, 'error': 0}
    total_score = 0
    error_count = 0

    for summary in summaries:
        if summary.chosen_type:
            chosen_counts[summary.chosen_type] = chosen_counts.get(summary.chosen_type, 0) + 1
        else:
            chosen_counts['error'] += 1

        if summary.judge_score:
            total_score += summary.judge_score

        if summary.errors:
            error_count += len(summary.errors)

    return {
        'total_waypoints': total,
        'content_type_distribution': chosen_counts,
        'average_judge_score': total_score / total if total > 0 else 0,
        'total_errors': error_count
    }
