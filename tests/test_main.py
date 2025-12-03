"""Tests for main application entry point."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from src.main import parse_arguments, main


class TestParseArguments:
    """Test command-line argument parsing."""

    def test_parse_arguments_no_args(self):
        """Test parsing with no arguments."""
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()
            assert args.start is None
            assert args.end is None
            assert args.max_points is None
            assert args.verbose is False
            assert args.export is None

    def test_parse_arguments_with_start_end(self):
        """Test parsing with start and end locations."""
        with patch('sys.argv', ['main.py', '--start', 'Tel Aviv', '--end', 'Jerusalem']):
            args = parse_arguments()
            assert args.start == 'Tel Aviv'
            assert args.end == 'Jerusalem'

    def test_parse_arguments_with_max_points(self):
        """Test parsing with max points."""
        with patch('sys.argv', ['main.py', '--max-points', '5']):
            args = parse_arguments()
            assert args.max_points == 5

    def test_parse_arguments_with_verbose(self):
        """Test parsing with verbose flag."""
        with patch('sys.argv', ['main.py', '--verbose']):
            args = parse_arguments()
            assert args.verbose is True

    def test_parse_arguments_with_export(self):
        """Test parsing with export path."""
        with patch('sys.argv', ['main.py', '--export', 'output.json']):
            args = parse_arguments()
            assert args.export == 'output.json'

    def test_parse_arguments_all_options(self):
        """Test parsing with all options."""
        with patch('sys.argv', [
            'main.py',
            '--start', 'A',
            '--end', 'B',
            '--max-points', '3',
            '--verbose',
            '--export', 'results.json'
        ]):
            args = parse_arguments()
            assert args.start == 'A'
            assert args.end == 'B'
            assert args.max_points == 3
            assert args.verbose is True
            assert args.export == 'results.json'


class TestMain:
    """Test main application function."""

    @patch('src.main.run_application')
    @patch('src.main.initialize_services')
    @patch('src.main.get_settings')
    @patch('src.main.parse_arguments')
    def test_main_success(self, mock_parse, mock_settings, mock_init, mock_run):
        """Test successful main execution."""
        # Setup mocks
        mock_args = Mock(verbose=False)
        mock_parse.return_value = mock_args

        mock_config = Mock(log_level="INFO")
        mock_settings.return_value = mock_config

        mock_services = {'logger': Mock()}
        mock_init.return_value = mock_services

        # Execute
        main()

        # Verify
        mock_parse.assert_called_once()
        mock_settings.assert_called_once()
        mock_init.assert_called_once_with(mock_config, "INFO")
        mock_run.assert_called_once_with(mock_services, mock_args, mock_config)

    @patch('src.main.get_settings')
    @patch('src.main.parse_arguments')
    def test_main_config_error(self, mock_parse, mock_settings):
        """Test main with configuration error."""
        mock_parse.return_value = Mock()
        mock_settings.side_effect = Exception("Config error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch('src.main.run_application')
    @patch('src.main.initialize_services')
    @patch('src.main.get_settings')
    @patch('src.main.parse_arguments')
    def test_main_keyboard_interrupt(self, mock_parse, mock_settings, mock_init, mock_run):
        """Test main with keyboard interrupt."""
        mock_parse.return_value = Mock(verbose=False)
        mock_settings.return_value = Mock(log_level="INFO")
        mock_services = {'logger': Mock()}
        mock_init.return_value = mock_services
        mock_run.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch('src.main.run_application')
    @patch('src.main.initialize_services')
    @patch('src.main.get_settings')
    @patch('src.main.parse_arguments')
    def test_main_application_error(self, mock_parse, mock_settings, mock_init, mock_run):
        """Test main with application error."""
        mock_parse.return_value = Mock(verbose=False)
        mock_settings.return_value = Mock(log_level="INFO")
        mock_logger = Mock()
        mock_services = {'logger': mock_logger}
        mock_init.return_value = mock_services
        mock_run.side_effect = Exception("App error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_logger.exception.assert_called_once()

    @patch('src.main.initialize_services')
    @patch('src.main.get_settings')
    @patch('src.main.parse_arguments')
    def test_main_verbose_log_level(self, mock_parse, mock_settings, mock_init):
        """Test that verbose flag sets DEBUG log level."""
        mock_args = Mock(verbose=True)
        mock_parse.return_value = mock_args
        mock_config = Mock(log_level="INFO")
        mock_settings.return_value = mock_config
        mock_init.return_value = {'logger': Mock()}

        with patch('src.main.run_application') as mock_run:
            main()

        # Verify DEBUG level was used instead of INFO
        mock_init.assert_called_once_with(mock_config, "DEBUG")
