"""
Service factory for creating route processing services.
Centralizes service initialization logic.
"""

from src.services import GoogleMapsService, GeminiClient, SearchTools
from src.agents import VideoAgent, SongAgent, StoryAgent, JudgeAgent
from src.core import Orchestrator, Collector
from src.utils import QueueManager


def create_services(settings):
    """
    Create all required services for route processing.

    Args:
        settings: Application settings object

    Returns:
        Dictionary of initialized services
    """
    google_maps = GoogleMapsService(settings.google_maps_api_key)
    gemini_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        max_tokens=settings.gemini_max_tokens,
        temperature=settings.gemini_temperature
    )
    search_tools = SearchTools()

    # Initialize agents
    video_agent = VideoAgent(gemini_client, search_tools)
    song_agent = SongAgent(gemini_client, search_tools)
    story_agent = StoryAgent(gemini_client, search_tools)
    judge_agent = JudgeAgent(gemini_client)

    # Initialize queue manager and orchestrator
    queue_manager = QueueManager()
    orchestrator = Orchestrator(
        video_agent=video_agent,
        song_agent=song_agent,
        story_agent=story_agent,
        judge_agent=judge_agent,
        queue_manager=queue_manager
    )

    return {
        'google_maps': google_maps,
        'orchestrator': orchestrator,
        'queue_manager': queue_manager
    }
