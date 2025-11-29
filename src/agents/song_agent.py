"""
Song Agent - Searches for relevant music about locations.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent, AgentTask
from src.services.gemini_client import GeminiClient
from src.services.search_tools import SearchTools
from src.utils.queue_manager import AgentResult


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
        filtered_songs = self._filter_and_score_songs(location, songs)

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

        system_prompt = """You are an expert music curator for travel experiences.
Select the MOST FITTING song to enhance the travel experience at a specific location.
Prioritize songs that:
- Directly reference or relate to the location
- Capture the cultural essence and mood
- Have artistic merit and broad appeal
- Create an emotional connection with travelers"""

        user_prompt = f"""Location: {location}

Available songs (pre-filtered for quality):
{songs_text}

Select the SINGLE BEST song for someone traveling to {location}. Optimal choices have:
1. Direct or meaningful reference to {location}
2. Authentic cultural connection to the location
3. High production quality and mainstream appeal
4. Appropriate musical mood (not too heavy, engaging)
5. Reasonable song length (3-5 minutes ideal)

IMPORTANT: Explain why THIS song will enhance the travel experience.

Respond in exactly this format:
CHOICE: [number 1-{len(top_songs)}]
SCORE: [relevance score 0-100]
REASONING: [one sentence about how this song captures the location]"""

        try:
            response = self.gemini.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )

            # Parse response
            choice_idx = self._parse_choice(response, len(top_songs))
            reasoning = self._parse_reasoning(response)
            score = self._parse_score(response)

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

    def _filter_and_score_songs(self, location: str, songs: list) -> list:
        """
        Filter out low-quality songs and score remaining ones by relevance.

        Args:
            location: Location name
            songs: List of song dictionaries

        Returns:
            List of (song, score) tuples, filtered and scored
        """
        scored_songs = []
        location_lower = location.lower()

        for song in songs:
            # Extract metadata
            title = song.get('title', '').lower()
            artist = song.get('artist', '').lower()
            genre = song.get('genre', '').lower()
            album = song.get('album', '').lower()

            # Initialize score
            score = 50  # Base score

            # Location/place relevance (highest priority)
            if location_lower in title:
                score += 25
            elif location_lower in artist:
                score += 10
            elif location_lower in album:
                score += 15

            # Genre appropriateness for travel
            travel_friendly_genres = ['pop', 'indie', 'world', 'folk', 'acoustic', 'alternative', 'rock']
            for friendly_genre in travel_friendly_genres:
                if friendly_genre in genre:
                    score += 8
                    break

            # Avoid overly niche or heavy genres
            heavy_genres = ['death', 'thrash', 'black metal', 'harsh', 'extreme']
            for heavy_genre in heavy_genres:
                if heavy_genre in genre:
                    score -= 20

            # Production quality indicators
            if 'official' in title.lower() or 'official' in artist.lower():
                score += 5

            # Duration preference (3-5 minutes is ideal for travel playlists)
            duration = song.get('duration', '')
            if duration:
                try:
                    if ':' in str(duration):
                        parts = str(duration).split(':')
                        if len(parts) == 2:
                            mins = int(parts[0])
                            if 3 <= mins <= 5:
                                score += 10
                            elif 2 <= mins <= 7:
                                score += 5
                except:
                    pass

            # Recency bonus for contemporary music
            year = song.get('year')
            if year:
                try:
                    year_int = int(year)
                    if 2020 <= year_int <= 2024:
                        score += 5
                except:
                    pass

            # Minimum quality filter
            if score >= 40:
                scored_songs.append((song, score))

        return scored_songs

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
