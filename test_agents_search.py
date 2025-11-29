#!/usr/bin/env python3
"""
Test script to verify agents can find search results with retry logic.
"""

import sys
import os
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.video_agent import VideoAgent
from src.agents.song_agent import SongAgent
from src.agents.story_agent import StoryAgent
from src.agents.base_agent import AgentTask
from src.services.gemini_client import GeminiClient
from src.services.search_tools import SearchTools
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("test_agents_search")

def test_agent_search(agent_class, agent_name, waypoint):
    """Test a single agent's ability to find search results."""
    print(f"\n{'='*60}")
    print(f"Testing {agent_name} Agent")
    print(f"Waypoint: {waypoint}")
    print(f"{'='*60}")

    try:
        settings = get_settings()
        gemini_client = GeminiClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            max_tokens=settings.gemini_max_tokens,
            temperature=settings.gemini_temperature,
            retry_delay=1.0,
            max_retries=3
        )

        search_tools = SearchTools()
        agent = agent_class(gemini_client=gemini_client, search_tools=search_tools)

        # Create AgentTask for the agent
        task = AgentTask(
            route_id="test_route",
            point_id=1,
            address=waypoint,
            location={"lat": 0, "lng": 0}
        )

        # Execute the agent
        print(f"\nSearching for {agent_name.lower()} content...")
        result = agent.execute(task=task)

        print(f"\n✓ {agent_name} Agent Result:")
        # Result is an AgentResult dataclass
        has_error = result.error is not None
        result_dict = {
            "agent_type": result.agent_type,
            "route_id": result.route_id,
            "point_id": result.point_id,
            "has_content": bool(result.content),
            "content_keys": list(result.content.keys()) if result.content else [],
            "error": result.error
        }
        print(json.dumps(result_dict, indent=2, ensure_ascii=False))

        # Check if results were found
        if not has_error and result.content:
            print(f"\n✓ SUCCESS: {agent_name} found content")
            print(f"  - Content type: {type(result.content)}")
            print(f"  - Content keys: {list(result.content.keys())}")
            return True
        else:
            print(f"\n✗ ISSUE: {agent_name} returned error or empty result")
            if has_error:
                print(f"  - Error: {result.error}")
            else:
                print(f"  - Empty content: {result.content}")
            return False

    except Exception as e:
        logger.error(f"{agent_name} agent test failed: {e}")
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests for all agents."""
    print("\n" + "="*60)
    print("Agent Search Results Test")
    print("="*60)

    # Test with a specific waypoint
    test_waypoint = "Eiffel Tower, Paris"

    results = {
        "Video Agent": test_agent_search(VideoAgent, "Video", test_waypoint),
        "Song Agent": test_agent_search(SongAgent, "Song", test_waypoint),
        "Story Agent": test_agent_search(StoryAgent, "Story", test_waypoint),
    }

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")

    for agent_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{agent_name}: {status}")

    all_passed = all(results.values())
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    print(f"{'='*60}\n")

    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)
