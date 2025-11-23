"""
Shared test fixtures for Route Stories tests.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from src.agents.base_agent import AgentTask
from src.utils.queue_manager import AgentResult


@pytest.fixture
def mock_waypoint():
    """Sample waypoint for testing."""
    return {
        'point_id': 1,
        'address': 'Times Square, New York, NY',
        'lat': 40.758896,
        'lng': -73.985130
    }


@pytest.fixture
def sample_agent_task(mock_waypoint):
    """Sample AgentTask for testing."""
    return AgentTask(
        route_id="test-route-001",
        point_id=mock_waypoint['point_id'],
        address=mock_waypoint['address'],
        location={'lat': mock_waypoint['lat'], 'lng': mock_waypoint['lng']},
        context={}
    )


@pytest.fixture
def mock_video_results():
    """Mock YouTube video search results."""
    return [
        {
            'title': 'Times Square: The Crossroads of the World',
            'description': 'Exploring the history and culture of Times Square',
            'url': 'https://youtube.com/watch?v=abc123',
            'duration': '8:45',
            'views': '1.2M',
            'channel': 'NYC History'
        },
        {
            'title': 'Walking Tour Times Square NYC',
            'description': 'A complete walking tour of Times Square at night',
            'url': 'https://youtube.com/watch?v=def456',
            'duration': '15:30',
            'views': '850K',
            'channel': 'Virtual Tourist'
        },
        {
            'title': 'Times Square New Years Eve 2024',
            'description': 'Full ball drop celebration',
            'url': 'https://youtube.com/watch?v=ghi789',
            'duration': '45:00',
            'views': '5M',
            'channel': 'ABC News'
        }
    ]


@pytest.fixture
def mock_song_results():
    """Mock song search results."""
    return [
        {
            'title': 'Empire State of Mind',
            'artist': 'Jay-Z feat. Alicia Keys',
            'album': 'The Blueprint 3',
            'url': 'https://spotify.com/track/123',
            'duration': '4:36'
        },
        {
            'title': 'New York, New York',
            'artist': 'Frank Sinatra',
            'album': 'Trilogy: Past Present Future',
            'url': 'https://spotify.com/track/456',
            'duration': '3:26'
        },
        {
            'title': 'Welcome to New York',
            'artist': 'Taylor Swift',
            'album': '1989',
            'url': 'https://spotify.com/track/789',
            'duration': '3:32'
        }
    ]


@pytest.fixture
def mock_story_results():
    """Mock historical story results."""
    return [
        {
            'title': 'The Birth of Times Square',
            'summary': 'In 1904, the area was renamed Times Square after The New York Times moved its headquarters to the newly erected Times Building.',
            'source': 'NYC Historical Society',
            'era': '1900s'
        },
        {
            'title': 'The Great White Way',
            'summary': 'Times Square earned its nickname in the 1920s when electric billboards illuminated Broadway.',
            'source': 'Broadway Museum',
            'era': '1920s'
        }
    ]


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client."""
    mock = Mock()
    mock.simple_query = Mock(return_value="CHOICE: 1\nREASONING: Best video for travelers")
    mock.structured_query = Mock(return_value={
        'selected': 'video',
        'reasoning': 'Most relevant for location',
        'scores': {'video': 9.0, 'song': 7.0, 'story': 8.0},
        'confidence': 85
    })
    return mock


@pytest.fixture
def mock_search_tools():
    """Mock search tools."""
    mock = Mock()
    mock.search_youtube_videos = Mock(return_value=[
        {
            'title': 'Test Video',
            'description': 'Test description',
            'url': 'https://youtube.com/test',
            'duration': '10:00',
            'views': '1M',
            'channel': 'Test Channel'
        }
    ])
    mock.search_songs = Mock(return_value=[
        {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'url': 'https://spotify.com/test',
            'duration': '3:30'
        }
    ])
    mock.search_stories = Mock(return_value=[
        {
            'title': 'Test Story',
            'summary': 'Test historical content',
            'source': 'Test Source',
            'era': '2000s'
        }
    ])
    return mock


@pytest.fixture
def sample_agent_result(sample_agent_task):
    """Sample successful agent result."""
    return AgentResult(
        route_id=sample_agent_task.route_id,
        point_id=sample_agent_task.point_id,
        agent_type='video',
        content={'test': 'content'},
        timestamp=datetime.now(),
        error=None
    )


@pytest.fixture
def sample_error_result(sample_agent_task):
    """Sample error agent result."""
    return AgentResult(
        route_id=sample_agent_task.route_id,
        point_id=sample_agent_task.point_id,
        agent_type='video',
        content={},
        timestamp=datetime.now(),
        error='Test error occurred'
    )
