"""
Story Agent - Searches for historical stories and facts about locations.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent, AgentTask
from src.services.gemini_client import GeminiClient
from src.services.search_tools import SearchTools
from src.utils.queue_manager import AgentResult
from src.agents.agent_prompts import StoryPrompts
from src.agents.response_parser import parse_choice, parse_score, parse_reasoning
from src.agents.story_filter import filter_and_score_stories


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
        Use Gemini to select the most interesting story with quality filtering.

        Args:
            location: Location name
            stories: List of story dictionaries

        Returns:
            Selected story with reasoning and relevance score
        """
        # Step 1: Filter and score stories for quality and relevance
        filtered_stories = filter_and_score_stories(location, stories)

        if not filtered_stories:
            self.logger.warning("No high-quality stories after filtering, using all stories")
            filtered_stories = [(s, 0) for s in stories]

        # Sort by score (relevance)
        sorted_stories = sorted(filtered_stories, key=lambda x: x[1], reverse=True)
        top_stories = [s[0] for s in sorted_stories[:5]]

        # Build stories text for prompt
        stories_text = "\n\n".join([
            f"Story {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Content: {s['content'][:300]}{'...' if len(s['content']) > 300 else ''}\n"
            f"Source: {s['source']}\n"
            f"Period: {s.get('period', 'N/A')}\n"
            f"Category: {s.get('category', 'N/A')}"
            for i, s in enumerate(top_stories)
        ])

        # Get prompts
        system_prompt = StoryPrompts.SYSTEM
        user_prompt = StoryPrompts.user_prompt(location, stories_text, len(top_stories))

        try:
            response = self.gemini.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response
            choice_idx = parse_choice(response, len(top_stories))
            reasoning = parse_reasoning(response)
            score = parse_score(response)

            selected = top_stories[choice_idx].copy()
            selected["reasoning"] = reasoning
            selected["relevance_score"] = score

            return selected

        except Exception as e:
            self.logger.warning(f"Gemini selection failed, using top-scored story: {e}")
            selected = top_stories[0].copy()
            selected["reasoning"] = "Top-ranked by quality metrics"
            selected["relevance_score"] = sorted_stories[0][1] if sorted_stories else 0
            return selected
