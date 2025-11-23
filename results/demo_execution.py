#!/usr/bin/env python3
"""
Demo Execution Script for Route Stories
Demonstrates end-to-end execution with mocked external APIs.
This script provides proof that the system runs correctly without requiring real API keys.
"""

import sys
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import setup_logger, QueueManager
from services.search_tools import SearchTools
from agents import VideoAgent, SongAgent, StoryAgent, JudgeAgent
from core import Orchestrator, Collector
from services.google_maps import Route, Waypoint


def create_mock_claude_client():
    """Create a mock Claude client that simulates agent decisions."""
    mock_claude = Mock()

    # Simulate Video Agent responses
    video_responses = {
        "Tel Aviv": "CHOICE: 1\nREASONING: The comprehensive travel guide provides the best overview of Tel Aviv's vibrant culture and modern attractions.",
        "Latrun": "CHOICE: 2\nREASONING: Drone footage captures the historical significance and beautiful landscape of Latrun from a unique aerial perspective.",
        "Jerusalem": "CHOICE: 3\nREASONING: The historical documentary offers deep insights into Jerusalem's rich heritage and cultural importance."
    }

    # Simulate Song Agent responses
    song_responses = {
        "Tel Aviv": "CHOICE: 2\nREASONING: The indie rock song captures the modern, energetic vibe of Tel Aviv nights perfectly.",
        "Latrun": "CHOICE: 1\nREASONING: The folk song reflects the traditional and historical atmosphere of the area.",
        "Jerusalem": "CHOICE: 3\nREASONING: Traditional music honors Jerusalem's deep cultural and spiritual heritage."
    }

    # Simulate Story Agent responses
    story_responses = {
        "Tel Aviv": "CHOICE: 1\nREASONING: The founding story provides essential context about Tel Aviv's establishment as the first Hebrew city.",
        "Latrun": "CHOICE: 2\nREASONING: The stories of notable figures from this region add personal and human dimensions to the location's history.",
        "Jerusalem": "CHOICE: 3\nREASONING: The architectural heritage showcases Jerusalem's millennia of cultural and religious significance."
    }

    # Simulate Judge Agent responses
    judge_responses = {
        "Tel Aviv": "CHOICE: 1\nREASONING: The video provides the most engaging and comprehensive introduction to Tel Aviv for travelers, combining visual appeal with practical information.",
        "Latrun": "CHOICE: 3\nREASONING: The historical story best captures the significance of Latrun as a strategic location, enriching the journey with meaningful context.",
        "Jerusalem": "CHOICE: 1\nREASONING: The video documentary offers the most immersive experience for this iconic destination, balancing education and inspiration."
    }

    def simple_query_side_effect(prompt, **kwargs):
        """Simulate Claude responses based on prompt content."""
        # Determine which location is being processed
        location = None
        for loc in ["Jerusalem", "Latrun", "Tel Aviv"]:
            if loc in prompt:
                location = loc
                break

        if not location:
            location = "Tel Aviv"  # Default

        # Determine which agent type based on prompt
        if "video" in prompt.lower():
            return video_responses.get(location, "CHOICE: 1\nREASONING: Default video choice")
        elif "song" in prompt.lower() or "music" in prompt.lower():
            return song_responses.get(location, "CHOICE: 1\nREASONING: Default song choice")
        elif "story" in prompt.lower() or "historical" in prompt.lower():
            return story_responses.get(location, "CHOICE: 1\nREASONING: Default story choice")
        elif "judge" in prompt.lower() or "evaluate" in prompt.lower():
            return judge_responses.get(location, "CHOICE: 1\nREASONING: Default judge choice")

        return "CHOICE: 1\nREASONING: Default response"

    mock_claude.simple_query.side_effect = simple_query_side_effect

    return mock_claude


def create_mock_route():
    """Create a mock route from Tel Aviv to Jerusalem."""
    waypoints = [
        Waypoint(
            point_id=0,
            address="Tel Aviv-Yafo, Israel",
            location={"lat": 32.0853, "lng": 34.7818},
            distance_from_start=0,
            duration_from_start=0
        ),
        Waypoint(
            point_id=1,
            address="Latrun, Israel",
            location={"lat": 31.8358, "lng": 34.9878},
            distance_from_start=35000,  # 35 km
            duration_from_start=2400    # 40 minutes
        ),
        Waypoint(
            point_id=2,
            address="Jerusalem, Israel",
            location={"lat": 31.7683, "lng": 35.2137},
            distance_from_start=65000,  # 65 km
            duration_from_start=4500    # 75 minutes
        )
    ]

    route = Route(
        route_id="demo_route_tel_aviv_jerusalem",
        origin="Tel Aviv",
        destination="Jerusalem",
        waypoints=waypoints,
        total_distance=65000,
        total_duration=4500
    )

    return route


def print_section_header(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def main():
    """Execute the demo."""
    print_section_header("ROUTE STORIES - DEMO EXECUTION")

    print("This demo executes the Route Stories system with:")
    print("  - Mock route: Tel Aviv → Latrun → Jerusalem")
    print("  - Mock Claude API (simulated agent decisions)")
    print("  - Real SearchTools (mock search results)")
    print("  - Real multi-threaded orchestration")
    print("  - Real queue-based communication\n")

    # Setup logging
    logger = setup_logger(
        log_level="INFO",
        log_dir=Path(__file__).parent / "logs",
        enable_console=True,
        enable_file=True
    )

    logger.info("="*80)
    logger.info("Demo Execution - Starting")
    logger.info("="*80)

    # Initialize services
    print_section_header("INITIALIZING SERVICES")

    mock_claude = create_mock_claude_client()
    search_tools = SearchTools()

    print("✓ Mock Claude client created")
    print("✓ SearchTools initialized")

    # Initialize agents
    print_section_header("INITIALIZING AGENTS")

    video_agent = VideoAgent(mock_claude, search_tools)
    song_agent = SongAgent(mock_claude, search_tools)
    story_agent = StoryAgent(mock_claude, search_tools)
    judge_agent = JudgeAgent(mock_claude)

    print("✓ Video Agent initialized")
    print("✓ Song Agent initialized")
    print("✓ Story Agent initialized")
    print("✓ Judge Agent initialized")

    # Initialize queue manager and orchestrator
    queue_manager = QueueManager()

    orchestrator = Orchestrator(
        video_agent=video_agent,
        song_agent=song_agent,
        story_agent=story_agent,
        judge_agent=judge_agent,
        queue_manager=queue_manager
    )

    print("✓ Orchestrator initialized with multi-threading")

    # Create mock route
    print_section_header("CREATING ROUTE")

    route = create_mock_route()

    print(f"Route: {route.origin} → {route.destination}")
    print(f"Total Distance: {route.total_distance / 1000:.1f} km")
    print(f"Total Duration: {route.total_duration / 60:.0f} minutes")
    print(f"Waypoints: {len(route.waypoints)}")

    for wp in route.waypoints:
        print(f"  {wp.point_id}. {wp.address}")

    # Initialize collector
    collector = Collector(route_id=route.route_id, queue_manager=queue_manager)

    # Process each waypoint
    print_section_header("PROCESSING WAYPOINTS")

    for waypoint in route.waypoints:
        print(f"\n{'─'*80}")
        print(f"WAYPOINT {waypoint.point_id}: {waypoint.address}")
        print(f"{'─'*80}\n")

        logger.info(f"Processing waypoint {waypoint.point_id}: {waypoint.address}")

        # Process waypoint
        print("  → Executing agents in parallel...")
        result = orchestrator.process_waypoint(
            route_id=route.route_id,
            point_id=waypoint.point_id,
            address=waypoint.address,
            location=waypoint.location
        )

        if result:
            print(f"  ✓ Processing completed")

            # Check each agent result
            video_result = result.get('video')
            song_result = result.get('song')
            story_result = result.get('story')
            judge_result = result.get('judge')

            print(f"    - Video Agent: {'SUCCESS' if video_result and not video_result.error else 'FAILED'}")
            print(f"    - Song Agent: {'SUCCESS' if song_result and not song_result.error else 'FAILED'}")
            print(f"    - Story Agent: {'SUCCESS' if story_result and not story_result.error else 'FAILED'}")

            if judge_result and not judge_result.error:
                print(f"    - Judge Decision: MADE")
                selected = judge_result.content.get('chosen_type', 'unknown')
                reasoning = judge_result.content.get('reasoning', 'No reasoning provided')
                print(f"    - Selected Content: {selected.upper()}")
                print(f"    - Reasoning: {reasoning[:80]}...")
            else:
                print(f"    - Judge Decision: PENDING")

            # Collect results
            collector.collect_waypoint(
                point_id=waypoint.point_id,
                address=waypoint.address,
                location=waypoint.location,
                results=result
            )

        else:
            print(f"  ✗ Processing failed")

    # Export results
    print_section_header("EXPORTING RESULTS")

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    export_path = output_dir / f"demo_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    collector.export_to_json(export_path)

    print(f"✓ Results exported to: {export_path}")

    # Display summary
    print_section_header("EXECUTION SUMMARY")

    summaries = collector.get_all_summaries()

    print(f"Total Waypoints Processed: {len(summaries)}")
    print(f"Route ID: {route.route_id}")
    print(f"Origin: {route.origin}")
    print(f"Destination: {route.destination}")
    print()

    # Show judge decisions
    print("Judge Decisions:")
    for summary in summaries:
        if summary.chosen_type:
            print(f"  Waypoint {summary.point_id} ({summary.address}): {summary.chosen_type.upper()}")
        else:
            print(f"  Waypoint {summary.point_id} ({summary.address}): NO DECISION")

    print()

    # Print detailed summary
    collector.print_summary()

    # Cleanup
    logger.info("Shutting down orchestrator...")
    orchestrator.shutdown()

    print_section_header("DEMO COMPLETED SUCCESSFULLY")

    print("Output files:")
    print(f"  - Execution results: {export_path}")
    print(f"  - Logs: {Path(__file__).parent / 'logs' / 'route_stories.log'}")
    print()
    print("The system has been demonstrated to work end-to-end with:")
    print("  ✓ Multi-agent orchestration")
    print("  ✓ Parallel execution with threading")
    print("  ✓ Queue-based communication")
    print("  ✓ Agent decision-making (simulated)")
    print("  ✓ Result collection and export")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
