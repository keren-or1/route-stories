"""
Unit tests for Orchestrator.
"""

import pytest
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor
from core.orchestrator import Orchestrator
from agents.base_agent import AgentTask
from utils.queue_manager import AgentResult, QueueManager


class TestOrchestrator:
    """Test suite for Orchestrator."""

    def test_initialization(self):
        """Test orchestrator initialization."""
        mock_agents = {
            'video': Mock(),
            'song': Mock(),
            'story': Mock(),
            'judge': Mock()
        }
        mock_queue = Mock(spec=QueueManager)

        orchestrator = Orchestrator(
            video_agent=mock_agents['video'],
            song_agent=mock_agents['song'],
            story_agent=mock_agents['story'],
            judge_agent=mock_agents['judge'],
            queue_manager=mock_queue
        )

        assert orchestrator.video_agent == mock_agents['video']
        assert orchestrator.song_agent == mock_agents['song']
        assert orchestrator.story_agent == mock_agents['story']
        assert orchestrator.judge_agent == mock_agents['judge']
        assert orchestrator.queue == mock_queue

    def test_process_waypoint_success(self, sample_agent_task, sample_agent_result):
        """Test successful waypoint processing with all agents."""
        # Setup mock agents
        mock_video = Mock()
        mock_video.run.return_value = sample_agent_result

        mock_song = Mock()
        mock_song.run.return_value = sample_agent_result

        mock_story = Mock()
        mock_story.run.return_value = sample_agent_result

        mock_judge = Mock()
        judge_result = sample_agent_result
        judge_result.agent_type = 'judge'
        mock_judge.run.return_value = judge_result

        mock_queue = Mock(spec=QueueManager)
        mock_queue.get_results_for_point.return_value = [
            sample_agent_result,
            sample_agent_result,
            sample_agent_result
        ]

        orchestrator = Orchestrator(
            video_agent=mock_video,
            song_agent=mock_song,
            story_agent=mock_story,
            judge_agent=mock_judge,
            queue_manager=mock_queue
        )

        result = orchestrator.process_waypoint(sample_agent_task)

        # Verify all content agents were called
        mock_video.run.assert_called_once_with(sample_agent_task)
        mock_song.run.assert_called_once_with(sample_agent_task)
        mock_story.run.assert_called_once_with(sample_agent_task)

        # Verify results added to queue
        assert mock_queue.add_result.call_count >= 3

        # Verify judge was called
        mock_judge.run.assert_called_once()

        # Verify return value is judge result
        assert result.agent_type == 'judge'

    def test_process_waypoint_with_agent_failure(self, sample_agent_task, sample_agent_result, sample_error_result):
        """Test waypoint processing when one agent fails."""
        # Video agent succeeds
        mock_video = Mock()
        mock_video.run.return_value = sample_agent_result

        # Song agent fails
        mock_song = Mock()
        mock_song.run.return_value = sample_error_result

        # Story agent succeeds
        mock_story = Mock()
        mock_story.run.return_value = sample_agent_result

        mock_judge = Mock()
        judge_result = sample_agent_result
        judge_result.agent_type = 'judge'
        mock_judge.run.return_value = judge_result

        mock_queue = Mock(spec=QueueManager)
        mock_queue.get_results_for_point.return_value = [
            sample_agent_result,
            sample_error_result,
            sample_agent_result
        ]

        orchestrator = Orchestrator(
            video_agent=mock_video,
            song_agent=mock_song,
            story_agent=mock_story,
            judge_agent=mock_judge,
            queue_manager=mock_queue
        )

        result = orchestrator.process_waypoint(sample_agent_task)

        # Should still complete and call judge
        mock_judge.run.assert_called_once()
        assert result.agent_type == 'judge'

    def test_process_waypoint_timeout_handling(self, sample_agent_task):
        """Test timeout handling for slow agents."""
        # Create agents that simulate slow execution
        import time

        def slow_agent_run(task):
            time.sleep(0.1)  # Simulate work
            return sample_agent_result

        mock_video = Mock()
        mock_video.run = slow_agent_run

        mock_song = Mock()
        mock_song.run = slow_agent_run

        mock_story = Mock()
        mock_story.run = slow_agent_run

        mock_judge = Mock()
        mock_judge.run.return_value = sample_agent_result

        mock_queue = Mock(spec=QueueManager)

        orchestrator = Orchestrator(
            video_agent=mock_video,
            song_agent=mock_song,
            story_agent=mock_story,
            judge_agent=mock_judge,
            queue_manager=mock_queue,
            timeout=5  # Reasonable timeout
        )

        # Should complete within timeout
        result = orchestrator.process_waypoint(sample_agent_task)
        assert result is not None

    def test_parallel_execution(self, sample_agent_task, sample_agent_result):
        """Test that content agents run in parallel."""
        import threading
        execution_times = []

        def timed_run(task):
            import time
            start = time.time()
            time.sleep(0.05)  # Simulate work
            execution_times.append((threading.current_thread().name, time.time() - start))
            return sample_agent_result

        mock_video = Mock()
        mock_video.run = timed_run

        mock_song = Mock()
        mock_song.run = timed_run

        mock_story = Mock()
        mock_story.run = timed_run

        mock_judge = Mock()
        mock_judge.run.return_value = sample_agent_result

        mock_queue = Mock(spec=QueueManager)
        mock_queue.get_results_for_point.return_value = [
            sample_agent_result,
            sample_agent_result,
            sample_agent_result
        ]

        orchestrator = Orchestrator(
            video_agent=mock_video,
            song_agent=mock_song,
            story_agent=mock_story,
            judge_agent=mock_judge,
            queue_manager=mock_queue
        )

        import time
        start_time = time.time()
        result = orchestrator.process_waypoint(sample_agent_task)
        total_time = time.time() - start_time

        # If sequential, would take 0.15+ seconds
        # If parallel, should take ~0.05 seconds
        # Allow some overhead, assert < 0.12 seconds
        assert total_time < 0.12, "Agents appear to be running sequentially, not in parallel"
