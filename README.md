# Route Stories - AI-Powered Journey Guide

A multi-agent system that enriches your route with curated content (videos, songs, and stories) for each waypoint along your journey.

## Overview

Route Stories uses Google Maps API to plan your route and deploys AI agents to find relevant content for each location:
- **Agent A (Video)**: Searches for YouTube videos about the location
- **Agent B (Song)**: Searches for songs/music related to the location
- **Agent C (Story)**: Finds historical facts and interesting stories
- **Judge Agent**: Evaluates all three options and selects the most appropriate content

## Architecture

```
User Input (CLI)
    ↓
Google Maps API → Route with Waypoints
    ↓
Scheduler (Manual/Timer)
    ↓
Orchestrator (Multi-threaded)
    ├─→ Video Agent (Thread 1)
    ├─→ Song Agent (Thread 2)
    ├─→ Story Agent (Thread 3)
    └─→ Judge Agent (Thread 4)
    ↓
Results Queue → Collector
    ↓
Output (Display Results)
```

## Requirements

- Python 3.8+
- Google Maps API Key
- Anthropic Claude API Key

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys:
# GOOGLE_MAPS_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

## Usage

### Basic Usage (Manual Mode)

```bash
python main.py
```

Then follow the prompts:
- Enter starting location
- Enter destination
- Press Enter to advance through each waypoint

### Command Line Arguments

```bash
# Specify start and end directly
python main.py --start "Tel Aviv" --end "Jerusalem"

# Set number of waypoints to process
python main.py --start "Tel Aviv" --end "Jerusalem" --max-points 3

# Enable verbose logging
python main.py --start "Tel Aviv" --end "Jerusalem" --verbose
```

## Project Structure

```
route-stories/
├── main.py                 # Entry point
├── config.py               # Configuration and settings
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # Base agent class
│   ├── video_agent.py     # YouTube video search agent
│   ├── song_agent.py      # Music search agent
│   ├── story_agent.py     # Historical story agent
│   └── judge_agent.py     # Decision-making judge agent
├── services/
│   ├── __init__.py
│   ├── google_maps.py     # Google Maps API integration
│   ├── claude_client.py   # Claude API wrapper
│   └── search_tools.py    # Search utilities (YouTube, etc.)
├── core/
│   ├── __init__.py
│   ├── orchestrator.py    # Multi-threaded agent orchestration
│   ├── scheduler.py       # Waypoint progression scheduler
│   └── collector.py       # Results collection and storage
├── ui/
│   ├── __init__.py
│   └── cli.py             # Command-line interface
└── utils/
    ├── __init__.py
    ├── logger.py          # Logging configuration
    └── queue_manager.py   # Queue management utilities
```

## Features

### Current Features (v1.0)
- ✅ Google Maps API integration for route planning
- ✅ Multi-threaded agent execution
- ✅ Queue-based inter-agent communication
- ✅ Manual waypoint progression
- ✅ Comprehensive logging
- ✅ Claude-powered agent decisions
- ✅ CLI interface

### Future Enhancements
- ⏳ Timer-based automatic progression
- ⏳ Web UI
- ⏳ Audio playback integration
- ⏳ Route caching
- ⏳ Export results to JSON/PDF

## Development

### Running Tests
```bash
pytest tests/
```

### Logging
Logs are written to `logs/route_stories.log` and console. Configure log level in `config.py`.

## License

Educational project for LLM Agents course.
