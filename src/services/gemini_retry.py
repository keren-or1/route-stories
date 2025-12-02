"""
Retry handling utilities for Gemini API.
"""

import time
from src.utils.logger import get_logger


logger = get_logger("gemini_retry")


class RetryHandler:
    """Handles retry logic for API calls."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retries
            retry_delay: Base delay in seconds between retries
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if should retry after an error.

        Args:
            error: Exception that occurred
            attempt: Current attempt number (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        error_str = str(error)

        # Check for rate limit errors
        if "429" in error_str or "rate" in error_str.lower():
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Rate limited. Retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                time.sleep(wait_time)
                return True

        logger.error(f"API call failed (attempt {attempt + 1}): {error}")
        return attempt < self.max_retries - 1
