"""Executor configuration for thread pool management."""

from concurrent.futures import ThreadPoolExecutor
from src.utils.logger import get_logger

logger = get_logger("executor_config")


def create_executor(max_workers: int = 4) -> ThreadPoolExecutor:
    """Create a thread pool executor."""
    logger.debug(f"Creating executor with {max_workers} workers")
    return ThreadPoolExecutor(max_workers=max_workers)
