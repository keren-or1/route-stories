"""
Address parsing and extraction utilities for Google Maps route steps.
"""

import re
from typing import Dict, Any, Optional, Callable
from src.utils.logger import get_logger

logger = get_logger("address_parser")


# Direction keywords that indicate turn-by-turn instructions
DIRECTION_KEYWORDS = [
    'head', 'turn', 'continue', 'bear', 'go', 'keep', 'merge',
    'enter', 'exit', 'take', 'make', 'slight', 'sharp', 'right', 'left'
]


def extract_address_from_html_instructions(html: str) -> Optional[str]:
    """
    Extract meaningful address from HTML instructions.

    Args:
        html: HTML instructions from Google Maps step

    Returns:
        Extracted address or None
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    text_lower = text.lower().strip()

    # Check if this is a trivial direction (starts with direction verb)
    starts_with_direction = any(
        text_lower.startswith(keyword) for keyword in DIRECTION_KEYWORDS
    )

    # If it's NOT a direction, use the full instruction as-is
    if not starts_with_direction and len(text) > 3:
        return text

    # If it IS a direction, extract the street/location name that comes after the verb
    # Pattern: "Head [left/right/straight] on [Street Name]" or "Turn [direction] onto [Street Name]"
    if starts_with_direction:
        # Extract everything after prepositions like "on", "onto", "to"
        match = re.search(r'\b(?:on|onto|to|toward)\s+([A-Z][^,]+)', text)
        if match:
            street_name = match.group(1).strip()
            # Only use if it looks like a real street name (has letters, reasonable length)
            if len(street_name) > 2 and street_name not in ['right', 'left', 'straight']:
                return street_name

    return None


def extract_street_name_from_text(text: str) -> Optional[str]:
    """
    Extract street name from text using pattern matching.

    Args:
        text: Text containing potential street name

    Returns:
        Extracted street name or None
    """
    # Remove HTML tags if present
    text = re.sub(r'<[^>]+>', '', text)

    # Try to find a capitalized location/street name in the instruction
    match = re.search(
        r'\b([A-Z][a-zA-Z\s]+(?:St|Road|Ave|Blvd|Street|Highway|Drive|Lane|Rd|Av)\.?)\b',
        text
    )
    if match:
        return match.group(1).strip()

    return None


def format_geocoded_address(address: str) -> str:
    """
    Format a geocoded address to extract main location.

    Args:
        address: Full geocoded address

    Returns:
        Formatted address with main parts
    """
    # Extract just the main location (not full address)
    parts = address.split(',')

    # Prefer first meaningful part (usually street or area name)
    if len(parts) >= 2:
        return parts[0].strip() + ', ' + parts[1].strip()

    if parts[0].strip():
        return parts[0].strip()

    return address


def parse_step_address(
    step: Dict[str, Any],
    reverse_geocode_fn: Optional[Callable[[float, float], Optional[str]]] = None
) -> str:
    """
    Extract meaningful address from a route step.
    Prioritizes location information from turn-by-turn directions,
    falls back to reverse geocoding, then returns street names as last resort.

    Args:
        step: Step dictionary from Google Maps API
        reverse_geocode_fn: Optional function for reverse geocoding (lat, lng) -> address

    Returns:
        Address string or empty if no meaningful location found
    """
    # Try to extract from HTML instructions
    if 'html_instructions' in step:
        html = step['html_instructions']
        address = extract_address_from_html_instructions(html)
        if address:
            return address

    # Try reverse geocoding if function provided
    if reverse_geocode_fn:
        try:
            loc = step['end_location']
            address = reverse_geocode_fn(loc['lat'], loc['lng'])
            if address:
                return format_geocoded_address(address)
        except Exception as e:
            logger.debug(f"Reverse geocoding failed: {e}")

    # Final fallback: try to extract any street name from the instruction
    if 'html_instructions' in step:
        html = step['html_instructions']
        street_name = extract_street_name_from_text(html)
        if street_name:
            return street_name

    # No meaningful location found
    logger.debug("Could not extract meaningful address for step, skipping")
    return ""
