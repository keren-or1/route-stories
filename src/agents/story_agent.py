"""
Story Agent - Searches for historical stories and facts about locations.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent, AgentTask
from src.services.gemini_client import GeminiClient
from src.services.search_tools import SearchTools
from src.utils.queue_manager import AgentResult


class StoryAgent(BaseAgent):
    """
    Agent responsible for finding historical stories and facts for locations.
    Uses Gemini to analyze search results and select the most interesting story.
    """

    def __init__(self, gemini_client: GeminiClient, search_tools: SearchTools):
        """
        Initialize Story Agent.

        Args:
            gemini_client: Gemini API client
            search_tools: Search utilities
        """
        super().__init__(name="StoryAgent", agent_type="story")
        self.gemini = gemini_client
        self.search = search_tools

    def execute(self, task: AgentTask) -> AgentResult:
        """
        Search for and select the best historical story for a location.

        Args:
            task: AgentTask with location information

        Returns:
            AgentResult with selected story
        """
        self.logger.info(f"Searching stories for: {task.address}")

        # Step 1: Search for stories
        stories = self.search.search_historical_stories(task.address, max_results=3)

        if not stories:
            return self._create_result(
                task=task,
                content={},
                error="No stories found"
            )

        # Step 2: Use Gemini to analyze and select best story
        selected_story = self._select_best_story(task.address, stories)

        # Step 3: Create result
        content = {
            "selected": selected_story,
            "candidates": stories,
            "selection_reasoning": selected_story.get("reasoning", "")
        }

        self.logger.info(f"Selected story: {selected_story.get('title', 'N/A')}")

        return self._create_result(task=task, content=content)

    def _select_best_story(
        self,
        location: str,
        stories: list
    ) -> Dict[str, Any]:
        """
        Use Gemini to select the most interesting story.

        Args:
            location: Location name
            stories: List of story dictionaries

        Returns:
            Selected story with reasoning
        """
        # Build prompt for Gemini
        stories_text = "\n\n".join([
            f"Story {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Content: {s['content']}\n"
            f"Source: {s['source']}\n"
            f"Period: {s['period']}\n"
            f"Category: {s['category']}"
            for i, s in enumerate(stories)
        ])

        system_prompt = """You are a historian and storyteller. Your task is to select the most engaging historical story about a location for travelers."""

        user_prompt = f"""Location: {location}

Available stories:
{stories_text}

Select the most interesting story for someone traveling to {location}. Consider:
1. Historical significance
2. Engaging narrative
3. Relevance to modern travelers
4. Educational value
5. Uniqueness and fascination factor

Respond with:
CHOICE: [number 1-{len(stories)}]
REASONING: [brief explanation]"""

        try:
            response = self.gemini.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response
            choice_idx = self._parse_choice(response, len(stories))
            reasoning = self._parse_reasoning(response)

            selected = stories[choice_idx].copy()
            selected["reasoning"] = reasoning

            return selected

        except Exception as e:
            self.logger.warning(f"Gemini selection failed, using first story: {e}")
            selected = stories[0].copy()
            selected["reasoning"] = "Default selection (Gemini unavailable)"
            return selected

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
