"""
Unit tests for Video Agent.
"""

import pytest
from unittest.mock import Mock, patch
from src.agents.video_agent import VideoAgent
from src.agents.base_agent import AgentTask


class TestVideoAgent:
    """Test suite for VideoAgent."""

    def test_initialization(self, mock_gemini_client, mock_search_tools):
        """Test agent initialization."""
        agent = VideoAgent(mock_gemini_client, mock_search_tools)

        assert agent.name == "VideoAgent"
        assert agent.agent_type == "video"
        assert agent.gemini == mock_gemini_client
        assert agent.search == mock_search_tools

    def test_execute_success(self, mock_gemini_client, mock_search_tools, sample_agent_task, mock_video_results):
        """Test successful video search and selection."""
        mock_search_tools.search_youtube_videos.return_value = mock_video_results
        mock_gemini_client.simple_query.return_value = "CHOICE: 1\nREASONING: Most informative video"

        agent = VideoAgent(mock_gemini_client, mock_search_tools)
        result = agent.execute(sample_agent_task)

        # Verify search was called
        mock_search_tools.search_youtube_videos.assert_called_once_with(
            sample_agent_task.address,
            max_results=5
        )

        # Verify result structure
        assert result.agent_type == "video"
        assert result.route_id == sample_agent_task.route_id
        assert result.point_id == sample_agent_task.point_id
        assert result.error is None
        assert 'selected' in result.content
        assert 'candidates' in result.content
        assert 'selection_reasoning' in result.content

    def test_execute_no_videos_found(self, mock_gemini_client, mock_search_tools, sample_agent_task):
        """Test behavior when no videos found."""
        mock_search_tools.search_youtube_videos.return_value = []

        agent = VideoAgent(mock_gemini_client, mock_search_tools)
        result = agent.execute(sample_agent_task)

        assert result.error == "No videos found"
        assert result.content == {}

    def test_execute_gemini_failure_fallback(self, mock_gemini_client, mock_search_tools, sample_agent_task, mock_video_results):
        """Test fallback to first video when Gemini fails."""
        mock_search_tools.search_youtube_videos.return_value = mock_video_results
        mock_gemini_client.simple_query.side_effect = Exception("API Error")

        agent = VideoAgent(mock_gemini_client, mock_search_tools)
        result = agent.execute(sample_agent_task)

        # Should still return a result, using first video
        assert result.error is None
        assert result.content['selected']['title'] == mock_video_results[0]['title']
        assert 'Default selection' in result.content['selected']['reasoning']

    def test_parse_choice_valid(self, mock_gemini_client, mock_search_tools):
        """Test parsing valid choice from Gemini response."""
        agent = VideoAgent(mock_gemini_client, mock_search_tools)

        response = "CHOICE: 2\nREASONING: Best option"
        choice = agent._parse_choice(response, max_options=3)

        assert choice == 1  # 2 - 1 = index 1

    def test_parse_choice_out_of_bounds(self, mock_gemini_client, mock_search_tools):
        """Test parsing choice that exceeds max options."""
        agent = VideoAgent(mock_gemini_client, mock_search_tools)

        response = "CHOICE: 10\nREASONING: Something"
        choice = agent._parse_choice(response, max_options=3)

        assert choice == 2  # Capped at max_options - 1

    def test_parse_choice_invalid_format(self, mock_gemini_client, mock_search_tools):
        """Test parsing invalid choice format."""
        agent = VideoAgent(mock_gemini_client, mock_search_tools)

        response = "CHOICE: invalid\nREASONING: Something"
        choice = agent._parse_choice(response, max_options=3)

        assert choice == 0  # Default to first option

    def test_parse_reasoning_valid(self, mock_gemini_client, mock_search_tools):
        """Test parsing reasoning from response."""
        agent = VideoAgent(mock_gemini_client, mock_search_tools)

        response = "CHOICE: 1\nREASONING: This is the best video because..."
        reasoning = agent._parse_reasoning(response)

        assert reasoning == "This is the best video because..."

    def test_parse_reasoning_missing(self, mock_gemini_client, mock_search_tools):
        """Test parsing when reasoning is missing."""
        agent = VideoAgent(mock_gemini_client, mock_search_tools)

        response = "CHOICE: 1"
        reasoning = agent._parse_reasoning(response)

        assert reasoning == "No reasoning provided"

    def test_run_with_error_handling(self, mock_gemini_client, mock_search_tools, sample_agent_task):
        """Test run method with error handling."""
        mock_search_tools.search_youtube_videos.side_effect = Exception("Network error")

        agent = VideoAgent(mock_gemini_client, mock_search_tools)
        result = agent.run(sample_agent_task)

        # Should return error result, not raise exception
        assert result.error is not None
        assert "Network error" in result.error
        assert result.route_id == sample_agent_task.route_id
