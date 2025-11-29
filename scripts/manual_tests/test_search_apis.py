#!/usr/bin/env python3
"""
Test script for real search API integrations.
Tests YouTube, Wikipedia, and Music search with actual locations.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.search_tools import SearchTools
from utils.logger import get_logger

logger = get_logger("test_search")


def test_youtube_search():
    """Test real YouTube video search."""
    print("\n" + "="*80)
    print("TESTING YOUTUBE VIDEO SEARCH")
    print("="*80)

    search_tools = SearchTools()

    # Test with a well-known location
    location = "Paris"
    print(f"\nSearching for videos about: {location}")

    results = search_tools.search_youtube_videos(location, max_results=3)

    print(f"\nFound {len(results)} videos:")
    for i, video in enumerate(results, 1):
        print(f"\n{i}. {video['title']}")
        print(f"   URL: {video['url']}")
        print(f"   Channel: {video['channel']}")
        print(f"   Duration: {video['duration']}")
        print(f"   Views: {video['views']}")
        if video['description']:
            print(f"   Description: {video['description'][:100]}...")

    # Verify URLs are real (not mock)
    if results and 'mock_video' not in results[0]['url']:
        print("\n✅ SUCCESS: YouTube search is returning REAL video URLs!")
    else:
        print("\n⚠️  WARNING: YouTube search is using mock data (library may not be installed)")


def test_music_search():
    """Test real music search (Spotify or YouTube Music)."""
    print("\n" + "="*80)
    print("TESTING MUSIC SEARCH")
    print("="*80)

    search_tools = SearchTools()

    # Test with a well-known location (use different location to avoid cache)
    location = "Tokyo"
    print(f"\nSearching for songs about: {location}")

    results = search_tools.search_music(location, max_results=3)

    print(f"\nFound {len(results)} songs:")
    for i, song in enumerate(results, 1):
        print(f"\n{i}. {song['title']}")
        print(f"   Artist: {song['artist']}")
        print(f"   URL: {song['url']}")
        print(f"   Duration: {song['duration']}")
        print(f"   Album: {song['album']}")
        print(f"   Source: {song.get('source', 'Unknown')}")

    # Verify URLs are real (not mock)
    if results and 'mock_song' not in results[0]['url']:
        print("\n✅ SUCCESS: Music search is returning REAL song URLs!")
    else:
        print("\n⚠️  WARNING: Music search is using mock data (libraries may not be installed)")


def test_historical_search():
    """Test real Wikipedia/historical search."""
    print("\n" + "="*80)
    print("TESTING HISTORICAL/WIKIPEDIA SEARCH")
    print("="*80)

    search_tools = SearchTools()

    # Test with a well-known location
    location = "Rome"
    print(f"\nSearching for historical information about: {location}")

    results = search_tools.search_historical_stories(location, max_results=3)

    print(f"\nFound {len(results)} historical stories:")
    for i, story in enumerate(results, 1):
        print(f"\n{i}. {story['title']}")
        print(f"   Source: {story['source']}")
        print(f"   URL: {story['url']}")
        print(f"   Category: {story['category']}")
        print(f"   Content: {story['content'][:150]}...")

    # Verify content is real (not generic mock)
    if results and 'Wikipedia' in results[0]['source']:
        print("\n✅ SUCCESS: Historical search is returning REAL Wikipedia content!")
    elif results and 'Web Search' in results[0]['source']:
        print("\n✅ SUCCESS: Historical search is returning REAL web search content!")
    else:
        print("\n⚠️  WARNING: Historical search is using mock data (libraries may not be installed)")


def test_caching():
    """Test that caching is working."""
    print("\n" + "="*80)
    print("TESTING CACHE FUNCTIONALITY")
    print("="*80)

    search_tools = SearchTools()

    location = "London"
    print(f"\nFirst search for: {location}")

    import time
    start = time.time()
    results1 = search_tools.search_youtube_videos(location, max_results=2)
    time1 = time.time() - start

    print(f"First search took: {time1:.2f} seconds")

    print(f"\nSecond search for same location (should use cache)")
    start = time.time()
    results2 = search_tools.search_youtube_videos(location, max_results=2)
    time2 = time.time() - start

    print(f"Second search took: {time2:.2f} seconds")

    if time2 < time1 * 0.5:  # Cache should be significantly faster
        print("\n✅ SUCCESS: Caching is working (second search was much faster)!")
    else:
        print("\n⚠️  INFO: Cache may be working, but speed difference was not significant")

    # Verify same results
    if results1 == results2:
        print("✅ SUCCESS: Cached results match original results!")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("ROUTE STORIES - REAL SEARCH API INTEGRATION TESTS")
    print("="*80)

    try:
        test_youtube_search()
    except Exception as e:
        print(f"\n❌ ERROR in YouTube search test: {e}")

    try:
        test_music_search()
    except Exception as e:
        print(f"\n❌ ERROR in music search test: {e}")

    try:
        test_historical_search()
    except Exception as e:
        print(f"\n❌ ERROR in historical search test: {e}")

    try:
        test_caching()
    except Exception as e:
        print(f"\n❌ ERROR in caching test: {e}")

    print("\n" + "="*80)
    print("TEST SUITE COMPLETED")
    print("="*80)
    print("\nNOTE: If you see mock data warnings, install missing libraries:")
    print("  pip install youtube-search-python wikipedia-api duckduckgo-search spotipy")
    print("\n")


if __name__ == "__main__":
    main()
