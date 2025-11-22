"""
Unit tests for Story Agent.
"""

import pytest
from unittest.mock import Mock
from agents.story_agent import StoryAgent


class TestStoryAgent:
    """Test suite for StoryAgent."""

    def test_initialization(self, mock_claude_client, mock_search_tools):
        """Test agent initialization."""
        agent = StoryAgent(mock_claude_client, mock_search_tools)

        assert agent.name == "StoryAgent"
        assert agent.agent_type == "story"
        assert agent.claude == mock_claude_client
        assert agent.search == mock_search_tools

    def test_execute_success(self, mock_claude_client, mock_search_tools, sample_agent_task, mock_story_results):
        """Test successful story search and selection."""
        mock_search_tools.search_stories.return_value = mock_story_results
        mock_claude_client.simple_query.return_value = "CHOICE: 1\nREASONING: Most interesting historical fact"

        agent = StoryAgent(mock_claude_client, mock_search_tools)
        result = agent.execute(sample_agent_task)

        # Verify search was called
        mock_search_tools.search_stories.assert_called_once()

        # Verify result structure
        assert result.agent_type == "story"
        assert result.route_id == sample_agent_task.route_id
        assert result.error is None
        assert 'selected' in result.content
        assert 'candidates' in result.content

    def test_execute_no_stories_found(self, mock_claude_client, mock_search_tools, sample_agent_task):
        """Test behavior when no stories found."""
        mock_search_tools.search_stories.return_value = []

        agent = StoryAgent(mock_claude_client, mock_search_tools)
        result = agent.execute(sample_agent_task)

        assert result.error == "No stories found"
        assert result.content == {}

    def test_run_with_exception(self, mock_claude_client, mock_search_tools, sample_agent_task):
        """Test error handling in run method."""
        mock_search_tools.search_stories.side_effect = ValueError("Invalid input")

        agent = StoryAgent(mock_claude_client, mock_search_tools)
        result = agent.run(sample_agent_task)

        # Should return error result, not crash
        assert result.error is not None
        assert "Invalid input" in result.error
