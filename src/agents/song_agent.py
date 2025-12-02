"""
Song Agent - Searches for relevant music about locations.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent, AgentTask
from src.services.gemini_client import GeminiClient
from src.services.search_tools import SearchTools
from src.utils.queue_manager import AgentResult
from src.agents.agent_prompts import SongPrompts
from src.agents.response_parser import parse_choice, parse_score, parse_reasoning
from src.agents.song_filter import filter_and_score_songs


class SongAgent(BaseAgent):
    """
    Agent responsible for finding relevant music/songs for locations.
    Uses Gemini to analyze search results and select the most appropriate song.
    """

    def __init__(self, gemini_client: GeminiClient, search_tools: SearchTools):
        """
        Initialize Song Agent.

        Args:
            gemini_client: Gemini API client
            search_tools: Search utilities
        """
        super().__init__(name="SongAgent", agent_type="song")
        self.gemini = gemini_client
        self.search = search_tools

    def execute(self, task: AgentTask) -> AgentResult:
        """
        Search for and select the best song for a location.

        Args:
            task: AgentTask with location information

        Returns:
            AgentResult with selected song
        """
        self.logger.info(f"Searching music for: {task.address}")

        # Step 1: Search for music
        songs = self.search.search_music(task.address, max_results=5)

        if not songs:
            return self._create_result(
                task=task,
                content={},
                error="No music found"
            )

        # Step 2: Use Gemini to analyze and select best song
        selected_song = self._select_best_song(task.address, songs)

        # Step 3: Create result
        content = {
            "selected": selected_song,
            "candidates": songs,
            "selection_reasoning": selected_song.get("reasoning", "")
        }

        self.logger.info(f"Selected song: {selected_song.get('title', 'N/A')}")

        return self._create_result(task=task, content=content)

    def _select_best_song(
        self,
        location: str,
        songs: list
    ) -> Dict[str, Any]:
        """
        Use Gemini to select the most relevant song with quality filtering.

        Args:
            location: Location name
            songs: List of song dictionaries

        Returns:
            Selected song with reasoning and relevance score
        """
        # Step 1: Filter and score songs for quality and relevance
        filtered_songs = filter_and_score_songs(location, songs)

        if not filtered_songs:
            self.logger.warning("No high-quality songs after filtering, using all songs")
            filtered_songs = [(s, 0) for s in songs]

        # Sort by score (relevance)
        sorted_songs = sorted(filtered_songs, key=lambda x: x[1], reverse=True)
        top_songs = [s[0] for s in sorted_songs[:5]]

        # Build enhanced prompt for Gemini
        songs_text = "\n\n".join([
            f"Song {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Artist: {s['artist']}\n"
            f"Genre: {s['genre']}\n"
            f"Duration: {s.get('duration', 'N/A')}\n"
            f"Album: {s.get('album', 'N/A')}\n"
            f"Year: {s.get('year', 'N/A')}"
            for i, s in enumerate(top_songs)
        ])

        # Get prompts
        system_prompt = SongPrompts.SYSTEM
        user_prompt = SongPrompts.user_prompt(location, songs_text, len(top_songs))

        try:
            response = self.gemini.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response
            choice_idx = parse_choice(response, len(top_songs))
            reasoning = parse_reasoning(response)
            score = parse_score(response)

            selected = top_songs[choice_idx].copy()
            selected["reasoning"] = reasoning
            selected["relevance_score"] = score

            return selected

        except Exception as e:
            self.logger.warning(f"Gemini selection failed, using top-scored song: {e}")
            selected = top_songs[0].copy()
            selected["reasoning"] = "Top-ranked by quality metrics"
            selected["relevance_score"] = sorted_songs[0][1] if sorted_songs else 0
            return selected
