"""
Formatting utilities for Judge Agent.
Formats content options for LLM judgment.
"""

from typing import Dict, Any


def format_option_description(opt_type: str, data: Dict[str, Any]) -> str:
    """
    Format a single content option for display.

    Args:
        opt_type: Type of content ('video', 'song', 'story')
        data: Content data dictionary

    Returns:
        Formatted description string
    """
    if opt_type == 'video':
        desc = f"Video: \"{data.get('title', 'N/A')}\"\n"
        desc += f"  Description: {data.get('description', 'N/A')}\n"
        desc += f"  Duration: {data.get('duration', 'N/A')}\n"
        desc += f"  Channel: {data.get('channel', 'N/A')}"
        return desc

    elif opt_type == 'song':
        desc = f"Song: \"{data.get('title', 'N/A')}\" by {data.get('artist', 'N/A')}\n"
        desc += f"  Genre: {data.get('genre', 'N/A')}\n"
        desc += f"  Duration: {data.get('duration', 'N/A')}\n"
        desc += f"  Album: {data.get('album', 'N/A')}"
        return desc

    else:  # story
        desc = f"Story: \"{data.get('title', 'N/A')}\"\n"
        desc += f"  Content: {data.get('content', 'N/A')}\n"
        desc += f"  Category: {data.get('category', 'N/A')}\n"
        desc += f"  Period: {data.get('period', 'N/A')}"
        return desc
