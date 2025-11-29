"""
Unit tests for Song Agent.
"""

import pytest
from unittest.mock import Mock
from src.agents.song_agent import SongAgent


class TestSongAgent:
    """Test suite for SongAgent."""

    def test_initialization(self, mock_gemini_client, mock_search_tools):
        """Test agent initialization."""
        agent = SongAgent(mock_gemini_client, mock_search_tools)

        assert agent.name == "SongAgent"
        assert agent.agent_type == "song"
        assert agent.gemini == mock_gemini_client
        assert agent.search == mock_search_tools

    def test_execute_success(self, mock_gemini_client, mock_search_tools, sample_agent_task, mock_song_results):
        """Test successful song search and selection."""
        mock_search_tools.search_music.return_value = mock_song_results
        mock_gemini_client.simple_query.return_value = "CHOICE: 1\nREASONING: Perfect for NYC"

        agent = SongAgent(mock_gemini_client, mock_search_tools)
        result = agent.execute(sample_agent_task)

        # Verify search was called
        mock_search_tools.search_music.assert_called_once()

        # Verify result structure
        assert result.agent_type == "song"
        assert result.route_id == sample_agent_task.route_id
        assert result.error is None
        assert 'selected' in result.content
        assert 'candidates' in result.content

    def test_execute_no_songs_found(self, mock_gemini_client, mock_search_tools, sample_agent_task):
        """Test behavior when no songs found."""
        mock_search_tools.search_music.return_value = []

        agent = SongAgent(mock_gemini_client, mock_search_tools)
        result = agent.execute(sample_agent_task)

        assert result.error == "No music found"
        assert result.content == {}

    def test_execute_with_claude_failure(self, mock_gemini_client, mock_search_tools, sample_agent_task, mock_song_results):
        """Test fallback when Gemini API fails."""
        mock_search_tools.search_music.return_value = mock_song_results
        mock_gemini_client.simple_query.side_effect = Exception("API timeout")

        agent = SongAgent(mock_gemini_client, mock_search_tools)
        result = agent.execute(sample_agent_task)

        # Should use fallback (top-scored song from filtering)
        assert result.error is None
        # The selected song should be from the candidates
        assert result.content['selected']['title'] in [s['title'] for s in mock_song_results]
        assert 'reasoning' in result.content['selected']
