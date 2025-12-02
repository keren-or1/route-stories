"""
Data models for Collector.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


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
