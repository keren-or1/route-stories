"""
Comprehensive tests for CLI (Command Line Interface) module.
Tests user interaction, display methods, and interactive session flow.
"""

import pytest
import sys
from io import StringIO
from unittest.mock import Mock, MagicMock, patch, call
from src.ui.cli import CLI
from src.services.google_maps import Route, Waypoint
from src.core.collector import WaypointSummary


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for testing."""
    mock = Mock()
    mock.process_waypoint.return_value = {
        'video': {'title': 'Test Video', 'url': 'http://test.com'},
        'song': {'title': 'Test Song', 'artist': 'Test Artist'},
        'story': {'title': 'Test Story', 'content': 'Test content'}
    }
    return mock


@pytest.fixture
def mock_collector():
    """Mock collector for testing."""
    mock = Mock()
    mock.get_waypoint_summary.return_value = WaypointSummary(
        point_id=1,
        address="Test Location",
        location={'lat': 40.0, 'lng': -74.0},
        chosen_type='video',
        chosen_content={'title': 'Test Video', 'url': 'http://test.com', 'channel': 'Test Channel',
                       'duration': '10:00', 'views': '1M', 'description': 'Test description'},
        judge_reasoning='Best choice',
        judge_score=95,
        errors=[]
    )
    mock.print_summary.return_value = None
    return mock


@pytest.fixture
def cli(mock_orchestrator, mock_collector):
    """Create CLI instance for testing."""
    return CLI(orchestrator=mock_orchestrator, collector=mock_collector)


@pytest.fixture
def sample_route():
    """Sample route for testing."""
    waypoints = [
        Waypoint(
            point_id=1,
            address="New York, NY",
            location={'lat': 40.7128, 'lng': -74.0060},
            distance_from_start=0,
            duration_from_start=0
        ),
        Waypoint(
            point_id=2,
            address="Philadelphia, PA",
            location={'lat': 39.9526, 'lng': -75.1652},
            distance_from_start=150000,
            duration_from_start=7200
        )
    ]

    return Route(
        route_id="test-route-123",
        origin="New York, NY",
        destination="Philadelphia, PA",
        total_distance=150000,
        total_duration=7200,
        waypoints=waypoints
    )


class TestCLIInitialization:
    """Tests for CLI initialization."""

    def test_cli_init(self, mock_orchestrator, mock_collector):
        """Test CLI initializes correctly."""
        cli = CLI(orchestrator=mock_orchestrator, collector=mock_collector)
        assert cli.orchestrator == mock_orchestrator
        assert cli.collector == mock_collector

    def test_cli_init_logs(self, mock_orchestrator, mock_collector):
        """Test CLI initialization logs message."""
        with patch('src.ui.cli.logger') as mock_logger:
            cli = CLI(orchestrator=mock_orchestrator, collector=mock_collector)
            mock_logger.info.assert_called_with("CLI initialized")


class TestDisplayWelcome:
    """Tests for display_welcome method."""

    def test_display_welcome_output(self, cli):
        """Test welcome message is displayed."""
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_welcome()

        result = output.getvalue()
        assert 'ROUTE STORIES' in result
        assert 'AI-Powered Journey Content Curator' in result
        assert 'Welcome!' in result
        assert '=' in result  # Contains formatting

    def test_display_welcome_includes_instructions(self, cli):
        """Test welcome includes usage instructions."""
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_welcome()

        result = output.getvalue()
        assert 'route' in result.lower()
        assert 'content' in result.lower()


class TestGetRouteInput:
    """Tests for get_route_input method."""

    @patch('builtins.input')
    def test_get_route_input_success(self, mock_input, cli):
        """Test successful route input."""
        mock_input.side_effect = ['New York, NY', 'Philadelphia, PA']

        start, end = cli.get_route_input()

        assert start == 'New York, NY'
        assert end == 'Philadelphia, PA'
        assert mock_input.call_count == 2

    @patch('builtins.input')
    def test_get_route_input_strips_whitespace(self, mock_input, cli):
        """Test input strips whitespace."""
        mock_input.side_effect = ['  New York, NY  ', '  Philadelphia, PA  ']

        start, end = cli.get_route_input()

        assert start == 'New York, NY'
        assert end == 'Philadelphia, PA'

    @patch('builtins.input')
    def test_get_route_input_empty_start(self, mock_input, cli):
        """Test error when start is empty."""
        mock_input.side_effect = ['', 'Philadelphia, PA']

        with pytest.raises(SystemExit) as exc_info:
            cli.get_route_input()

        assert exc_info.value.code == 1

    @patch('builtins.input')
    def test_get_route_input_empty_end(self, mock_input, cli):
        """Test error when end is empty."""
        mock_input.side_effect = ['New York, NY', '']

        with pytest.raises(SystemExit) as exc_info:
            cli.get_route_input()

        assert exc_info.value.code == 1

    @patch('builtins.input')
    def test_get_route_input_whitespace_only_start(self, mock_input, cli):
        """Test error when start is only whitespace."""
        mock_input.side_effect = ['   ', 'Philadelphia, PA']

        with pytest.raises(SystemExit) as exc_info:
            cli.get_route_input()

        assert exc_info.value.code == 1


class TestDisplayRouteInfo:
    """Tests for display_route_info method."""

    def test_display_route_info_output(self, cli, sample_route):
        """Test route info is displayed correctly."""
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_route_info(sample_route)

        result = output.getvalue()
        assert 'ROUTE INFORMATION' in result
        assert sample_route.origin in result
        assert sample_route.destination in result
        assert '150.0 km' in result  # Distance conversion
        assert '120 minutes' in result  # Duration conversion
        assert '2' in result  # Number of waypoints

    def test_display_route_info_formatting(self, cli, sample_route):
        """Test route info has proper formatting."""
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_route_info(sample_route)

        result = output.getvalue()
        assert '=' * 80 in result  # Header separator
        assert 'From:' in result
        assert 'To:' in result
        assert 'Total Distance:' in result


class TestDisplayWaypointInfo:
    """Tests for display_waypoint_info method."""

    def test_display_waypoint_info_output(self, cli, sample_route):
        """Test waypoint info is displayed."""
        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_waypoint_info(waypoint, 0, 2)

        result = output.getvalue()
        assert 'WAYPOINT 1 of 2' in result
        assert waypoint.address in result
        assert '40.712800' in result  # Latitude
        assert '-74.006000' in result  # Longitude

    def test_display_waypoint_info_with_distance(self, cli, sample_route):
        """Test waypoint info includes distance from start."""
        waypoint = sample_route.waypoints[1]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_waypoint_info(waypoint, 1, 2)

        result = output.getvalue()
        assert 'Distance from start' in result
        assert '150.0 km' in result

    def test_display_waypoint_info_formatting(self, cli, sample_route):
        """Test waypoint info has proper formatting."""
        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_waypoint_info(waypoint, 0, 2)

        result = output.getvalue()
        assert '-' * 80 in result  # Separator


class TestDisplayProcessing:
    """Tests for display_processing method."""

    def test_display_processing_output(self, cli, sample_route):
        """Test processing message is displayed."""
        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_processing(waypoint)

        result = output.getvalue()
        assert waypoint.address in result
        assert 'Searching' in result
        assert 'Video Agent' in result
        assert 'Song Agent' in result
        assert 'Story Agent' in result
        assert 'Judge Agent' in result

    def test_display_processing_shows_all_agents(self, cli, sample_route):
        """Test all agent types are shown."""
        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_processing(waypoint)

        result = output.getvalue()
        assert 'YouTube' in result
        assert 'music' in result
        assert 'historical' in result
        assert 'evaluating' in result


class TestDisplayWaypointResult:
    """Tests for display_waypoint_result method."""

    def test_display_result_video(self, cli, mock_collector, sample_route):
        """Test displaying video result."""
        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_waypoint_result(waypoint)

        result = output.getvalue()
        assert 'RESULTS' in result
        assert 'SELECTED CONTENT: VIDEO' in result
        assert 'Test Video' in result
        assert 'Test Channel' in result
        assert '10:00' in result
        assert '1M' in result
        assert 'Best choice' in result
        assert '95/100' in result

    def test_display_result_song(self, cli, mock_collector, sample_route):
        """Test displaying song result."""
        mock_collector.get_waypoint_summary.return_value = WaypointSummary(
            point_id=1,
            address="Test Location",
            location={'lat': 40.0, 'lng': -74.0},
            chosen_type='song',
            chosen_content={'title': 'Test Song', 'artist': 'Test Artist', 'genre': 'Pop',
                           'duration': '3:30', 'album': 'Test Album', 'url': 'http://test.com'},
            judge_reasoning='Great music',
            judge_score=90,
            errors=[]
        )

        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_waypoint_result(waypoint)

        result = output.getvalue()
        assert 'SELECTED CONTENT: SONG' in result
        assert 'Test Song' in result
        assert 'Test Artist' in result
        assert 'Pop' in result
        assert '3:30' in result

    def test_display_result_story(self, cli, mock_collector, sample_route):
        """Test displaying story result."""
        mock_collector.get_waypoint_summary.return_value = WaypointSummary(
            point_id=1,
            address="Test Location",
            location={'lat': 40.0, 'lng': -74.0},
            chosen_type='story',
            chosen_content={'title': 'Test Story', 'content': 'Historical content here',
                           'source': 'Wikipedia', 'period': '1900s', 'url': 'http://test.com'},
            judge_reasoning='Interesting history',
            judge_score=88,
            errors=[]
        )

        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_waypoint_result(waypoint)

        result = output.getvalue()
        assert 'SELECTED CONTENT: STORY' in result
        assert 'Test Story' in result
        assert 'Historical content here' in result
        assert 'Wikipedia' in result
        assert '1900s' in result

    def test_display_result_no_summary(self, cli, mock_collector, sample_route):
        """Test displaying error when no summary."""
        mock_collector.get_waypoint_summary.return_value = None

        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_waypoint_result(waypoint)

        result = output.getvalue()
        assert 'Error' in result
        assert 'No results' in result

    def test_display_result_with_errors(self, cli, mock_collector, sample_route):
        """Test displaying result with errors."""
        mock_collector.get_waypoint_summary.return_value = WaypointSummary(
            point_id=1,
            address="Test Location",
            location={'lat': 40.0, 'lng': -74.0},
            chosen_type='video',
            chosen_content={'title': 'Test Video'},
            judge_reasoning='OK',
            judge_score=70,
            errors=['Warning: API timeout', 'Error: Rate limit']
        )

        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_waypoint_result(waypoint)

        result = output.getvalue()
        assert 'Warnings/Errors' in result
        assert 'API timeout' in result
        assert 'Rate limit' in result

    def test_display_result_no_content_selected(self, cli, mock_collector, sample_route):
        """Test displaying when no content selected."""
        mock_collector.get_waypoint_summary.return_value = WaypointSummary(
            point_id=1,
            address="Test Location",
            location={'lat': 40.0, 'lng': -74.0},
            chosen_type=None,
            chosen_content=None,
            judge_reasoning=None,
            judge_score=None,
            errors=['Processing failed']
        )

        waypoint = sample_route.waypoints[0]
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_waypoint_result(waypoint)

        result = output.getvalue()
        assert 'No content selected' in result
        assert 'processing failed' in result.lower()


class TestPromptNext:
    """Tests for prompt_next method."""

    @patch('builtins.input')
    def test_prompt_next_continue(self, mock_input, cli):
        """Test user continues to next waypoint."""
        mock_input.return_value = ''

        result = cli.prompt_next()

        assert result is True

    @patch('builtins.input')
    def test_prompt_next_quit_lowercase(self, mock_input, cli):
        """Test user quits with lowercase 'q'."""
        mock_input.return_value = 'q'

        result = cli.prompt_next()

        assert result is False

    @patch('builtins.input')
    def test_prompt_next_quit_uppercase(self, mock_input, cli):
        """Test user quits with uppercase 'Q'."""
        mock_input.return_value = 'Q'

        result = cli.prompt_next()

        assert result is False

    @patch('builtins.input')
    def test_prompt_next_quit_word(self, mock_input, cli):
        """Test user quits with 'quit'."""
        mock_input.return_value = 'quit'

        result = cli.prompt_next()

        assert result is False

    @patch('builtins.input')
    def test_prompt_next_random_input(self, mock_input, cli):
        """Test random input continues."""
        mock_input.return_value = 'xyz'

        result = cli.prompt_next()

        assert result is True


class TestDisplayFinalSummary:
    """Tests for display_final_summary method."""

    def test_display_final_summary_output(self, cli, mock_collector):
        """Test final summary is displayed."""
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_final_summary()

        result = output.getvalue()
        assert 'JOURNEY COMPLETE' in result
        assert '=' * 80 in result
        mock_collector.print_summary.assert_called_once()


class TestDisplayExportInfo:
    """Tests for display_export_info method."""

    def test_display_export_info_output(self, cli):
        """Test export info is displayed."""
        filepath = '/path/to/results.json'
        output = StringIO()
        with patch('sys.stdout', output):
            cli.display_export_info(filepath)

        result = output.getvalue()
        assert 'Results exported to' in result
        assert filepath in result
        assert 'review' in result.lower()


class TestRunInteractiveSession:
    """Tests for run_interactive_session method."""

    @patch('builtins.input')
    def test_run_interactive_session_full_route(self, mock_input, cli, mock_orchestrator,
                                                  mock_collector, sample_route):
        """Test running full interactive session."""
        # User continues through all waypoints
        mock_input.return_value = ''

        with patch('sys.stdout', StringIO()):
            cli.run_interactive_session(sample_route)

        # Verify all waypoints were processed
        assert mock_orchestrator.process_waypoint.call_count == 2
        assert mock_collector.collect_waypoint.call_count == 2

    @patch('builtins.input')
    def test_run_interactive_session_quit_early(self, mock_input, cli, mock_orchestrator,
                                                 mock_collector, sample_route):
        """Test user quits before completing all waypoints."""
        # User quits after first waypoint
        mock_input.return_value = 'q'

        with patch('sys.stdout', StringIO()):
            cli.run_interactive_session(sample_route)

        # Verify only first waypoint was processed
        assert mock_orchestrator.process_waypoint.call_count == 1
        assert mock_collector.collect_waypoint.call_count == 1

    def test_run_interactive_session_max_waypoints(self, cli, mock_orchestrator,
                                                     mock_collector, sample_route):
        """Test limiting number of waypoints processed."""
        with patch('sys.stdout', StringIO()):
            cli.run_interactive_session(sample_route, max_waypoints=1)

        # Verify only 1 waypoint was processed
        assert mock_orchestrator.process_waypoint.call_count == 1
        assert mock_collector.collect_waypoint.call_count == 1

    @patch('builtins.input')
    def test_run_interactive_session_calls_display_methods(self, mock_input, cli, sample_route):
        """Test interactive session calls all display methods."""
        mock_input.return_value = ''

        with patch.object(cli, 'display_route_info') as mock_route_info, \
             patch.object(cli, 'display_waypoint_info') as mock_waypoint_info, \
             patch.object(cli, 'display_processing') as mock_processing, \
             patch.object(cli, 'display_waypoint_result') as mock_result, \
             patch.object(cli, 'display_final_summary') as mock_summary, \
             patch('sys.stdout', StringIO()):

            cli.run_interactive_session(sample_route)

            mock_route_info.assert_called_once()
            assert mock_waypoint_info.call_count == 2
            assert mock_processing.call_count == 2
            assert mock_result.call_count == 2
            mock_summary.assert_called_once()

    @patch('builtins.input')
    def test_run_interactive_session_scheduler_not_used(self, mock_input, cli, sample_route):
        """Test that scheduler is created but not actively used in current implementation."""
        mock_input.return_value = ''

        with patch('src.ui.cli.Scheduler') as mock_scheduler_class, \
             patch('sys.stdout', StringIO()):

            cli.run_interactive_session(sample_route)

            # Scheduler is instantiated
            mock_scheduler_class.assert_called_once_with(sample_route)
