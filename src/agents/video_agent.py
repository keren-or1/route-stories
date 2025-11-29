"""
Video Agent - Searches for relevant YouTube videos about locations.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent, AgentTask
from src.services.gemini_client import GeminiClient
from src.services.search_tools import SearchTools
from src.utils.queue_manager import AgentResult


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
        filtered_videos = self._filter_and_score_videos(location, videos)

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

        system_prompt = """You are a travel content curator with expertise in selecting engaging educational videos.
Your task is to select the MOST RELEVANT and HIGH-QUALITY video about a specific location for travelers.
Prioritize videos that provide:
- Authentic location insights
- High production quality
- Accurate factual information
- Engaging storytelling"""

        user_prompt = f"""Location: {location}

Available videos (already filtered for quality):
{videos_text}

Select the SINGLE BEST video for someone visiting {location}. Consider:
1. Relevance and accuracy about {location}
2. Information value and educational content
3. Production quality and channel reputation
4. Optimal viewing length (prefer 5-20 minutes)
5. Recent vs timeless content appropriateness

IMPORTANT: Provide a brief, compelling reason why this video is the best choice.

Respond in exactly this format:
CHOICE: [number 1-{len(top_videos)}]
SCORE: [relevance score 0-100]
REASONING: [one sentence explaining why this video is best]"""

        try:
            response = self.gemini.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response
            choice_idx = self._parse_choice(response, len(top_videos))
            reasoning = self._parse_reasoning(response)
            score = self._parse_score(response)

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

    def _filter_and_score_videos(self, location: str, videos: list) -> list:
        """
        Filter out low-quality videos and score remaining ones by relevance.

        Args:
            location: Location name
            videos: List of video dictionaries

        Returns:
            List of (video, score) tuples, filtered and scored
        """
        scored_videos = []
        location_lower = location.lower()

        for video in videos:
            # Extract metadata
            title = video.get('title', '').lower()
            description = video.get('description', '').lower()
            views = video.get('views', 0) or 0
            duration = video.get('duration', '')

            # Initialize score
            score = 50  # Base score

            # Location relevance (most important)
            if location_lower in title:
                score += 25
            elif location_lower in description:
                score += 15

            # View count quality indicator
            if isinstance(views, int):
                if views > 1000000:
                    score += 15
                elif views > 100000:
                    score += 10
                elif views > 10000:
                    score += 5

            # Duration preference (5-20 minutes is good for travel content)
            if duration:
                try:
                    # Try to parse duration
                    if ':' in str(duration):
                        parts = str(duration).split(':')
                        if len(parts) == 2:
                            mins = int(parts[0])
                            if 5 <= mins <= 20:
                                score += 10
                            elif 3 <= mins <= 25:
                                score += 5
                except:
                    pass

            # Channel reputation (prefer larger channels)
            channel = video.get('channel', '').lower()
            if 'official' in channel or 'verified' in channel or video.get('channel_verified', False):
                score += 10

            # Recency bonus (prefer recent content)
            upload_date = video.get('upload_date', '')
            if upload_date and '2024' in str(upload_date):
                score += 5

            # Minimum quality filter
            if score >= 40:  # Keep videos with reasonable scores
                scored_videos.append((video, score))

        return scored_videos

    def _parse_score(self, response: str) -> int:
        """Parse SCORE from Gemini response."""
        for line in response.split('\n'):
            if line.strip().startswith('SCORE:'):
                try:
                    num = int(line.split(':')[1].strip())
                    return max(0, min(num, 100))
                except ValueError:
                    pass
        return 75  # Default score

    def _parse_choice(self, response: str, max_options: int) -> int:
        """Parse CHOICE from Gemini response."""
        for line in response.split('\n'):
            if line.strip().startswith('CHOICE:'):
                try:
                    num = int(line.split(':')[1].strip())
                    return max(0, min(num - 1, max_options - 1))
                except ValueError:
                    pass
        return 0  # Default to first option

    def _parse_reasoning(self, response: str) -> str:
        """Parse REASONING from Gemini response."""
        for line in response.split('\n'):
            if line.strip().startswith('REASONING:'):
                return line.split(':', 1)[1].strip()
        return "No reasoning provided"
