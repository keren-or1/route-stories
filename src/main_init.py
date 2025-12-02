"""
Initialization logic for main application.
"""

from src.utils import setup_logger, QueueManager
from src.services import GoogleMapsService, GeminiClient, SearchTools
from src.agents import VideoAgent, SongAgent, StoryAgent, JudgeAgent
from src.core import Orchestrator


def initialize_services(settings, log_level):
    """Initialize all services and agents."""
    # Setup logging
    logger = setup_logger(
        log_level=log_level,
        log_dir=settings.logs_dir,
        enable_console=True,
        enable_file=True
    )

    logger.info("="*80)
    logger.info("Route Stories - Starting Application")
    logger.info("="*80)

    # Initialize services
    logger.info("Initializing services...")
    google_maps = GoogleMapsService(settings.google_maps_api_key)
    gemini_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        max_tokens=settings.gemini_max_tokens,
        temperature=settings.gemini_temperature
    )
    search_tools = SearchTools()

    # Initialize agents
    logger.info("Initializing agents...")
    video_agent = VideoAgent(gemini_client, search_tools)
    song_agent = SongAgent(gemini_client, search_tools)
    story_agent = StoryAgent(gemini_client, search_tools)
    judge_agent = JudgeAgent(gemini_client)

    # Initialize queue manager
    queue_manager = QueueManager()

    # Initialize orchestrator
    orchestrator = Orchestrator(
        video_agent=video_agent,
        song_agent=song_agent,
        story_agent=story_agent,
        judge_agent=judge_agent,
        queue_manager=queue_manager
    )

    return {
        'logger': logger,
        'google_maps': google_maps,
        'orchestrator': orchestrator,
        'queue_manager': queue_manager
    }
