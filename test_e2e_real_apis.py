#!/usr/bin/env python3
"""
End-to-end test: Verify search tools provide real APIs
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.search_tools import SearchTools

print("\n" + "="*80)
print("END-TO-END TEST: Search Tools with Real APIs")
print("="*80)

# Initialize
search_tools = SearchTools()

# Test locations
test_location = "Paris, France"

print(f"\nTest Location: {test_location}\n")

# Test Video Search
print("-" * 80)
print("Testing Video Search (YouTube)...")
print("-" * 80)

videos = search_tools.search_youtube_videos(test_location, max_results=2)

print(f"\nFound {len(videos)} videos:")
for i, video in enumerate(videos, 1):
    print(f"\n{i}. {video['title']}")
    print(f"   URL: {video['url']}")
    print(f"   Real URL: {'✅' if 'mock' not in video['url'] else '❌'}")
    print(f"   Channel: {video['channel']}")

# Test Music Search
print("\n" + "-" * 80)
print("Testing Music Search...")
print("-" * 80)

songs = search_tools.search_music(test_location, max_results=2)

print(f"\nFound {len(songs)} songs:")
for i, song in enumerate(songs, 1):
    print(f"\n{i}. {song['title']}")
    print(f"   Artist: {song['artist']}")
    print(f"   URL: {song['url']}")
    print(f"   Real URL: {'✅' if 'mock' not in song['url'] else '❌'}")
    print(f"   Source: {song.get('source', 'Unknown')}")

# Test Historical Search
print("\n" + "-" * 80)
print("Testing Historical Search (Wikipedia)...")
print("-" * 80)

stories = search_tools.search_historical_stories(test_location, max_results=2)

print(f"\nFound {len(stories)} stories:")
for i, story in enumerate(stories, 1):
    print(f"\n{i}. {story['title']}")
    print(f"   Source: {story['source']}")
    print(f"   URL: {story['url']}")
    print(f"   Real Content: {'✅' if story['source'] in ['Wikipedia', 'Web Search'] else '❌'}")
    print(f"   Preview: {story['content'][:80]}...")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

video_real = all('mock' not in v['url'] for v in videos)
song_real = all('mock' not in s['url'] for s in songs)
story_real = all(s['source'] in ['Wikipedia', 'Web Search'] for s in stories)

print(f"\nVideo Agent: {'✅ Using REAL YouTube data' if video_real else '❌ Using mock data'}")
print(f"Song Agent:  {'✅ Using REAL music data' if song_real else '❌ Using mock data'}")
print(f"Story Agent: {'✅ Using REAL Wikipedia data' if story_real else '❌ Using mock data'}")

if video_real and song_real and story_real:
    print("\n🎉 SUCCESS: All agents are using REAL search APIs!")
else:
    print("\n⚠️  WARNING: Some agents are still using mock data")

print("\n")
