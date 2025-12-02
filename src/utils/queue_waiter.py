"""
Wait utilities for queue results.
"""

import time
from typing import List
from src.utils.logger import get_logger


logger = get_logger("queue_waiter")


def wait_for_results(
    queue_manager,
    route_id: str,
    point_id: int,
    agent_types: List[str],
    timeout: float = 30.0,
    poll_interval: float = 0.1
) -> bool:
    """
    Wait for specific agent results with timeout.

    Args:
        queue_manager: QueueManager instance
        route_id: Route identifier
        point_id: Point identifier
        agent_types: List of agent types to wait for
        timeout: Maximum wait time in seconds
        poll_interval: How often to check for results

    Returns:
        True if all results arrived, False on timeout
    """
    elapsed = 0.0

    while elapsed < timeout:
        results = queue_manager.get_point_results(route_id, point_id)
        if all(agent_type in results for agent_type in agent_types):
            return True

        time.sleep(poll_interval)
        elapsed += poll_interval

    logger.warning(
        f"Timeout waiting for results: route={route_id}, point={point_id}, "
        f"agents={agent_types}"
    )
    return False
