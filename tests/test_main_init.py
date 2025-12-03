"""Tests for main initialization module."""

import pytest
from unittest.mock import Mock, patch
from src.main_init import initialize_services


class TestInitializeServices:
    """Test service initialization."""

    @patch('src.main_init.Orchestrator')
    @patch('src.main_init.QueueManager')
    @patch('src.main_init.JudgeAgent')
    @patch('src.main_init.StoryAgent')
    @patch('src.main_init.SongAgent')
    @patch('src.main_init.VideoAgent')
    @patch('src.main_init.SearchTools')
    @patch('src.main_init.GeminiClient')
    @patch('src.main_init.GoogleMapsService')
    @patch('src.main_init.setup_logger')
    def test_initialize_services_success(
        self,
        mock_logger_setup,
        mock_maps,
        mock_gemini,
        mock_search,
        mock_video,
        mock_song,
        mock_story,
        mock_judge,
        mock_queue,
        mock_orch
    ):
        """Test successful service initialization."""
        # Setup mocks
        mock_logger = Mock()
        mock_logger_setup.return_value = mock_logger

        settings = Mock(
            google_maps_api_key="test_maps_key",
            gemini_api_key="test_gemini_key",
            gemini_model="gemini-pro",
            gemini_max_tokens=1000,
            gemini_temperature=0.7,
            logs_dir="logs"
        )

        # Execute
        result = initialize_services(settings, "INFO")

        # Verify all services initialized
        mock_logger_setup.assert_called_once_with(
            log_level="INFO",
            log_dir="logs",
            enable_console=True,
            enable_file=True
        )
        mock_maps.assert_called_once_with("test_maps_key")
        mock_gemini.assert_called_once_with(
            api_key="test_gemini_key",
            model="gemini-pro",
            max_tokens=1000,
            temperature=0.7
        )
        mock_search.assert_called_once()

        # Verify agents initialized
        mock_video.assert_called_once()
        mock_song.assert_called_once()
        mock_story.assert_called_once()
        mock_judge.assert_called_once()

        # Verify queue manager initialized
        mock_queue.assert_called_once()

        # Verify orchestrator initialized
        mock_orch.assert_called_once()

        # Verify return dictionary
        assert 'logger' in result
        assert 'google_maps' in result
        assert 'orchestrator' in result
        assert 'queue_manager' in result
        assert result['logger'] == mock_logger

    @patch('src.main_init.Orchestrator')
    @patch('src.main_init.QueueManager')
    @patch('src.main_init.JudgeAgent')
    @patch('src.main_init.StoryAgent')
    @patch('src.main_init.SongAgent')
    @patch('src.main_init.VideoAgent')
    @patch('src.main_init.SearchTools')
    @patch('src.main_init.GeminiClient')
    @patch('src.main_init.GoogleMapsService')
    @patch('src.main_init.setup_logger')
    def test_initialize_services_logging_calls(
        self,
        mock_logger_setup,
        mock_maps,
        mock_gemini,
        mock_search,
        mock_video,
        mock_song,
        mock_story,
        mock_judge,
        mock_queue,
        mock_orch
    ):
        """Test that initialization logs appropriate messages."""
        mock_logger = Mock()
        mock_logger_setup.return_value = mock_logger

        settings = Mock(
            google_maps_api_key="key",
            gemini_api_key="key",
            gemini_model="model",
            gemini_max_tokens=100,
            gemini_temperature=0.5,
            logs_dir="logs"
        )

        initialize_services(settings, "DEBUG")

        # Verify logger was called with startup messages
        assert mock_logger.info.call_count >= 3
        calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Route Stories" in call for call in calls)
        assert any("services" in call.lower() for call in calls)
        assert any("agents" in call.lower() for call in calls)
