"""
Base agent class providing common functionality for all agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger
from utils.queue_manager import AgentResult


logger = get_logger("base_agent")


@dataclass
class AgentTask:
    """Task data structure for agents."""
    route_id: str
    point_id: int
    address: str
    location: Dict[str, float]  # {'lat': ..., 'lng': ...}
    context: Optional[Dict[str, Any]] = None

    def __repr__(self):
        return f"AgentTask(route={self.route_id}, point={self.point_id}, address='{self.address}')"


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Provides common functionality and interface.
    """

    def __init__(self, name: str, agent_type: str):
        """
        Initialize base agent.

        Args:
            name: Agent name for logging
            agent_type: Agent type identifier (video, song, story, judge)
        """
        self.name = name
        self.agent_type = agent_type
        self.logger = get_logger(f"agent.{name}")
        self.logger.info(f"{name} initialized")

    @abstractmethod
    def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute agent task and return result.

        Args:
            task: AgentTask with location and context

        Returns:
            AgentResult with findings
        """
        pass

    def _create_result(
        self,
        task: AgentTask,
        content: Dict[str, Any],
        error: Optional[str] = None
    ) -> AgentResult:
        """
        Create an AgentResult object.

        Args:
            task: Original task
            content: Result content dictionary
            error: Optional error message

        Returns:
            AgentResult object
        """
        return AgentResult(
            route_id=task.route_id,
            point_id=task.point_id,
            agent_type=self.agent_type,
            content=content,
            timestamp=datetime.now(),
            error=error
        )

    def _handle_error(self, task: AgentTask, error: Exception) -> AgentResult:
        """
        Handle execution error and create error result.

        Args:
            task: Task that failed
            error: Exception that occurred

        Returns:
            AgentResult with error information
        """
        error_msg = f"{self.name} failed: {str(error)}"
        self.logger.error(error_msg)

        return self._create_result(
            task=task,
            content={},
            error=error_msg
        )

    def run(self, task: AgentTask) -> AgentResult:
        """
        Run the agent with error handling.

        Args:
            task: AgentTask to execute

        Returns:
            AgentResult (may contain error)
        """
        self.logger.info(f"Starting task: {task}")

        try:
            start_time = datetime.now()
            result = self.execute(task)
            duration = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                f"Task completed in {duration:.2f}s: {task.point_id}"
            )
            return result

        except Exception as e:
            return self._handle_error(task, e)
