"""
Video Agent - Searches for relevant YouTube videos about locations.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent, AgentTask
from services.claude_client import ClaudeClient
from services.search_tools import SearchTools
from utils.queue_manager import AgentResult


class VideoAgent(BaseAgent):
    """
    Agent responsible for finding relevant YouTube videos for locations.
    Uses Claude to analyze search results and select the most appropriate video.
    """

    def __init__(self, claude_client: ClaudeClient, search_tools: SearchTools):
        """
        Initialize Video Agent.

        Args:
            claude_client: Claude API client
            search_tools: Search utilities
        """
        super().__init__(name="VideoAgent", agent_type="video")
        self.claude = claude_client
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

        # Step 2: Use Claude to analyze and select best video
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
        Use Claude to select the most relevant video.

        Args:
            location: Location name
            videos: List of video dictionaries

        Returns:
            Selected video with reasoning
        """
        # Build prompt for Claude
        videos_text = "\n\n".join([
            f"Video {i+1}:\n"
            f"Title: {v['title']}\n"
            f"Description: {v['description']}\n"
            f"Duration: {v['duration']}\n"
            f"Views: {v['views']}\n"
            f"Channel: {v['channel']}"
            for i, v in enumerate(videos)
        ])

        system_prompt = """You are a travel content curator. Your task is to select the most engaging and informative video about a location for travelers."""

        user_prompt = f"""Location: {location}

Available videos:
{videos_text}

Select the best video for someone traveling to {location}. Consider:
1. Relevance to the location
2. Content quality (views, channel reputation)
3. Video length (prefer 5-15 minutes)
4. Visual appeal and information value

Respond with:
CHOICE: [number 1-{len(videos)}]
REASONING: [brief explanation]"""

        try:
            response = self.claude.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response
            choice_idx = self._parse_choice(response, len(videos))
            reasoning = self._parse_reasoning(response)

            selected = videos[choice_idx].copy()
            selected["reasoning"] = reasoning

            return selected

        except Exception as e:
            self.logger.warning(f"Claude selection failed, using first video: {e}")
            selected = videos[0].copy()
            selected["reasoning"] = "Default selection (Claude unavailable)"
            return selected

    def _parse_choice(self, response: str, max_options: int) -> int:
        """Parse CHOICE from Claude response."""
        for line in response.split('\n'):
            if line.strip().startswith('CHOICE:'):
                try:
                    num = int(line.split(':')[1].strip())
                    return max(0, min(num - 1, max_options - 1))
                except ValueError:
                    pass
        return 0  # Default to first option

    def _parse_reasoning(self, response: str) -> str:
        """Parse REASONING from Claude response."""
        for line in response.split('\n'):
            if line.strip().startswith('REASONING:'):
                return line.split(':', 1)[1].strip()
        return "No reasoning provided"
