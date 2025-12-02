"""
Display utilities for CLI output formatting.
"""

from src.services.route_models import Route, Waypoint
from src.core.collector_models import WaypointSummary
from src.ui.content_display import (
    display_video_content,
    display_song_content,
    display_story_content
)


def display_welcome():
    """Display welcome message and instructions."""
    print("\n" + "="*80)
    print(" "*25 + "ROUTE STORIES")
    print(" "*15 + "AI-Powered Journey Content Curator")
    print("="*80)
    print("\nWelcome! This system will find engaging content for each stop")
    print("along your route - videos, songs, and historical stories.\n")


def display_route_info(route: Route):
    """
    Display route information.

    Args:
        route: Route object
    """
    print("\n" + "="*80)
    print("ROUTE INFORMATION")
    print("="*80)
    print(f"From: {route.origin}")
    print(f"To: {route.destination}")
    print(f"Total Distance: {route.total_distance / 1000:.1f} km")
    print(f"Estimated Duration: {route.total_duration / 60:.0f} minutes")
    print(f"Waypoints: {len(route.waypoints)}")
    print("="*80 + "\n")


def display_waypoint_info(waypoint: Waypoint, index: int, total: int):
    """
    Display information about current waypoint.

    Args:
        waypoint: Waypoint object
        index: Current waypoint index (0-based)
        total: Total number of waypoints
    """
    print("\n" + "-"*80)
    print(f"WAYPOINT {index + 1} of {total}")
    print("-"*80)
    print(f"Location: {waypoint.address}")
    print(f"Coordinates: {waypoint.location['lat']:.6f}, {waypoint.location['lng']:.6f}")

    if waypoint.distance_from_start:
        print(f"Distance from start: {waypoint.distance_from_start / 1000:.1f} km")

    print("-"*80)


def display_processing(waypoint: Waypoint):
    """
    Display processing message.

    Args:
        waypoint: Waypoint being processed
    """
    print(f"\nSearching for content about: {waypoint.address}")
    print("This may take a moment...")
    print("\nAgents working:")
    print("  [*] Video Agent - searching YouTube...")
    print("  [*] Song Agent - searching music...")
    print("  [*] Story Agent - searching historical facts...")
    print("  [*] Judge Agent - evaluating options...\n")


def display_waypoint_result(summary: WaypointSummary):
    """
    Display results for a completed waypoint.

    Args:
        summary: Waypoint summary object
    """
    if not summary:
        print("\nError: No results collected for this waypoint\n")
        return

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    if summary.errors:
        print("\nWarnings/Errors:")
        for error in summary.errors:
            print(f"  ⚠ {error}")

    if summary.chosen_type and summary.chosen_content:
        content = summary.chosen_content

        print(f"\n✓ SELECTED CONTENT: {summary.chosen_type.upper()}")
        print("-"*80)

        if summary.chosen_type == 'video':
            display_video_content(content)
        elif summary.chosen_type == 'song':
            display_song_content(content)
        elif summary.chosen_type == 'story':
            display_story_content(content)

        print()

        if summary.judge_reasoning:
            print(f"Judge's Reasoning: {summary.judge_reasoning}")

        if summary.judge_score is not None:
            print(f"Confidence Score: {summary.judge_score}/100")

    else:
        print("\n✗ No content selected (processing failed)")

    print("="*80)


def display_final_summary_header():
    """Display final summary header."""
    print("\n\n" + "="*80)
    print(" "*25 + "JOURNEY COMPLETE")
    print("="*80)


def display_export_info(filepath: str):
    """
    Display information about exported results.

    Args:
        filepath: Path to exported file
    """
    print(f"\nResults exported to: {filepath}")
    print("You can review the complete journey data in this file.\n")
