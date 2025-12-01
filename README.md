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

## Screenshots

### Web Interface

**Create Your Journey Story**
![Create Your Journey Story](screenshots/Create%20Your%20Journey%20Story.png)

**Processing Your Route**
![Processing Your Route](screenshots/Processing%20Your%20Journey%20Story.png)

**Example Results**
![Example 1](screenshots/example1.png)
![Example 2](screenshots/example2.png)

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
├── src/                          # Production source code
│   ├── agents/                   # Multi-agent system
│   │   ├── base_agent.py         # Abstract base class
│   │   ├── video_agent.py        # YouTube video search
│   │   ├── song_agent.py         # Music search
│   │   ├── story_agent.py        # Historical content search
│   │   └── judge_agent.py        # Content selection judge
│   ├── services/                 # External API integrations
│   │   ├── gemini_client.py      # Google Gemini AI
│   │   ├── search_tools.py       # YouTube, Wikipedia, Music APIs
│   │   ├── google_maps.py        # Google Maps integration
│   │   └── claude_client.py      # Claude API (alternative)
│   ├── core/                     # System orchestration
│   │   ├── orchestrator.py       # Parallel agent execution
│   │   ├── collector.py          # Result aggregation
│   │   └── scheduler.py          # Waypoint progression
│   ├── ui/                       # User interface
│   │   └── cli.py                # Command-line interface
│   ├── web/                      # Web application
│   │   ├── app.py                # Flask application
│   │   ├── routes.py             # API endpoints
│   │   └── templates/            # HTML templates
│   ├── utils/                    # Utilities
│   │   ├── logger.py             # Structured logging
│   │   └── queue_manager.py      # Thread-safe result queue
│   └── config.py                 # Configuration management
│
├── tests/                        # Comprehensive pytest test suite (223 tests)
│   ├── conftest.py               # Pytest fixtures and configuration
│   ├── agents/                   # Agent unit tests (29 tests)
│   │   ├── test_judge_agent.py   # 5 tests
│   │   ├── test_video_agent.py   # 10 tests
│   │   ├── test_song_agent.py    # 4 tests
│   │   └── test_story_agent.py   # 4 tests
│   ├── core/                     # Core system tests
│   │   └── test_orchestrator.py  # 5 tests
│   └── integration/              # Integration tests
│       └── test_end_to_end.py    # 6 tests
│
├── scripts/                      # Development and deployment scripts
│   └── manual_tests/             # Exploratory test scripts (not pytest)
│       ├── test_agents_search.py
│       ├── test_e2e_real_apis.py
│       ├── test_rate_limit_handling.py
│       ├── test_retry_logic.py
│       ├── test_search_apis.py
│       ├── test_setup.py
│       ├── test_waypoint_extraction.py
│       ├── test_web_app.py
│       └── README.md
│
├── docs/                         # Documentation
│   ├── PRD.md                    # Product Requirements Document
│   ├── ARCHITECTURE.md           # System architecture
│   ├── README.md                 # Quick start guide
│   ├── API.md                    # API documentation
│   ├── PROMPTS.md                # Prompt engineering
│   ├── PARAMETER_ANALYSIS.md     # Sensitivity analysis
│   ├── COSTS.md                  # Cost analysis
│   ├── WEB_UI.md                 # Web interface guide
│   ├── AI_MODEL_SELECTION.md     # AI model justification
│   └── TESTING.md                # Testing documentation
│
├── analysis/                     # Analysis and research
│   └── parameter_sensitivity_analysis.ipynb  # Jupyter notebook with visualizations
│
├── config/                       # Configuration files
│   ├── .env.example              # Environment template
│   └── settings.py               # Application settings
│
├── results/                      # Generated results and outputs
├── logs/                         # Application logs
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
└── README.md                     # Project README
```

### Directory Organization

The project follows Python packaging standards with a clear separation of concerns:

- **`src/`**: Production source code organized by functionality (agents, services, core orchestration)
- **`tests/`**: Formal pytest test suite with 34 tests organized by component
- **`docs/`**: Comprehensive documentation covering architecture, setup, and usage
- **`scripts/`**: Development scripts including manual integration tests
- **`analysis/`**: Research materials and analytical notebooks
- **`config/`**: Configuration templates and settings
- **`results/`**: Output and execution results directory

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

## OS Compatibility

Route Stories is built with Python and designed to be cross-platform compatible:

### Tested Platforms
- **macOS**: Fully tested on macOS 13+ (Ventura and later)
- **Linux**: Compatible with Ubuntu 20.04+, Debian, and other major distributions
- **Windows**: Compatible with Windows 10+ (requires Python 3.11+)

### Platform-Specific Notes

#### macOS
- Uses native threading (Python `threading` module)
- Tested with both Intel and Apple Silicon (M1/M2)
- Homebrew recommended for Python installation

#### Linux
- Fully compatible with systemd-based distributions
- Uses `threading` for concurrent agent execution
- Recommended: Python installed via system package manager

#### Windows
- Compatible with Windows 10 and later
- PowerShell or Command Prompt supported
- UTF-8 encoding handled automatically

### Cross-Platform Features
- **Threading**: Uses Python's built-in `threading` module (cross-platform)
- **File Paths**: Uses `pathlib` for OS-independent path handling
- **Environment Variables**: `.env` file support works across all platforms
- **API Integrations**: REST APIs work identically on all platforms

### Python Version Requirements
- **Minimum**: Python 3.11
- **Recommended**: Python 3.11 or 3.12
- All dependencies compatible with Python 3.11+

## License

Academic project for Reichman University - LLM Agents Course

## Authors

Assignment 4 - Route Stories
Reichman University, 2025

---

For detailed documentation, please refer to the `docs/` directory.
