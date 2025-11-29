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
        Use Gemini to select the most interesting story with quality filtering.

        Args:
            location: Location name
            stories: List of story dictionaries

        Returns:
            Selected story with reasoning and relevance score
        """
        # Step 1: Filter and score stories for quality and relevance
        filtered_stories = self._filter_and_score_stories(location, stories)

        if not filtered_stories:
            self.logger.warning("No high-quality stories after filtering, using all stories")
            filtered_stories = [(s, 0) for s in stories]

        # Sort by score (relevance)
        sorted_stories = sorted(filtered_stories, key=lambda x: x[1], reverse=True)
        top_stories = [s[0] for s in sorted_stories[:5]]

        # Truncate long stories for the prompt
        stories_text = "\n\n".join([
            f"Story {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Content: {s['content'][:300]}{'...' if len(s['content']) > 300 else ''}\n"
            f"Source: {s['source']}\n"
            f"Period: {s.get('period', 'N/A')}\n"
            f"Category: {s.get('category', 'N/A')}"
            for i, s in enumerate(top_stories)
        ])

        system_prompt = """You are a renowned historian and storyteller specializing in travel experiences.
Select the MOST CAPTIVATING story that will enrich a traveler's visit to a specific location.
Prioritize stories that:
- Directly relate to and illuminate the location
- Have compelling emotional or historical weight
- Are accurate and from reliable sources
- Offer unique cultural insights
- Create a memorable learning moment"""

        user_prompt = f"""Location: {location}

Available stories (pre-filtered for quality):
{stories_text}

Select the SINGLE BEST story for someone visiting {location}. The ideal story should:
1. Be directly connected to {location} 's history or culture
2. Have engaging narrative quality that captures imagination
3. Offer educational value and cultural insight
4. Be relevant and interesting to modern travelers
5. Feel like a "must-know" fact about the location

IMPORTANT: Explain why this particular story makes the visit more meaningful.

Respond in exactly this format:
CHOICE: [number 1-{len(top_stories)}]
SCORE: [relevance score 0-100]
REASONING: [one sentence on why this story deepens understanding of the location]"""

        try:
            response = self.gemini.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response
            choice_idx = self._parse_choice(response, len(top_stories))
            reasoning = self._parse_reasoning(response)
            score = self._parse_score(response)

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

    def _filter_and_score_stories(self, location: str, stories: list) -> list:
        """
        Filter out low-quality stories and score remaining ones by relevance.

        Args:
            location: Location name
            stories: List of story dictionaries

        Returns:
            List of (story, score) tuples, filtered and scored
        """
        scored_stories = []
        location_lower = location.lower()

        for story in stories:
            # Extract metadata
            title = story.get('title', '').lower()
            content = story.get('content', '').lower()
            source = story.get('source', '').lower()
            period = story.get('period', '')
            category = story.get('category', '').lower()

            # Filter: Reject Google/tech product help articles (not location-relevant)
            irrelevant_help_patterns = [
                'how to stop sharing',
                'how to turn off',
                'google maps help',
                'google support',
                'android settings',
                'iphone settings',
                'app settings',
                'technical support',
                'troubleshoot',
            ]

            is_irrelevant_help = any(pattern in content for pattern in irrelevant_help_patterns)
            is_about_google_product_not_location = (
                any(keyword in content for keyword in ['google maps', 'google help', 'app feature', 'phone settings']) and
                location_lower not in content[:300]
            )

            if is_irrelevant_help or is_about_google_product_not_location:
                self.logger.debug(f"Filtering out irrelevant article: {title[:50]}")
                continue  # Skip this story entirely

            # Initialize score
            score = 50  # Base score

            # Location relevance (highest priority)
            if location_lower in title:
                score += 25
            elif location_lower in content[:200]:  # Check first part of content
                score += 20

            # Content quality (length indicates depth)
            content_text = story.get('content', '')
            if len(content_text) > 500:
                score += 10
            elif len(content_text) > 200:
                score += 5

            # Category appropriateness for travelers
            interesting_categories = ['history', 'culture', 'landmark', 'architecture', 'art', 'famous', 'notable']
            for cat in interesting_categories:
                if cat in category:
                    score += 8
                    break

            # Source credibility
            trusted_sources = ['wikipedia', 'bbc', 'national geographic', 'history', 'britannica', 'government']
            for trusted in trusted_sources:
                if trusted in source:
                    score += 10
                    break

            # Avoid low-quality sources
            poor_sources = ['random', 'unknown', 'unverified']
            for poor in poor_sources:
                if poor in source:
                    score -= 15

            # Historical significance markers in content
            significant_keywords = ['ancient', 'historic', 'founded', 'built', 'established', 'famous', 'renowned', 'important']
            for keyword in significant_keywords:
                if keyword in content[:200]:
                    score += 3

            # Period boost for well-documented historical periods
            if period and period.lower() in ['ancient', 'medieval', 'renaissance', 'colonial', 'modern']:
                score += 5

            # Minimum quality filter
            if score >= 40 and len(content_text) >= 50:  # Must have meaningful content
                scored_stories.append((story, score))

        return scored_stories

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
