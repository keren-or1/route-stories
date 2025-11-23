"""
Queue management utilities for inter-agent communication.
Handles thread-safe data exchange between agents.
"""

import queue
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from src.utils.logger import get_logger


logger = get_logger("queue_manager")


@dataclass
class AgentResult:
    """Data structure for agent results."""
    route_id: str
    point_id: int
    agent_type: str  # 'video', 'song', 'story', 'judge'
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None

    def __repr__(self):
        status = "ERROR" if self.error else "SUCCESS"
        return f"AgentResult({self.agent_type}, point_id={self.point_id}, status={status})"


class QueueManager:
    """
    Manages queues for agent communication and result collection.
    Thread-safe implementation for multi-threaded agent execution.
    """

    def __init__(self):
        """Initialize queue manager with result queues."""
        self.results_queue: queue.Queue = queue.Queue()
        self._results_by_point: Dict[str, Dict[int, Dict[str, AgentResult]]] = {}
        self._lock = threading.Lock()
        logger.info("QueueManager initialized")

    def put_result(self, result: AgentResult) -> None:
        """
        Add an agent result to the queue.

        Args:
            result: AgentResult object containing agent output
        """
        self.results_queue.put(result)

        with self._lock:
            # Organize results by route_id and point_id
            if result.route_id not in self._results_by_point:
                self._results_by_point[result.route_id] = {}

            if result.point_id not in self._results_by_point[result.route_id]:
                self._results_by_point[result.route_id][result.point_id] = {}

            self._results_by_point[result.route_id][result.point_id][result.agent_type] = result

        logger.debug(f"Added result: {result}")

    def get_result(self, timeout: Optional[float] = None) -> Optional[AgentResult]:
        """
        Retrieve a result from the queue.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            AgentResult or None if timeout
        """
        try:
            return self.results_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_point_results(
        self,
        route_id: str,
        point_id: int
    ) -> Dict[str, AgentResult]:
        """
        Get all results for a specific point.

        Args:
            route_id: Route identifier
            point_id: Point identifier

        Returns:
            Dictionary mapping agent_type to AgentResult
        """
        with self._lock:
            return self._results_by_point.get(route_id, {}).get(point_id, {}).copy()

    def has_all_content_results(
        self,
        route_id: str,
        point_id: int
    ) -> bool:
        """
        Check if all three content agents (video, song, story) have submitted results.

        Args:
            route_id: Route identifier
            point_id: Point identifier

        Returns:
            True if all content agents have results
        """
        results = self.get_point_results(route_id, point_id)
        required_agents = {'video', 'song', 'story'}
        return required_agents.issubset(results.keys())

    def get_all_results_for_route(self, route_id: str) -> Dict[int, Dict[str, AgentResult]]:
        """
        Get all results for an entire route.

        Args:
            route_id: Route identifier

        Returns:
            Dictionary mapping point_id to agent results
        """
        with self._lock:
            return self._results_by_point.get(route_id, {}).copy()

    def clear_route_results(self, route_id: str) -> None:
        """
        Clear all results for a specific route.

        Args:
            route_id: Route identifier
        """
        with self._lock:
            if route_id in self._results_by_point:
                del self._results_by_point[route_id]
        logger.info(f"Cleared results for route {route_id}")

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.results_queue.qsize()

    def wait_for_results(
        self,
        route_id: str,
        point_id: int,
        agent_types: List[str],
        timeout: float = 30.0,
        poll_interval: float = 0.1
    ) -> bool:
        """
        Wait for specific agent results with timeout.

        Args:
            route_id: Route identifier
            point_id: Point identifier
            agent_types: List of agent types to wait for
            timeout: Maximum wait time in seconds
            poll_interval: How often to check for results

        Returns:
            True if all results arrived, False on timeout
        """
        import time
        elapsed = 0.0

        while elapsed < timeout:
            results = self.get_point_results(route_id, point_id)
            if all(agent_type in results for agent_type in agent_types):
                return True

            time.sleep(poll_interval)
            elapsed += poll_interval

        logger.warning(
            f"Timeout waiting for results: route={route_id}, point={point_id}, "
            f"agents={agent_types}"
        )
        return False
