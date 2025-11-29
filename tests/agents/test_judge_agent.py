"""
Unit tests for Judge Agent.
"""

import pytest
from unittest.mock import Mock
from src.agents.judge_agent import JudgeAgent


class TestJudgeAgent:
    """Test suite for JudgeAgent."""

    def test_initialization(self, mock_gemini_client):
        """Test agent initialization."""
        agent = JudgeAgent(mock_gemini_client)

        assert agent.name == "JudgeAgent"
        assert agent.agent_type == "judge"
        assert agent.gemini == mock_gemini_client

    def test_execute_with_all_options(self, mock_gemini_client, sample_agent_task):
        """Test judge evaluation with all three content types."""
        from src.utils.queue_manager import AgentResult
        from datetime import datetime

        # Create three content results
        video_result = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='video',
            content={'selected': {'title': 'Test Video', 'duration': '10:00', 'channel': 'Test'}},
            timestamp=datetime.now(),
            error=None
        )

        song_result = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='song',
            content={'selected': {'title': 'Test Song', 'artist': 'Test', 'genre': 'Pop'}},
            timestamp=datetime.now(),
            error=None
        )

        story_result = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='story',
            content={'selected': {'title': 'Test Story', 'content': 'Story text', 'period': 'Modern'}},
            timestamp=datetime.now(),
            error=None
        )

        # Mock Gemini response
        mock_gemini_client.simple_query.return_value = "CHOICE: 1\nSCORE: 85\nREASONING: Most visually engaging"

        agent = JudgeAgent(mock_gemini_client)

        # Create task with context containing results
        task = sample_agent_task
        task.context = {'content_results': {
            'video': video_result,
            'song': song_result,
            'story': story_result
        }}

        result = agent.execute(task)

        # Verify Gemini was called
        mock_gemini_client.simple_query.assert_called_once()

        # Verify result structure
        assert result.agent_type == "judge"
        assert result.error is None
        assert 'chosen_type' in result.content
        assert result.content['chosen_type'] == 'video'
        assert 'reasoning' in result.content
        assert 'score' in result.content

    def test_execute_missing_content_option(self, mock_gemini_client, sample_agent_task):
        """Test judge handling when one content type is missing."""
        from src.utils.queue_manager import AgentResult
        from datetime import datetime

        # Only provide video and song, no story
        video_result = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='video',
            content={'selected': {'title': 'Test Video'}},
            timestamp=datetime.now(),
            error=None
        )

        song_result = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='song',
            content={'selected': {'title': 'Test Song'}},
            timestamp=datetime.now(),
            error=None
        )

        mock_gemini_client.simple_query.return_value = "CHOICE: 1\nSCORE: 75\nREASONING: Best of available options"

        agent = JudgeAgent(mock_gemini_client)

        task = sample_agent_task
        task.context = {'content_results': {
            'video': video_result,
            'song': song_result
        }}

        result = agent.execute(task)

        # Should still work with partial results
        assert result.error is None
        assert 'chosen_type' in result.content

    def test_execute_with_error_results(self, mock_gemini_client, sample_agent_task):
        """Test judge handling error results from content agents."""
        from src.utils.queue_manager import AgentResult
        from datetime import datetime

        # All agents returned errors
        video_error = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='video',
            content={},
            timestamp=datetime.now(),
            error='Video search failed'
        )

        song_error = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='song',
            content={},
            timestamp=datetime.now(),
            error='Song search failed'
        )

        story_error = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='story',
            content={},
            timestamp=datetime.now(),
            error='Story search failed'
        )

        agent = JudgeAgent(mock_gemini_client)

        task = sample_agent_task
        task.context = {'content_results': {
            'video': video_error,
            'song': song_error,
            'story': story_error
        }}

        result = agent.execute(task)

        # Should return error when no valid content available
        assert result.error is not None
        assert "No valid options" in result.error or "No valid content" in result.error

    def test_execute_claude_failure(self, mock_gemini_client, sample_agent_task):
        """Test fallback when Gemini API fails."""
        from src.utils.queue_manager import AgentResult
        from datetime import datetime

        video_result = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='video',
            content={'selected': {'title': 'Test Video'}},
            timestamp=datetime.now(),
            error=None
        )

        song_result = AgentResult(
            route_id=sample_agent_task.route_id,
            point_id=sample_agent_task.point_id,
            agent_type='song',
            content={'selected': {'title': 'Test Song'}},
            timestamp=datetime.now(),
            error=None
        )

        # Simulate Gemini failure
        mock_gemini_client.simple_query.side_effect = Exception("API Error")

        agent = JudgeAgent(mock_gemini_client)

        task = sample_agent_task
        task.context = {'content_results': {
            'video': video_result,
            'song': song_result
        }}

        result = agent.execute(task)

        # Should still return a result with fallback logic
        assert result.error is None  # Fallback should make it succeed
        assert 'chosen_type' in result.content
        assert result.content['reasoning'] == "Default selection (Gemini unavailable)"
