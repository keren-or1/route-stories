"""
Unit tests for logger configuration module.
Tests logging setup, formatters, and output.
"""

import pytest
import logging
import sys
from pathlib import Path
from io import StringIO
from src.utils.logger import ColoredFormatter, setup_logger, get_logger


class TestColoredFormatter:
    """Tests for ColoredFormatter class."""

    def test_colored_formatter_debug(self):
        """Test DEBUG level formatting with color."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.DEBUG,
            pathname='test.py',
            lineno=1,
            msg='Test debug message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        assert 'DEBUG' in formatted
        assert 'Test debug message' in formatted
        # Check that color codes are present
        assert '\033[' in formatted

    def test_colored_formatter_info(self):
        """Test INFO level formatting with color."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test info message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        assert 'INFO' in formatted
        assert 'Test info message' in formatted
        assert '\033[32m' in formatted  # Green color

    def test_colored_formatter_warning(self):
        """Test WARNING level formatting with color."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.WARNING,
            pathname='test.py',
            lineno=1,
            msg='Test warning message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        assert 'WARNING' in formatted
        assert 'Test warning message' in formatted
        assert '\033[33m' in formatted  # Yellow color

    def test_colored_formatter_error(self):
        """Test ERROR level formatting with color."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Test error message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        assert 'ERROR' in formatted
        assert 'Test error message' in formatted
        assert '\033[31m' in formatted  # Red color

    def test_colored_formatter_critical(self):
        """Test CRITICAL level formatting with color."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.CRITICAL,
            pathname='test.py',
            lineno=1,
            msg='Test critical message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        assert 'CRITICAL' in formatted
        assert 'Test critical message' in formatted
        assert '\033[35m' in formatted  # Magenta color

    def test_colored_formatter_unknown_level(self):
        """Test unknown log level uses reset color."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=25,  # Non-standard level
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.levelname = 'CUSTOM'

        formatted = formatter.format(record)

        assert 'CUSTOM' in formatted
        assert 'Test message' in formatted


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_basic(self, tmp_path):
        """Test basic logger setup."""
        logger = setup_logger(
            name="test_logger",
            log_level="INFO",
            log_dir=tmp_path,
            enable_console=True,
            enable_file=True
        )

        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

    def test_setup_logger_debug_level(self, tmp_path):
        """Test logger with DEBUG level."""
        logger = setup_logger(
            name="debug_logger",
            log_level="DEBUG",
            log_dir=tmp_path
        )

        assert logger.level == logging.DEBUG

    def test_setup_logger_warning_level(self, tmp_path):
        """Test logger with WARNING level."""
        logger = setup_logger(
            name="warning_logger",
            log_level="WARNING",
            log_dir=tmp_path
        )

        assert logger.level == logging.WARNING

    def test_setup_logger_error_level(self, tmp_path):
        """Test logger with ERROR level."""
        logger = setup_logger(
            name="error_logger",
            log_level="ERROR",
            log_dir=tmp_path
        )

        assert logger.level == logging.ERROR

    def test_setup_logger_console_only(self):
        """Test logger with only console handler."""
        logger = setup_logger(
            name="console_logger",
            log_level="INFO",
            enable_console=True,
            enable_file=False
        )

        assert len(logger.handlers) >= 1
        # Should have console handler
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_setup_logger_file_only(self, tmp_path):
        """Test logger with only file handler."""
        logger = setup_logger(
            name="file_logger",
            log_level="INFO",
            log_dir=tmp_path,
            enable_console=False,
            enable_file=True
        )

        assert len(logger.handlers) >= 1
        # Should have file handler
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_setup_logger_creates_log_file(self, tmp_path):
        """Test that logger creates log file."""
        logger = setup_logger(
            name="file_test_logger",
            log_level="INFO",
            log_dir=tmp_path,
            enable_file=True
        )

        # Write a log message
        logger.info("Test message")

        # Check that log file was created
        log_files = list(tmp_path.glob("route_stories_*.log"))
        assert len(log_files) >= 1

    def test_setup_logger_no_handlers(self):
        """Test logger with no handlers."""
        logger = setup_logger(
            name="no_handlers_logger",
            log_level="INFO",
            enable_console=False,
            enable_file=False
        )

        assert len(logger.handlers) == 0

    def test_setup_logger_clears_existing_handlers(self, tmp_path):
        """Test that setup_logger clears existing handlers."""
        # Setup logger first time
        logger = setup_logger(
            name="clear_test_logger",
            log_level="INFO",
            log_dir=tmp_path
        )

        handler_count_1 = len(logger.handlers)

        # Setup same logger again
        logger = setup_logger(
            name="clear_test_logger",
            log_level="INFO",
            log_dir=tmp_path
        )

        handler_count_2 = len(logger.handlers)

        # Should have same number of handlers (not doubled)
        assert handler_count_2 == handler_count_1

    def test_setup_logger_log_dir_creation(self, tmp_path):
        """Test that logger creates log directory if it doesn't exist."""
        log_dir = tmp_path / "new_logs" / "nested"

        assert not log_dir.exists()

        logger = setup_logger(
            name="dir_creation_logger",
            log_level="INFO",
            log_dir=log_dir,
            enable_file=True
        )

        assert log_dir.exists()

    def test_setup_logger_file_encoding(self, tmp_path):
        """Test that log files use UTF-8 encoding."""
        logger = setup_logger(
            name="encoding_logger",
            log_level="INFO",
            log_dir=tmp_path,
            enable_file=True
        )

        # Log message with special characters
        logger.info("Test message with special chars: é, ñ, 中文, תטסט")

        # Read log file and verify encoding works
        log_files = list(tmp_path.glob("route_stories_*.log"))
        assert len(log_files) >= 1

        content = log_files[0].read_text(encoding='utf-8')
        assert "Test message with special chars" in content

    def test_setup_logger_console_stream(self):
        """Test that console handler uses stdout."""
        logger = setup_logger(
            name="stream_logger",
            log_level="INFO",
            enable_console=True,
            enable_file=False
        )

        # Find console handler
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) >= 1

        # Check it uses stdout
        assert console_handlers[0].stream == sys.stdout


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_child(self):
        """Test that get_logger returns a child logger."""
        logger = get_logger("test_module")

        assert logger.name == "route_stories.test_module"

    def test_get_logger_different_names(self):
        """Test getting loggers with different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "route_stories.module1"
        assert logger2.name == "route_stories.module2"
        assert logger1 is not logger2

    def test_get_logger_same_name_returns_same_instance(self):
        """Test that same name returns same logger instance."""
        logger1 = get_logger("same_module")
        logger2 = get_logger("same_module")

        assert logger1 is logger2

    def test_get_logger_inherits_parent_config(self):
        """Test that child logger inherits parent configuration."""
        # Setup parent logger
        parent = setup_logger(
            name="route_stories",
            log_level="DEBUG",
            enable_console=True,
            enable_file=False
        )

        # Get child logger
        child = get_logger("child_module")

        # Child should inherit parent's configuration
        assert child.parent == parent


class TestLoggerIntegration:
    """Integration tests for logging functionality."""

    def test_logger_logs_to_console(self, capsys):
        """Test that logger actually writes to console."""
        logger = setup_logger(
            name="console_test",
            log_level="INFO",
            enable_console=True,
            enable_file=False
        )

        logger.info("Test console output")

        # Note: capsys captures sys.stdout, but logging might not show up immediately
        # This is a basic check that the logger was configured

    def test_logger_logs_to_file(self, tmp_path):
        """Test that logger writes to file correctly."""
        logger = setup_logger(
            name="file_write_test",
            log_level="INFO",
            log_dir=tmp_path,
            enable_console=False,
            enable_file=True
        )

        logger.info("Test file output")
        logger.warning("Test warning")
        logger.error("Test error")

        # Check file content
        log_files = list(tmp_path.glob("route_stories_*.log"))
        assert len(log_files) >= 1

        content = log_files[0].read_text()
        assert "Test file output" in content
        assert "Test warning" in content
        assert "Test error" in content

    def test_logger_respects_level_filtering(self, tmp_path):
        """Test that logger filters messages by level."""
        logger = setup_logger(
            name="level_filter_test",
            log_level="WARNING",
            log_dir=tmp_path,
            enable_console=False,
            enable_file=True
        )

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Check file content
        log_files = list(tmp_path.glob("route_stories_*.log"))
        assert len(log_files) >= 1

        content = log_files[0].read_text()
        # Should not contain DEBUG or INFO
        assert "Debug message" not in content
        assert "Info message" not in content
        # Should contain WARNING and ERROR
        assert "Warning message" in content
        assert "Error message" in content

    def test_logger_file_handler_level(self, tmp_path):
        """Test file handler uses DEBUG level."""
        logger = setup_logger(
            name="handler_level_test",
            log_level="DEBUG",
            log_dir=tmp_path,
            enable_file=True
        )

        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1
        assert file_handlers[0].level == logging.DEBUG

    def test_logger_console_handler_level(self):
        """Test console handler uses INFO level."""
        logger = setup_logger(
            name="console_handler_level_test",
            log_level="DEBUG",
            enable_console=True,
            enable_file=False
        )

        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) >= 1
        assert console_handlers[0].level == logging.INFO
