"""
Printing utilities for Collector summaries.
"""

from typing import List, Dict, Any
from src.core.collector_models import WaypointSummary


def print_waypoint_summary(summary: WaypointSummary) -> None:
    """Print a single waypoint summary."""
    print(f"\nWaypoint {summary.point_id}: {summary.address}")
    print("-" * 80)

    if summary.chosen_type and summary.chosen_content:
        content = summary.chosen_content
        print(f"SELECTED: {summary.chosen_type.upper()}")

        if summary.chosen_type == 'video':
            _print_video_content(content)
        elif summary.chosen_type == 'song':
            _print_song_content(content)
        elif summary.chosen_type == 'story':
            _print_story_content(content)

        if summary.judge_reasoning:
            print(f"\nJudge's Reasoning: {summary.judge_reasoning}")
        if summary.judge_score:
            print(f"Confidence Score: {summary.judge_score}/100")

    if summary.errors:
        print("\nERRORS:")
        for error in summary.errors:
            print(f"  - {error}")


def _print_video_content(content: Dict[str, Any]) -> None:
    """Print video content details."""
    print(f"  Title: {content.get('title', 'N/A')}")
    print(f"  Channel: {content.get('channel', 'N/A')}")
    print(f"  Duration: {content.get('duration', 'N/A')}")
    print(f"  URL: {content.get('url', 'N/A')}")


def _print_song_content(content: Dict[str, Any]) -> None:
    """Print song content details."""
    print(f"  Title: {content.get('title', 'N/A')}")
    print(f"  Artist: {content.get('artist', 'N/A')}")
    print(f"  Genre: {content.get('genre', 'N/A')}")
    print(f"  URL: {content.get('url', 'N/A')}")


def _print_story_content(content: Dict[str, Any]) -> None:
    """Print story content details."""
    print(f"  Title: {content.get('title', 'N/A')}")
    print(f"  Content: {content.get('content', 'N/A')[:200]}...")
    print(f"  Source: {content.get('source', 'N/A')}")


def print_statistics(stats: Dict[str, Any]) -> None:
    """Print route statistics."""
    print("\n" + "="*80)
    print("STATISTICS")
    print("="*80)
    print(f"Total Waypoints: {stats.get('total_waypoints', 0)}")
    print(f"Content Distribution: {stats.get('content_type_distribution', {})}")
    print(f"Average Judge Score: {stats.get('average_judge_score', 0):.1f}/100")
    print(f"Total Errors: {stats.get('total_errors', 0)}")
    print("="*80 + "\n")


def print_full_summary(
    route_id: str,
    summaries: List[WaypointSummary],
    stats: Dict[str, Any]
) -> None:
    """Print complete route summary."""
    print("\n" + "="*80)
    print(f"ROUTE SUMMARY - {route_id}")
    print("="*80)

    for summary in summaries:
        print_waypoint_summary(summary)

    print_statistics(stats)
