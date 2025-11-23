"""
Collector - Collects and organizes results from all waypoints.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from src.utils.queue_manager import QueueManager, AgentResult
from src.utils.logger import get_logger


logger = get_logger("collector")


@dataclass
class WaypointSummary:
    """Summary of processing results for a single waypoint."""
    point_id: int
    address: str
    location: Dict[str, float]
    video: Optional[Dict[str, Any]] = None
    song: Optional[Dict[str, Any]] = None
    story: Optional[Dict[str, Any]] = None
    chosen_type: Optional[str] = None
    chosen_content: Optional[Dict[str, Any]] = None
    judge_reasoning: Optional[str] = None
    judge_score: Optional[int] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class Collector:
    """
    Collects and organizes results from all waypoints.
    Provides methods to retrieve and export results.
    """

    def __init__(self, route_id: str, queue_manager: QueueManager):
        """
        Initialize collector.

        Args:
            route_id: Route identifier
            queue_manager: Queue manager with results
        """
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
        """
        Collect and organize results for a single waypoint.

        Args:
            point_id: Waypoint identifier
            address: Waypoint address
            location: Location coordinates
            results: Dictionary of agent results

        Returns:
            WaypointSummary object
        """
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
        """
        Get summary for a specific waypoint.

        Args:
            point_id: Waypoint identifier

        Returns:
            WaypointSummary or None
        """
        return self.waypoint_summaries.get(point_id)

    def get_all_summaries(self) -> List[WaypointSummary]:
        """
        Get all waypoint summaries in order.

        Returns:
            List of WaypointSummary objects
        """
        sorted_ids = sorted(self.waypoint_summaries.keys())
        return [self.waypoint_summaries[pid] for pid in sorted_ids]

    def get_route_summary(self) -> Dict[str, Any]:
        """
        Get complete route summary with all waypoints.

        Returns:
            Dictionary with route information and waypoints
        """
        summaries = self.get_all_summaries()

        return {
            'route_id': self.route_id,
            'total_waypoints': len(summaries),
            'waypoints': [asdict(s) for s in summaries],
            'statistics': self._calculate_statistics(summaries)
        }

    def _calculate_statistics(self, summaries: List[WaypointSummary]) -> Dict[str, Any]:
        """Calculate statistics for the route."""
        total = len(summaries)

        if total == 0:
            return {}

        chosen_counts = {'video': 0, 'song': 0, 'story': 0, 'error': 0}
        total_score = 0
        error_count = 0

        for summary in summaries:
            if summary.chosen_type:
                chosen_counts[summary.chosen_type] = chosen_counts.get(summary.chosen_type, 0) + 1
            else:
                chosen_counts['error'] += 1

            if summary.judge_score:
                total_score += summary.judge_score

            if summary.errors:
                error_count += len(summary.errors)

        return {
            'total_waypoints': total,
            'content_type_distribution': chosen_counts,
            'average_judge_score': total_score / total if total > 0 else 0,
            'total_errors': error_count
        }

    def export_to_json(self, filepath: Path) -> None:
        """
        Export results to JSON file.

        Args:
            filepath: Path to output JSON file
        """
        summary = self.get_route_summary()

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported results to {filepath}")

    def print_summary(self) -> None:
        """Print a human-readable summary to console."""
        summaries = self.get_all_summaries()

        print("\n" + "="*80)
        print(f"ROUTE SUMMARY - {self.route_id}")
        print("="*80)

        for summary in summaries:
            print(f"\nWaypoint {summary.point_id}: {summary.address}")
            print("-" * 80)

            if summary.chosen_type and summary.chosen_content:
                content = summary.chosen_content

                print(f"SELECTED: {summary.chosen_type.upper()}")

                if summary.chosen_type == 'video':
                    print(f"  Title: {content.get('title', 'N/A')}")
                    print(f"  Channel: {content.get('channel', 'N/A')}")
                    print(f"  Duration: {content.get('duration', 'N/A')}")
                    print(f"  URL: {content.get('url', 'N/A')}")

                elif summary.chosen_type == 'song':
                    print(f"  Title: {content.get('title', 'N/A')}")
                    print(f"  Artist: {content.get('artist', 'N/A')}")
                    print(f"  Genre: {content.get('genre', 'N/A')}")
                    print(f"  URL: {content.get('url', 'N/A')}")

                elif summary.chosen_type == 'story':
                    print(f"  Title: {content.get('title', 'N/A')}")
                    print(f"  Content: {content.get('content', 'N/A')[:200]}...")
                    print(f"  Source: {content.get('source', 'N/A')}")

                if summary.judge_reasoning:
                    print(f"\nJudge's Reasoning: {summary.judge_reasoning}")
                if summary.judge_score:
                    print(f"Confidence Score: {summary.judge_score}/100")

            if summary.errors:
                print("\nERRORS:")
                for error in summary.errors:
                    print(f"  - {error}")

        # Print statistics
        stats = self._calculate_statistics(summaries)
        print("\n" + "="*80)
        print("STATISTICS")
        print("="*80)
        print(f"Total Waypoints: {stats.get('total_waypoints', 0)}")
        print(f"Content Distribution: {stats.get('content_type_distribution', {})}")
        print(f"Average Judge Score: {stats.get('average_judge_score', 0):.1f}/100")
        print(f"Total Errors: {stats.get('total_errors', 0)}")
        print("="*80 + "\n")
