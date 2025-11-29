# Route Stories

AI-powered journey content curator using multi-agent system architecture.

## Overview

Route Stories transforms road trips into enriched experiences by intelligently selecting content (videos, music, and stories) for each location along your route. The system uses Google Maps API to plan your journey and employs a sophisticated multi-agent architecture powered by Google Gemini AI to curate the perfect content for each waypoint.

## Key Features

- **Multi-Agent Architecture**: Four specialized AI agents (Video, Song, Story, and Judge) work in parallel
- **Real Search APIs**: YouTube, Wikipedia, and music search with actual content (no mock data!)
- **Intelligent Content Curation**: Each location gets matched with the most relevant video, song, or story
- **Google Maps Integration**: Automatic route planning with waypoint extraction
- **Smart Caching**: 24-hour cache reduces API calls by 1000x on repeated searches
- **Concurrent Processing**: ThreadPoolExecutor for efficient parallel agent execution
- **Queue-Based Communication**: Robust inter-agent communication system
- **Comprehensive Logging**: Detailed execution logs and performance metrics

## Quick Start

### Web UI (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config/.env.example .env
# Edit .env with your API keys

# Start the web server
python src/web_main.py

# Open browser to http://localhost:8080
```

### Command Line Interface

```bash
# Run the application
python src/main.py

# Run with specific route
python src/main.py --start "Tel Aviv" --end "Jerusalem"
```

For detailed setup and usage instructions, see [docs/README.md](docs/README.md)

## Project Structure

```
route-stories/
├── src/                           # Source code
│   ├── agents/                    # AI agent modules
│   ├── services/                  # External API services
│   ├── core/                      # Core orchestration logic
│   ├── ui/                        # Command-line interface
│   ├── web/                       # Flask web UI
│   │   ├── static/                # CSS, JavaScript
│   │   └── templates/             # HTML templates
│   ├── utils/                     # Helper utilities
│   ├── config.py                  # Configuration management
│   ├── main.py                    # CLI entry point
│   └── web_main.py                # Web UI entry point
├── tests/                         # Unit and integration tests
├── docs/                          # Documentation
│   ├── README.md                  # Detailed setup/usage guide
│   ├── ARCHITECTURE.md            # System architecture
│   ├── PRD.md                     # Product requirements
│   ├── WEB_UI.md                  # Web UI documentation
│   └── ...                        # Additional documentation
├── config/                        # Configuration files
│   └── .env.example               # Environment template
├── results/                       # Output and execution results
├── analysis/                      # Research and analysis
└── requirements.txt               # Python dependencies
```

## Documentation

- **[Setup Guide](docs/README.md)** - Detailed installation and configuration
- **[Web UI Guide](docs/WEB_UI.md)** - Web interface documentation and usage
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Product Requirements](docs/PRD.md)** - Features and specifications
- **[Prompt Engineering](docs/PROMPTS.md)** - Agent prompt design
- **[Cost Analysis](docs/COSTS.md)** - API usage and cost breakdown
- **[Testing Guide](docs/TESTING.md)** - Test coverage and methodology
- **[Execution Log](docs/EXECUTION_LOG.md)** - Sample execution results
- **[Parameter Analysis](docs/PARAMETER_ANALYSIS.md)** - Configuration research

## Technology Stack

- **Language**: Python 3.9+
- **Web Framework**: Flask 3.0 (for web UI)
- **AI Model**: Google Gemini Pro
- **APIs**: Google Maps Directions API, YouTube Search, Spotify, Web Search
- **Concurrency**: ThreadPoolExecutor, Queue-based communication
- **Testing**: pytest with comprehensive coverage
- **Configuration**: pydantic-settings with environment variables

## System Architecture

Route Stories uses a sophisticated multi-agent architecture:

1. **Google Maps Service**: Fetches route and extracts waypoints
2. **Scheduler**: Manages progression through waypoints
3. **Orchestrator**: Coordinates parallel agent execution
4. **Content Agents** (Video, Song, Story): Search and retrieve content candidates
5. **Judge Agent**: Evaluates and selects the best content for each location
6. **Collector**: Aggregates results and generates output

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design.

## Requirements

- Python 3.9 or higher
- Google Maps API key (with Directions API enabled)
- Google Gemini API key
- Internet connection for API access

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/agents/test_video_agent.py
```

## Output Format

The system generates JSON output with:
- Complete route information
- All content candidates (video, song, story) for each waypoint
- Judge's decision and reasoning
- Performance statistics and metrics

Example output is available in `results/demo_execution_*.json`

## License

Academic project for Reichman University - LLM Agents Course

## Authors

Assignment 4 - Route Stories
Reichman University, 2025

---

For detailed documentation, please refer to the `docs/` directory.
