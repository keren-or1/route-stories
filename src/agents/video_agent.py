"""
Video Agent - Searches for relevant YouTube videos about locations.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent, AgentTask
from src.services.gemini_client import GeminiClient
from src.services.search_tools import SearchTools
from src.utils.queue_manager import AgentResult
from src.agents.agent_prompts import VideoPrompts
from src.agents.response_parser import parse_choice, parse_score, parse_reasoning
from src.agents.video_filter import filter_and_score_videos


class VideoAgent(BaseAgent):
    """
    Agent responsible for finding relevant YouTube videos for locations.
    Uses Gemini to analyze search results and select the most appropriate video.
    """

    def __init__(self, gemini_client: GeminiClient, search_tools: SearchTools):
        """
        Initialize Video Agent.

        Args:
            gemini_client: Gemini API client
            search_tools: Search utilities
        """
        super().__init__(name="VideoAgent", agent_type="video")
        self.gemini = gemini_client
        self.search = search_tools

    def execute(self, task: AgentTask) -> AgentResult:
        """
        Search for and select the best YouTube video for a location.

        Args:
            task: AgentTask with location information

        Returns:
            AgentResult with selected video
        """
        self.logger.info(f"Searching videos for: {task.address}")

        # Step 1: Search for videos
        videos = self.search.search_youtube_videos(task.address, max_results=5)

        if not videos:
            return self._create_result(
                task=task,
                content={},
                error="No videos found"
            )

        # Step 2: Use Gemini to analyze and select best video
        selected_video = self._select_best_video(task.address, videos)

        # Step 3: Create result
        content = {
            "selected": selected_video,
            "candidates": videos,
            "selection_reasoning": selected_video.get("reasoning", "")
        }

        self.logger.info(f"Selected video: {selected_video.get('title', 'N/A')}")

        return self._create_result(task=task, content=content)

    def _select_best_video(
        self,
        location: str,
        videos: list
    ) -> Dict[str, Any]:
        """
        Use Gemini to select the most relevant video with quality filtering.

        Args:
            location: Location name
            videos: List of video dictionaries

        Returns:
            Selected video with reasoning and relevance score
        """
        # Step 1: Filter and score videos for quality
        filtered_videos = filter_and_score_videos(location, videos)

        if not filtered_videos:
            self.logger.warning("No high-quality videos after filtering, using all videos")
            filtered_videos = [(v, 0) for v in videos]

        # Sort by score (relevance)
        sorted_videos = sorted(filtered_videos, key=lambda x: x[1], reverse=True)
        top_videos = [v[0] for v in sorted_videos[:5]]

        # Build enhanced prompt for Gemini
        videos_text = "\n\n".join([
            f"Video {i+1}:\n"
            f"Title: {v['title']}\n"
            f"Description: {v['description']}\n"
            f"Duration: {v.get('duration', 'N/A')}\n"
            f"Views: {v.get('views', 'N/A')}\n"
            f"Channel: {v.get('channel', 'N/A')}\n"
            f"Upload Date: {v.get('upload_date', 'N/A')}"
            for i, v in enumerate(top_videos)
        ])

        # Get prompts
        system_prompt = VideoPrompts.SYSTEM
        user_prompt = VideoPrompts.user_prompt(location, videos_text, len(top_videos))

        try:
            response = self.gemini.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response
            choice_idx = parse_choice(response, len(top_videos))
            reasoning = parse_reasoning(response)
            score = parse_score(response)

            selected = top_videos[choice_idx].copy()
            selected["reasoning"] = reasoning
            selected["relevance_score"] = score

            return selected

        except Exception as e:
            self.logger.warning(f"Gemini selection failed, using top-scored video: {e}")
            selected = top_videos[0].copy()
            selected["reasoning"] = "Top-ranked by quality metrics"
            selected["relevance_score"] = sorted_videos[0][1] if sorted_videos else 0
            return selected
