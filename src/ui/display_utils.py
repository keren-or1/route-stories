"""Utility functions for CLI display formatting."""

# Separator and formatting constants
SEPARATOR_LONG = "=" * 80
SEPARATOR_SHORT = "-" * 80
TITLE_PAD = " " * 25
SUBTITLE_PAD = " " * 15


def format_route_display(origin, destination, distance_m, duration_s, num_waypoints):
    """Format route information for display."""
    lines = [
        "",
        SEPARATOR_LONG,
        "ROUTE INFORMATION",
        SEPARATOR_LONG,
        f"From: {origin}",
        f"To: {destination}",
        f"Total Distance: {distance_m / 1000:.1f} km",
        f"Estimated Duration: {duration_s / 60:.0f} minutes",
        f"Waypoints: {num_waypoints}",
        SEPARATOR_LONG + "\n"
    ]
    return "\n".join(lines)


def format_waypoint_header(index, total, address, lat, lng):
    """Format waypoint header information."""
    lines = [
        "",
        SEPARATOR_SHORT,
        f"WAYPOINT {index + 1} of {total}",
        SEPARATOR_SHORT,
        f"Location: {address}",
        f"Coordinates: {lat:.6f}, {lng:.6f}"
    ]
    return "\n".join(lines)


def format_content_item(title, source, url):
    """Format content item for display."""
    lines = [
        f"  Title: {title}",
        f"  Source: {source}"
    ]
    if url:
        lines.append(f"  URL: {url}")
    return "\n".join(lines)
