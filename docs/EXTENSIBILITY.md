# Route Stories - Extensibility Guide

## Overview

This guide demonstrates how to extend the Route Stories multi-agent system with custom agents, search integrations, and content types. The system is designed with extensibility in mind, following object-oriented design principles and clear abstraction layers.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Creating Custom Content Agents](#creating-custom-content-agents)
3. [Tutorial: Adding a Podcast Agent](#tutorial-adding-a-podcast-agent)
4. [Adding New Search API Integrations](#adding-new-search-api-integrations)
5. [Extending the Orchestrator](#extending-the-orchestrator)
6. [Hook Points and Extension Interfaces](#hook-points-and-extension-interfaces)
7. [Testing Custom Agents](#testing-custom-agents)
8. [Best Practices](#best-practices)

---

## Architecture Overview

The Route Stories system follows a modular architecture with clear extension points:

```
┌─────────────────────────────────────────────────────┐
│              Extension Points                        │
├─────────────────────────────────────────────────────┤
│  1. BaseAgent (Abstract Class)                      │
│     └─ Custom Agent Implementation                  │
│                                                      │
│  2. SearchTools (Service Layer)                     │
│     └─ New Search API Integration                   │
│                                                      │
│  3. Orchestrator (Core Coordination)                │
│     └─ Agent Registration & Execution               │
│                                                      │
│  4. Prompts & Parsers (Agent Behavior)              │
│     └─ Custom Selection Logic                       │
└─────────────────────────────────────────────────────┘
```

---

## Creating Custom Content Agents

All content agents extend the `BaseAgent` abstract class located at `/src/agents/base_agent.py`.

### BaseAgent Interface

```python
from abc import ABC, abstractmethod
from src.agents.base_agent import BaseAgent, AgentTask
from src.utils.queue_manager import AgentResult

class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, agent_type: str):
        """
        Initialize base agent.

        Args:
            name: Agent name for logging
            agent_type: Agent type identifier (video, song, story, judge, etc.)
        """
        pass

    @abstractmethod
    def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute agent task and return result.

        Args:
            task: AgentTask with location and context

        Returns:
            AgentResult with findings
        """
        pass
```

### Key Components

1. **AgentTask**: Input data structure containing:
   - `route_id`: Unique route identifier
   - `point_id`: Waypoint identifier
   - `address`: Human-readable location address
   - `location`: Coordinates `{'lat': float, 'lng': float}`
   - `context`: Optional context dictionary

2. **AgentResult**: Output data structure containing:
   - `route_id`: Route identifier
   - `point_id`: Point identifier
   - `agent_type`: Type of agent that generated result
   - `content`: Dictionary with agent findings
   - `timestamp`: Result generation timestamp
   - `error`: Optional error message

3. **Helper Methods**:
   - `_create_result()`: Create standardized AgentResult
   - `_handle_error()`: Handle exceptions gracefully
   - `run()`: Wrapper that adds error handling to `execute()`

---

## Tutorial: Adding a Podcast Agent

This tutorial demonstrates how to add a new agent that finds relevant podcast episodes for each location.

### Step 1: Define the Agent Class

Create `/src/agents/podcast_agent.py`:

```python
"""
Podcast Agent - Searches for relevant podcast episodes about locations.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent, AgentTask
from src.services.gemini_client import GeminiClient
from src.services.search_tools import SearchTools
from src.utils.queue_manager import AgentResult


class PodcastAgent(BaseAgent):
    """
    Agent responsible for finding relevant podcast episodes for locations.
    Uses Gemini to analyze search results and select the most appropriate episode.
    """

    def __init__(self, gemini_client: GeminiClient, search_tools: SearchTools):
        """
        Initialize Podcast Agent.

        Args:
            gemini_client: Gemini API client for content selection
            search_tools: Search utilities (must have podcast search capability)
        """
        super().__init__(name="PodcastAgent", agent_type="podcast")
        self.gemini = gemini_client
        self.search = search_tools

    def execute(self, task: AgentTask) -> AgentResult:
        """
        Search for and select the best podcast episode for a location.

        Args:
            task: AgentTask with location information

        Returns:
            AgentResult with selected podcast episode
        """
        self.logger.info(f"Searching podcasts for: {task.address}")

        # Step 1: Search for podcast episodes
        podcasts = self.search.search_podcasts(task.address, max_results=5)

        if not podcasts:
            return self._create_result(
                task=task,
                content={},
                error="No podcast episodes found"
            )

        # Step 2: Use Gemini to select best episode
        selected_podcast = self._select_best_podcast(task.address, podcasts)

        # Step 3: Create result
        content = {
            "selected": selected_podcast,
            "candidates": podcasts,
            "selection_reasoning": selected_podcast.get("reasoning", "")
        }

        self.logger.info(f"Selected podcast: {selected_podcast.get('title', 'N/A')}")

        return self._create_result(task=task, content=content)

    def _select_best_podcast(
        self,
        location: str,
        podcasts: list
    ) -> Dict[str, Any]:
        """
        Use Gemini to select the most relevant podcast episode.

        Args:
            location: Location name
            podcasts: List of podcast episode dictionaries

        Returns:
            Selected podcast with reasoning
        """
        # Build prompt for Gemini
        podcasts_text = "\n\n".join([
            f"Podcast {i+1}:\n"
            f"Title: {p['title']}\n"
            f"Show: {p['show']}\n"
            f"Description: {p['description']}\n"
            f"Duration: {p['duration']}\n"
            f"Release Date: {p['release_date']}"
            for i, p in enumerate(podcasts)
        ])

        system_prompt = """You are a podcast curator specializing in location-based content.
        Analyze podcast episodes and select the most relevant one for the given location."""

        user_prompt = f"""Location: {location}

Available podcast episodes:
{podcasts_text}

Select the most relevant podcast episode. Respond in this format:
CHOICE: [number 1-{len(podcasts)}]
REASONING: [Brief explanation of why this episode is most relevant]
SCORE: [Relevance score 0-10]"""

        try:
            response = self.gemini.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response (reuse existing parsers)
            from src.agents.response_parser import parse_choice, parse_reasoning, parse_score

            choice_idx = parse_choice(response, len(podcasts))
            reasoning = parse_reasoning(response)
            score = parse_score(response)

            selected = podcasts[choice_idx].copy()
            selected["reasoning"] = reasoning
            selected["relevance_score"] = score

            return selected

        except Exception as e:
            self.logger.warning(f"Gemini selection failed, using first episode: {e}")
            selected = podcasts[0].copy()
            selected["reasoning"] = "Default selection due to API error"
            selected["relevance_score"] = 5.0
            return selected
```

### Step 2: Add Podcast Search to SearchTools

Extend `/src/services/search_tools.py`:

```python
def search_podcasts(self, location: str, max_results: int = 5) -> list:
    """
    Search for podcast episodes related to a location.

    Args:
        location: Location to search for
        max_results: Maximum number of results

    Returns:
        List of podcast episode dictionaries
    """
    try:
        # Example: Using Podcast Index API or iTunes Search API
        query = f"{location} travel tourism history"

        # Make API call (pseudo-code)
        response = self._podcast_api_call(query, max_results)

        # Parse and structure results
        podcasts = []
        for item in response['results']:
            podcasts.append({
                'title': item['episode_title'],
                'show': item['podcast_name'],
                'description': item['description'],
                'duration': item['duration'],
                'release_date': item['pub_date'],
                'url': item['audio_url'],
                'thumbnail': item['image_url']
            })

        return podcasts

    except Exception as e:
        self.logger.error(f"Podcast search failed: {e}")
        return []
```

### Step 3: Register Agent in Orchestrator

Modify `/src/core/orchestrator.py` to include the podcast agent:

```python
class Orchestrator:
    def __init__(
        self,
        video_agent: VideoAgent,
        song_agent: SongAgent,
        story_agent: StoryAgent,
        podcast_agent: PodcastAgent,  # NEW
        judge_agent: JudgeAgent,
        queue_manager: QueueManager,
        max_workers: int = 5  # Increased from 4
    ):
        self.video_agent = video_agent
        self.song_agent = song_agent
        self.story_agent = story_agent
        self.podcast_agent = podcast_agent  # NEW
        self.judge_agent = judge_agent
        self.queue_manager = queue_manager
        self.executor = create_executor(max_workers)

    def process_waypoint(
        self,
        route_id: str,
        point_id: int,
        address: str,
        location: Dict[str, float]
    ) -> Dict[str, AgentResult]:
        # Create task
        task = AgentTask(
            route_id=route_id,
            point_id=point_id,
            address=address,
            location=location
        )

        # Launch content agents in parallel
        futures = {
            'video': self.executor.submit(self._run_agent, self.video_agent, task),
            'song': self.executor.submit(self._run_agent, self.song_agent, task),
            'story': self.executor.submit(self._run_agent, self.story_agent, task),
            'podcast': self.executor.submit(self._run_agent, self.podcast_agent, task)  # NEW
        }

        # Wait for all content agents...
        # (rest of implementation remains the same)
```

### Step 4: Update Judge Agent

The judge agent must be aware of the new content type. Update `/src/agents/judge_agent.py`:

```python
def _prepare_content_for_judging(self, content_results: Dict[str, AgentResult]) -> Dict[str, Any]:
    """Extract and structure content for judge evaluation."""
    prepared = {}

    # Include all content types
    for content_type in ['video', 'song', 'story', 'podcast']:  # Added 'podcast'
        if content_type in content_results:
            result = content_results[content_type]
            if not result.error and result.content:
                prepared[content_type] = result.content.get('selected', {})

    return prepared
```

### Step 5: Initialize and Use

In your main application (`/src/main.py`):

```python
from src.agents.podcast_agent import PodcastAgent

# Initialize services
gemini_client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
search_tools = SearchTools(api_key=os.getenv("SEARCH_API_KEY"))

# Initialize agents
video_agent = VideoAgent(gemini_client, search_tools)
song_agent = SongAgent(gemini_client, search_tools)
story_agent = StoryAgent(gemini_client, search_tools)
podcast_agent = PodcastAgent(gemini_client, search_tools)  # NEW
judge_agent = JudgeAgent(gemini_client)

# Initialize orchestrator with new agent
orchestrator = Orchestrator(
    video_agent=video_agent,
    song_agent=song_agent,
    story_agent=story_agent,
    podcast_agent=podcast_agent,  # NEW
    judge_agent=judge_agent,
    queue_manager=queue_manager,
    max_workers=5
)
```

---

## Adding New Search API Integrations

### Integration Pattern

All search integrations should be added to `/src/services/search_tools.py` and follow this pattern:

```python
class SearchTools:
    def search_[content_type](self, location: str, max_results: int = 5) -> list:
        """
        Search for [content_type] related to a location.

        Args:
            location: Location to search for
            max_results: Maximum results to return

        Returns:
            List of dictionaries with structured results
        """
        try:
            # 1. Build search query
            query = self._build_query(location, content_type)

            # 2. Call external API
            response = self._make_api_call(query, max_results)

            # 3. Parse and structure results
            results = self._parse_api_response(response)

            # 4. Validate and filter
            filtered_results = self._filter_results(results)

            return filtered_results[:max_results]

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
```

### Example: Adding Yelp Restaurant Search

```python
def search_restaurants(self, location: str, max_results: int = 5) -> list:
    """
    Search for restaurants using Yelp API.

    Args:
        location: Location to search for restaurants
        max_results: Maximum number of results

    Returns:
        List of restaurant dictionaries
    """
    import requests

    try:
        headers = {"Authorization": f"Bearer {self.yelp_api_key}"}
        params = {
            "location": location,
            "limit": max_results,
            "sort_by": "rating",
            "categories": "restaurants"
        }

        response = requests.get(
            "https://api.yelp.com/v3/businesses/search",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        restaurants = []
        for business in data.get('businesses', []):
            restaurants.append({
                'name': business['name'],
                'rating': business['rating'],
                'review_count': business['review_count'],
                'price': business.get('price', 'N/A'),
                'categories': [c['title'] for c in business['categories']],
                'address': ' '.join(business['location']['display_address']),
                'phone': business.get('phone', ''),
                'url': business['url'],
                'image_url': business.get('image_url', '')
            })

        return restaurants

    except Exception as e:
        self.logger.error(f"Yelp search failed: {e}")
        return []
```

---

## Extending the Orchestrator

### Custom Processing Logic

The orchestrator can be extended to support custom processing patterns:

```python
class ExtendedOrchestrator(Orchestrator):
    """Extended orchestrator with custom processing capabilities."""

    def process_waypoint_with_priority(
        self,
        route_id: str,
        point_id: int,
        address: str,
        location: Dict[str, float],
        priority_agent: str = 'video'
    ) -> Dict[str, AgentResult]:
        """
        Process waypoint with one agent prioritized.

        Args:
            priority_agent: Agent to run first before others
        """
        task = AgentTask(route_id, point_id, address, location)

        # Run priority agent first
        priority_result = self._run_agent(
            getattr(self, f"{priority_agent}_agent"),
            task
        )

        # If priority agent succeeds, run others in parallel
        if not priority_result.error:
            # Launch remaining agents...
            pass

        return results
```

---

## Hook Points and Extension Interfaces

### 1. Pre/Post Processing Hooks

Add hooks to agents for custom processing:

```python
class ExtensibleAgent(BaseAgent):
    """Agent with pre/post processing hooks."""

    def __init__(self, name: str, agent_type: str):
        super().__init__(name, agent_type)
        self.pre_hooks = []
        self.post_hooks = []

    def register_pre_hook(self, hook_fn):
        """Register a function to run before execute()."""
        self.pre_hooks.append(hook_fn)

    def register_post_hook(self, hook_fn):
        """Register a function to run after execute()."""
        self.post_hooks.append(hook_fn)

    def execute(self, task: AgentTask) -> AgentResult:
        # Run pre-hooks
        for hook in self.pre_hooks:
            task = hook(task)

        # Execute main logic
        result = self._execute_internal(task)

        # Run post-hooks
        for hook in self.post_hooks:
            result = hook(result)

        return result
```

### 2. Custom Result Filters

Add filtering logic to queue manager:

```python
class FilteredQueueManager(QueueManager):
    """Queue manager with result filtering."""

    def __init__(self):
        super().__init__()
        self.filters = []

    def add_filter(self, filter_fn):
        """Add a filter function."""
        self.filters.append(filter_fn)

    def put_result(self, result: AgentResult):
        """Put result with filtering."""
        for filter_fn in self.filters:
            if not filter_fn(result):
                self.logger.info(f"Result filtered: {result}")
                return

        super().put_result(result)
```

### 3. Dynamic Agent Registry

Create a registry for runtime agent registration:

```python
class AgentRegistry:
    """Registry for dynamic agent management."""

    def __init__(self):
        self.agents = {}

    def register(self, agent_type: str, agent_instance: BaseAgent):
        """Register an agent."""
        self.agents[agent_type] = agent_instance

    def get(self, agent_type: str) -> BaseAgent:
        """Get agent by type."""
        return self.agents.get(agent_type)

    def list_types(self) -> list:
        """List all registered agent types."""
        return list(self.agents.keys())
```

---

## Testing Custom Agents

### Unit Test Template

Create `/tests/agents/test_podcast_agent.py`:

```python
import pytest
from unittest.mock import Mock
from src.agents.podcast_agent import PodcastAgent
from src.agents.base_agent import AgentTask


class TestPodcastAgent:
    """Test suite for PodcastAgent."""

    @pytest.fixture
    def mock_gemini_client(self):
        return Mock()

    @pytest.fixture
    def mock_search_tools(self):
        return Mock()

    @pytest.fixture
    def sample_task(self):
        return AgentTask(
            route_id="test-route",
            point_id=1,
            address="Central Park, New York, NY",
            location={'lat': 40.785091, 'lng': -73.968285}
        )

    def test_initialization(self, mock_gemini_client, mock_search_tools):
        """Test agent initialization."""
        agent = PodcastAgent(mock_gemini_client, mock_search_tools)

        assert agent.name == "PodcastAgent"
        assert agent.agent_type == "podcast"
        assert agent.gemini == mock_gemini_client
        assert agent.search == mock_search_tools

    def test_execute_success(
        self,
        mock_gemini_client,
        mock_search_tools,
        sample_task
    ):
        """Test successful podcast search and selection."""
        # Mock search results
        mock_search_tools.search_podcasts.return_value = [
            {
                'title': 'History of Central Park',
                'show': 'NYC Stories',
                'description': 'Deep dive into Central Park history',
                'duration': '45:00',
                'release_date': '2023-05-01'
            }
        ]

        # Mock Gemini response
        mock_gemini_client.simple_query.return_value = (
            "CHOICE: 1\n"
            "REASONING: Perfect match for Central Park\n"
            "SCORE: 9.5"
        )

        agent = PodcastAgent(mock_gemini_client, mock_search_tools)
        result = agent.execute(sample_task)

        assert result.error is None
        assert 'selected' in result.content
        assert result.content['selected']['title'] == 'History of Central Park'

    def test_execute_no_results(
        self,
        mock_gemini_client,
        mock_search_tools,
        sample_task
    ):
        """Test behavior when no podcasts found."""
        mock_search_tools.search_podcasts.return_value = []

        agent = PodcastAgent(mock_gemini_client, mock_search_tools)
        result = agent.execute(sample_task)

        assert result.error == "No podcast episodes found"
        assert result.content == {}
```

---

## Best Practices

### 1. Agent Design Principles

- **Single Responsibility**: Each agent should focus on one type of content
- **Fail Gracefully**: Always return AgentResult, even on errors
- **Log Extensively**: Use `self.logger` for debugging and monitoring
- **Timeout Awareness**: External API calls should have timeouts
- **Stateless**: Agents should not maintain state between calls

### 2. Search Integration Guidelines

- **Rate Limiting**: Implement rate limiting for API calls
- **Caching**: Cache search results when appropriate
- **Error Handling**: Handle API failures gracefully with fallbacks
- **Structured Output**: Always return consistently structured dictionaries
- **API Keys**: Store API keys in environment variables

### 3. Orchestrator Extensions

- **Thread Safety**: Ensure custom orchestrator logic is thread-safe
- **Resource Management**: Properly shutdown thread pools and connections
- **Timeout Handling**: Set appropriate timeouts for agent execution
- **Error Propagation**: Don't let one agent failure stop others

### 4. Testing Requirements

- **Unit Tests**: Test agents in isolation with mocked dependencies
- **Integration Tests**: Test agent interactions with real instances
- **Mock External APIs**: Never call real APIs in tests
- **Coverage Target**: Aim for 70%+ code coverage

---

## Example: Complete Custom Agent

Here's a complete example of a weather agent:

```python
"""Weather Agent - Provides weather information for locations."""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent, AgentTask
from src.utils.queue_manager import AgentResult
import requests


class WeatherAgent(BaseAgent):
    """Agent that fetches weather information for locations."""

    def __init__(self, weather_api_key: str):
        super().__init__(name="WeatherAgent", agent_type="weather")
        self.api_key = weather_api_key

    def execute(self, task: AgentTask) -> AgentResult:
        """
        Fetch weather information for the location.

        Args:
            task: AgentTask with location information

        Returns:
            AgentResult with weather data
        """
        self.logger.info(f"Fetching weather for: {task.address}")

        try:
            weather_data = self._fetch_weather(task.location)

            content = {
                "temperature": weather_data['temp'],
                "conditions": weather_data['conditions'],
                "humidity": weather_data['humidity'],
                "wind_speed": weather_data['wind_speed'],
                "forecast": weather_data['forecast']
            }

            return self._create_result(task=task, content=content)

        except Exception as e:
            return self._create_result(
                task=task,
                content={},
                error=f"Weather fetch failed: {str(e)}"
            )

    def _fetch_weather(self, location: Dict[str, float]) -> Dict[str, Any]:
        """Fetch weather data from API."""
        lat, lng = location['lat'], location['lng']

        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                'lat': lat,
                'lon': lng,
                'appid': self.api_key,
                'units': 'metric'
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        return {
            'temp': data['main']['temp'],
            'conditions': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'forecast': data['weather'][0]['main']
        }
```

---

## Summary

The Route Stories system provides multiple extension points for adding new functionality:

1. **Custom Agents**: Extend `BaseAgent` to create new content agents
2. **Search Integrations**: Add methods to `SearchTools` for new APIs
3. **Orchestrator Hooks**: Extend `Orchestrator` for custom processing logic
4. **Filter & Parse**: Add custom filtering and parsing logic for content types
5. **Testing**: Follow the established testing patterns for quality assurance

For questions or contributions, refer to the project's GitHub repository and architecture documentation.

---

**Last Updated**: December 3, 2025
**Version**: 1.0
**Contributors**: Route Stories Development Team
