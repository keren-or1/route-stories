"""
Unit tests for Judge Agent.
"""

import pytest
from unittest.mock import Mock
from agents.judge_agent import JudgeAgent


class TestJudgeAgent:
    """Test suite for JudgeAgent."""

    def test_initialization(self, mock_claude_client):
        """Test agent initialization."""
        agent = JudgeAgent(mock_claude_client)

        assert agent.name == "JudgeAgent"
        assert agent.agent_type == "judge"
        assert agent.claude == mock_claude_client

    def test_execute_with_all_options(self, mock_claude_client, sample_agent_task, sample_agent_result):
        """Test judge evaluation with all three content types."""
        # Mock three content options
        video_result = sample_agent_result
        video_result.agent_type = 'video'
        video_result.content = {'selected': {'title': 'Test Video'}}

        song_result = sample_agent_result
        song_result.agent_type = 'song'
        song_result.content = {'selected': {'title': 'Test Song'}}

        story_result = sample_agent_result
        story_result.agent_type = 'story'
        story_result.content = {'selected': {'title': 'Test Story'}}

        results = [video_result, song_result, story_result]

        mock_claude_client.structured_query.return_value = {
            'selected': 'video',
            'reasoning': 'Most visually engaging',
            'scores': {'video': 9.0, 'song': 7.5, 'story': 8.0},
            'confidence': 85
        }

        agent = JudgeAgent(mock_claude_client)

        # Create task with context containing results
        task = sample_agent_task
        task.context = {'agent_results': results}

        result = agent.execute(task)

        # Verify Claude was called
        mock_claude_client.structured_query.assert_called_once()

        # Verify result structure
        assert result.agent_type == "judge"
        assert result.error is None
        assert 'decision' in result.content
        assert result.content['decision']['selected'] == 'video'
        assert 'reasoning' in result.content['decision']
        assert 'scores' in result.content['decision']

    def test_execute_missing_content_option(self, mock_claude_client, sample_agent_task, sample_agent_result):
        """Test judge handling when one content type is missing."""
        # Only provide video and song, no story
        video_result = sample_agent_result
        video_result.agent_type = 'video'

        song_result = sample_agent_result
        song_result.agent_type = 'song'

        results = [video_result, song_result]

        mock_claude_client.structured_query.return_value = {
            'selected': 'video',
            'reasoning': 'Best of available options',
            'scores': {'video': 8.0, 'song': 7.0},
            'confidence': 75
        }

        agent = JudgeAgent(mock_claude_client)

        task = sample_agent_task
        task.context = {'agent_results': results}

        result = agent.execute(task)

        # Should still work with partial results
        assert result.error is None
        assert 'decision' in result.content

    def test_execute_with_error_results(self, mock_claude_client, sample_agent_task, sample_error_result):
        """Test judge handling error results from content agents."""
        # All agents returned errors
        video_error = sample_error_result
        video_error.agent_type = 'video'

        song_error = sample_error_result
        song_error.agent_type = 'song'

        story_error = sample_error_result
        story_error.agent_type = 'story'

        results = [video_error, song_error, story_error]

        agent = JudgeAgent(mock_claude_client)

        task = sample_agent_task
        task.context = {'agent_results': results}

        result = agent.execute(task)

        # Should return error when no valid content available
        assert result.error is not None
        assert "No valid content" in result.error or "all agents failed" in result.error.lower()

    def test_execute_claude_failure(self, mock_claude_client, sample_agent_task, sample_agent_result):
        """Test fallback when Claude API fails."""
        video_result = sample_agent_result
        video_result.agent_type = 'video'

        song_result = sample_agent_result
        song_result.agent_type = 'song'

        results = [video_result, song_result]

        # Simulate Claude failure
        mock_claude_client.structured_query.side_effect = Exception("API Error")

        agent = JudgeAgent(mock_claude_client)

        task = sample_agent_task
        task.context = {'agent_results': results}

        result = agent.execute(task)

        # Should return error result
        assert result.error is not None
        assert "API Error" in result.error or "failed" in result.error.lower()
