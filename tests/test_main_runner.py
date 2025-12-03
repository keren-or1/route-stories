"""Tests for main runner module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.main_runner import (
    get_route_input,
    fetch_route,
    export_results,
    run_application
)


class TestGetRouteInput:
    """Test route input handling."""

    def test_get_route_input_from_args(self):
        """Test getting route from command-line arguments."""
        args = Mock(start="Tel Aviv", end="Jerusalem")
        cli = Mock()

        start, end = get_route_input(args, cli)

        assert start == "Tel Aviv"
        assert end == "Jerusalem"
        cli.get_route_input.assert_not_called()

    def test_get_route_input_from_cli(self):
        """Test getting route from CLI input."""
        args = Mock(start=None, end=None)
        cli = Mock()
        cli.get_route_input.return_value = ("A", "B")

        start, end = get_route_input(args, cli)

        assert start == "A"
        assert end == "B"
        cli.get_route_input.assert_called_once()

    def test_get_route_input_missing_end(self):
        """Test getting route when only start is provided."""
        args = Mock(start="Tel Aviv", end=None)
        cli = Mock()
        cli.get_route_input.return_value = ("Tel Aviv", "Jerusalem")

        start, end = get_route_input(args, cli)

        assert start == "Tel Aviv"
        assert end == "Jerusalem"
        cli.get_route_input.assert_called_once()


class TestFetchRoute:
    """Test route fetching."""

    def test_fetch_route_success(self):
        """Test successful route fetch."""
        google_maps = Mock()
        mock_route = Mock()
        google_maps.get_route.return_value = mock_route

        settings = Mock(max_waypoints=10)
        logger = Mock()

        result = fetch_route(
            google_maps,
            "Tel Aviv",
            "Jerusalem",
            None,
            settings,
            logger
        )

        assert result == mock_route
        google_maps.get_route.assert_called_once_with(
            origin="Tel Aviv",
            destination="Jerusalem",
            max_waypoints=10
        )
        logger.info.assert_called()

    def test_fetch_route_with_max_points(self):
        """Test route fetch with max_points override."""
        google_maps = Mock()
        google_maps.get_route.return_value = Mock()

        settings = Mock(max_waypoints=10)
        logger = Mock()

        fetch_route(google_maps, "A", "B", 5, settings, logger)

        google_maps.get_route.assert_called_once_with(
            origin="A",
            destination="B",
            max_waypoints=5
        )

    def test_fetch_route_error(self):
        """Test route fetch error handling."""
        google_maps = Mock()
        google_maps.get_route.side_effect = Exception("API error")

        settings = Mock(max_waypoints=10)
        logger = Mock()

        with pytest.raises(SystemExit) as exc_info:
            fetch_route(google_maps, "A", "B", None, settings, logger)

        assert exc_info.value.code == 1
        logger.error.assert_called()


class TestExportResults:
    """Test results export."""

    def test_export_results_custom_path(self):
        """Test export with custom path."""
        collector = Mock()
        args = Mock(export="custom.json")
        settings = Mock()
        route = Mock()
        cli = Mock()

        export_results(collector, args, settings, route, cli)

        collector.export_to_json.assert_called_once()
        export_path = collector.export_to_json.call_args[0][0]
        assert str(export_path) == "custom.json"
        cli.display_export_info.assert_called_once()

    def test_export_results_default_path(self):
        """Test export with default path."""
        collector = Mock()
        args = Mock(export=None)
        settings = Mock(base_dir=Path("/test"))
        route = Mock(route_id="test123")
        cli = Mock()

        export_results(collector, args, settings, route, cli)

        collector.export_to_json.assert_called_once()
        cli.display_export_info.assert_called_once()


class TestRunApplication:
    """Test main application flow."""

    @patch('src.main_runner.CLI')
    @patch('src.main_runner.Collector')
    @patch('src.main_runner.export_results')
    @patch('src.main_runner.fetch_route')
    @patch('src.main_runner.get_route_input')
    def test_run_application_success(
        self,
        mock_get_input,
        mock_fetch,
        mock_export,
        mock_collector_class,
        mock_cli_class
    ):
        """Test successful application run."""
        # Setup mocks
        mock_logger = Mock()
        mock_maps = Mock()
        mock_orchestrator = Mock()
        mock_queue = Mock()

        services = {
            'logger': mock_logger,
            'google_maps': mock_maps,
            'orchestrator': mock_orchestrator,
            'queue_manager': mock_queue
        }

        args = Mock(max_points=None)
        settings = Mock()

        mock_get_input.return_value = ("A", "B")
        mock_route = Mock(route_id="test123")
        mock_fetch.return_value = mock_route

        mock_collector = Mock()
        mock_collector_class.return_value = mock_collector

        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        # Execute
        run_application(services, args, settings)

        # Verify flow
        mock_cli_class.assert_called_once_with(orchestrator=None, collector=None)
        mock_cli.display_welcome.assert_called_once()
        mock_get_input.assert_called_once()
        mock_fetch.assert_called_once()
        mock_collector_class.assert_called_once_with(
            route_id="test123",
            queue_manager=mock_queue
        )
        mock_cli.run_interactive_session.assert_called_once()
        mock_export.assert_called_once()
        mock_orchestrator.shutdown.assert_called_once()

    @patch('src.main_runner.CLI')
    @patch('src.main_runner.Collector')
    @patch('src.main_runner.export_results')
    @patch('src.main_runner.fetch_route')
    @patch('src.main_runner.get_route_input')
    def test_run_application_updates_cli(
        self,
        mock_get_input,
        mock_fetch,
        mock_export,
        mock_collector_class,
        mock_cli_class
    ):
        """Test that CLI is updated with collector and orchestrator."""
        services = {
            'logger': Mock(),
            'google_maps': Mock(),
            'orchestrator': Mock(),
            'queue_manager': Mock()
        }

        mock_get_input.return_value = ("A", "B")
        mock_fetch.return_value = Mock(route_id="test")
        mock_collector = Mock()
        mock_collector_class.return_value = mock_collector
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        run_application(services, Mock(max_points=None), Mock())

        # Verify CLI was updated
        assert mock_cli.collector == mock_collector
        assert mock_cli.orchestrator == services['orchestrator']
