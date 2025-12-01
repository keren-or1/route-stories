"""
Unit tests for configuration module.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch
from src.config import Settings, get_settings, reload_settings


class TestSettings:
    """Tests for Settings class."""

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_gemini', 'GOOGLE_MAPS_API_KEY': 'test_maps'})
    def test_settings_loads_api_keys(self):
        """Test loading API keys from environment."""
        settings = Settings()
        assert settings.gemini_api_key == 'test_gemini'
        assert settings.google_maps_api_key == 'test_maps'

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'GOOGLE_MAPS_API_KEY': 'test', 'LOG_LEVEL': 'DEBUG'})
    def test_settings_log_level_from_env(self):
        """Test loading log level from environment."""
        settings = Settings()
        assert settings.log_level == 'DEBUG'

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'GOOGLE_MAPS_API_KEY': 'test'})
    def test_settings_defaults(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.log_level == 'INFO'
        assert settings.max_waypoints == 10
        assert settings.agent_timeout == 30
        assert settings.max_retries == 3

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'GOOGLE_MAPS_API_KEY': 'test'})
    def test_settings_gemini_defaults(self):
        """Test Gemini model default settings."""
        settings = Settings()
        # Check that gemini model is configured (exact model may vary)
        assert settings.gemini_model.startswith('gemini')
        assert settings.gemini_max_tokens == 4096
        assert settings.gemini_temperature == 0.7

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'GOOGLE_MAPS_API_KEY': 'test'})
    def test_settings_paths(self):
        """Test path configuration."""
        settings = Settings()
        assert settings.base_dir is not None
        assert isinstance(settings.base_dir, Path)
        assert settings.logs_dir is not None
        assert isinstance(settings.logs_dir, Path)

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'GOOGLE_MAPS_API_KEY': 'test'})
    def test_settings_creates_logs_dir(self):
        """Test that Settings creates logs directory."""
        settings = Settings()
        assert settings.logs_dir.exists()
        assert settings.logs_dir.is_dir()

    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test',
        'GOOGLE_MAPS_API_KEY': 'test',
        'MAX_WAYPOINTS': '20',
        'AGENT_TIMEOUT': '60'
    })
    def test_settings_custom_values(self):
        """Test loading custom values from environment."""
        settings = Settings()
        assert settings.max_waypoints == 20
        assert settings.agent_timeout == 60


class TestGetSettings:
    """Tests for get_settings function."""

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'GOOGLE_MAPS_API_KEY': 'test'})
    def test_get_settings_returns_instance(self):
        """Test that get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'GOOGLE_MAPS_API_KEY': 'test'})
    def test_get_settings_singleton(self):
        """Test that get_settings returns same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test2', 'GOOGLE_MAPS_API_KEY': 'test2'})
    def test_reload_settings(self):
        """Test reload_settings creates new instance."""
        settings = reload_settings()
        assert isinstance(settings, Settings)

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'GOOGLE_MAPS_API_KEY': 'test'})
    def test_get_settings_creates_if_none(self):
        """Test get_settings creates instance if global is None."""
        import src.config as config_module
        config_module.settings = None

        settings = get_settings()
        assert settings is not None
        assert isinstance(settings, Settings)
