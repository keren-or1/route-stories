"""
Collector - Collects and organizes results from all waypoints.
"""

from typing import Dict, List, Any, Optional
from dataclasses import asdict
import json
from pathlib import Path
from src.utils.queue_manager import QueueManager, AgentResult
from src.utils.logger import get_logger
from src.core.collector_models import WaypointSummary
from src.core.collector_stats import calculate_statistics
from src.core.collector_printer import print_full_summary


logger = get_logger("collector")


class Collector:
    """
    Collects and organizes results from all waypoints.
    Provides methods to retrieve and export results.
    """

    def __init__(self, route_id: str, queue_manager: QueueManager):
        """Initialize collector."""
        self.route_id = route_id
        self.queue_manager = queue_manager
        self.waypoint_summaries: Dict[int, WaypointSummary] = {}
        logger.info(f"Collector initialized for route {route_id}")

    def collect_waypoint(
        self,
        point_id: int,
        address: str,
        location: Dict[str, float],
        results: Dict[str, AgentResult]
    ) -> WaypointSummary:
        """Collect and organize results for a single waypoint."""
        summary = WaypointSummary(
            point_id=point_id,
            address=address,
            location=location
        )

        # Collect content agent results
        for agent_type in ['video', 'song', 'story']:
            if agent_type in results:
                result = results[agent_type]
                if result.error:
                    summary.errors.append(f"{agent_type}: {result.error}")
                else:
                    content = result.content.get('selected', {})
                    setattr(summary, agent_type, content)

        # Collect judge result
        if 'judge' in results:
            judge_result = results['judge']
            if judge_result.error:
                summary.errors.append(f"judge: {judge_result.error}")
            else:
                summary.chosen_type = judge_result.content.get('chosen_type')
                summary.chosen_content = judge_result.content.get('chosen_content')
                summary.judge_reasoning = judge_result.content.get('reasoning')
                summary.judge_score = judge_result.content.get('score')

        # Store summary
        self.waypoint_summaries[point_id] = summary

        logger.info(f"Collected waypoint {point_id}: chosen={summary.chosen_type}")
        return summary

    def get_waypoint_summary(self, point_id: int) -> Optional[WaypointSummary]:
        """Get summary for a specific waypoint."""
        return self.waypoint_summaries.get(point_id)

    def get_all_summaries(self) -> List[WaypointSummary]:
        """Get all waypoint summaries in order."""
        sorted_ids = sorted(self.waypoint_summaries.keys())
        return [self.waypoint_summaries[pid] for pid in sorted_ids]

    def get_route_summary(self) -> Dict[str, Any]:
        """Get complete route summary with all waypoints."""
        summaries = self.get_all_summaries()

        return {
            'route_id': self.route_id,
            'total_waypoints': len(summaries),
            'waypoints': [asdict(s) for s in summaries],
            'statistics': calculate_statistics(summaries)
        }

    def export_to_json(self, filepath: Path) -> None:
        """Export results to JSON file."""
        summary = self.get_route_summary()

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported results to {filepath}")

    def print_summary(self) -> None:
        """Print a human-readable summary to console."""
        summaries = self.get_all_summaries()
        stats = calculate_statistics(summaries)
        print_full_summary(self.route_id, summaries, stats)

    def _calculate_statistics(self, summaries: List[WaypointSummary]) -> Dict[str, Any]:
        """Calculate statistics for the route (backward compatibility)."""
        return calculate_statistics(summaries)
