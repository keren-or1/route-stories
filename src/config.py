"""
Configuration module for Route Stories application.
Manages environment variables and application settings.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    google_maps_api_key: str
    gemini_api_key: str

    # Application settings
    log_level: str = "INFO"
    max_waypoints: int = 10

    # Agent settings
    agent_timeout: int = 30  # seconds
    max_retries: int = 3

    # Gemini model configuration
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_max_tokens: int = 4096
    gemini_temperature: float = 0.7

    # Paths
    base_dir: Path = Path(__file__).parent.parent  # Project root
    logs_dir: Path = base_dir / "logs"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create logs directory if it doesn't exist
        self.logs_dir.mkdir(exist_ok=True)


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create the global settings instance.

    Returns:
        Settings instance with loaded configuration
    """
    global settings
    if settings is None:
        settings = Settings()
    return settings


def reload_settings() -> Settings:
    """
    Force reload settings from environment.

    Returns:
        Newly loaded Settings instance
    """
    global settings
    settings = Settings()
    return settings
