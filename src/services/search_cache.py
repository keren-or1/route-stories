"""
File-based caching system for search results with TTL expiration.
"""

import json
from typing import Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger("search_cache")


class SearchCache:
    """Simple file-based cache for search results (24-hour TTL)."""

    def __init__(self, cache_dir: str = ".cache"):
        """Initialize cache with directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_hours = 24

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if it exists and is not expired."""
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if cache is expired
            cached_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cached_time > timedelta(hours=self.ttl_hours):
                cache_path.unlink()  # Delete expired cache
                return None

            logger.debug(f"Cache hit for key: {key}")
            return data['value']

        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Cache a value with current timestamp."""
        cache_path = self._get_cache_path(key)

        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'value': value
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Cached result for key: {key}")

        except Exception as e:
            logger.warning(f"Cache write error: {e}")
