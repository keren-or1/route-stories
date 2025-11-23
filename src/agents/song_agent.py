"""
Song Agent - Searches for relevant music about locations.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent, AgentTask
from src.services.claude_client import ClaudeClient
from src.services.search_tools import SearchTools
from src.utils.queue_manager import AgentResult


class SongAgent(BaseAgent):
    """
    Agent responsible for finding relevant music/songs for locations.
    Uses Claude to analyze search results and select the most appropriate song.
    """

    def __init__(self, claude_client: ClaudeClient, search_tools: SearchTools):
        """
        Initialize Song Agent.

        Args:
            claude_client: Claude API client
            search_tools: Search utilities
        """
        super().__init__(name="SongAgent", agent_type="song")
        self.claude = claude_client
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

        # Step 2: Use Claude to analyze and select best song
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
        Use Claude to select the most relevant song.

        Args:
            location: Location name
            songs: List of song dictionaries

        Returns:
            Selected song with reasoning
        """
        # Build prompt for Claude
        songs_text = "\n\n".join([
            f"Song {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Artist: {s['artist']}\n"
            f"Genre: {s['genre']}\n"
            f"Duration: {s['duration']}\n"
            f"Album: {s['album']}"
            for i, s in enumerate(songs)
        ])

        system_prompt = """You are a music curator for travel experiences. Your task is to select the most fitting song about a location for travelers."""

        user_prompt = f"""Location: {location}

Available songs:
{songs_text}

Select the best song for someone traveling to {location}. Consider:
1. Lyrical relevance to the location
2. Cultural authenticity
3. Mood and atmosphere
4. Artistic quality

Respond with:
CHOICE: [number 1-{len(songs)}]
REASONING: [brief explanation]"""

        try:
            response = self.claude.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response
            choice_idx = self._parse_choice(response, len(songs))
            reasoning = self._parse_reasoning(response)

            selected = songs[choice_idx].copy()
            selected["reasoning"] = reasoning

            return selected

        except Exception as e:
            self.logger.warning(f"Claude selection failed, using first song: {e}")
            selected = songs[0].copy()
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
