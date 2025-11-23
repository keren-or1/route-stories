"""
Orchestrator - Manages multi-threaded execution of agents.
"""

import threading
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, Future
from src.agents import VideoAgent, SongAgent, StoryAgent, JudgeAgent, AgentTask
from src.utils.queue_manager import QueueManager, AgentResult
from src.utils.logger import get_logger


logger = get_logger("orchestrator")


class Orchestrator:
    """
    Orchestrates multi-threaded execution of content agents and judge.
    Manages concurrent search operations and result collection.
    """

    def __init__(
        self,
        video_agent: VideoAgent,
        song_agent: SongAgent,
        story_agent: StoryAgent,
        judge_agent: JudgeAgent,
        queue_manager: QueueManager,
        max_workers: int = 4
    ):
        """
        Initialize orchestrator with agents.

        Args:
            video_agent: Video search agent
            song_agent: Song search agent
            story_agent: Story search agent
            judge_agent: Judge agent
            queue_manager: Queue manager for results
            max_workers: Maximum number of worker threads
        """
        self.video_agent = video_agent
        self.song_agent = song_agent
        self.story_agent = story_agent
        self.judge_agent = judge_agent
        self.queue_manager = queue_manager
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"Orchestrator initialized with {max_workers} workers")

    def process_waypoint(
        self,
        route_id: str,
        point_id: int,
        address: str,
        location: Dict[str, float]
    ) -> Dict[str, AgentResult]:
        """
        Process a single waypoint by running all agents.

        Args:
            route_id: Route identifier
            point_id: Point identifier
            address: Location address
            location: Location coordinates {'lat': ..., 'lng': ...}

        Returns:
            Dictionary of all agent results including judge decision
        """
        logger.info(f"Processing waypoint {point_id}: {address}")

        # Create task for content agents
        task = AgentTask(
            route_id=route_id,
            point_id=point_id,
            address=address,
            location=location
        )

        # Step 1: Launch content agents in parallel
        futures = {
            'video': self.executor.submit(self._run_agent, self.video_agent, task),
            'song': self.executor.submit(self._run_agent, self.song_agent, task),
            'story': self.executor.submit(self._run_agent, self.story_agent, task)
        }

        # Step 2: Wait for all content agents to complete
        content_results = {}
        for agent_type, future in futures.items():
            try:
                result = future.result(timeout=60)  # 60 second timeout per agent
                content_results[agent_type] = result
                self.queue_manager.put_result(result)
            except Exception as e:
                logger.error(f"Agent {agent_type} failed: {e}")
                # Create error result
                error_result = AgentResult(
                    route_id=route_id,
                    point_id=point_id,
                    agent_type=agent_type,
                    content={},
                    error=str(e)
                )
                content_results[agent_type] = error_result
                self.queue_manager.put_result(error_result)

        # Step 3: Run judge agent with content results
        judge_task = AgentTask(
            route_id=route_id,
            point_id=point_id,
            address=address,
            location=location,
            context={'content_results': content_results}
        )

        try:
            judge_result = self.judge_agent.run(judge_task)
            content_results['judge'] = judge_result
            self.queue_manager.put_result(judge_result)
        except Exception as e:
            logger.error(f"Judge agent failed: {e}")
            error_result = AgentResult(
                route_id=route_id,
                point_id=point_id,
                agent_type='judge',
                content={},
                error=str(e)
            )
            content_results['judge'] = error_result
            self.queue_manager.put_result(error_result)

        logger.info(f"Completed waypoint {point_id}")
        return content_results

    def _run_agent(self, agent, task: AgentTask) -> AgentResult:
        """
        Run a single agent with error handling.

        Args:
            agent: Agent instance
            task: AgentTask

        Returns:
            AgentResult
        """
        return agent.run(task)

    def shutdown(self):
        """Shutdown the thread pool executor."""
        logger.info("Shutting down orchestrator")
        self.executor.shutdown(wait=True)
        logger.info("Orchestrator shutdown complete")
