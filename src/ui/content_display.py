"""Content display functions for different media types."""


def display_video_content(content: dict):
    """Display video content details."""
    print(f"Title: {content.get('title', 'N/A')}")
    print(f"Channel: {content.get('channel', 'N/A')}")
    print(f"Duration: {content.get('duration', 'N/A')}")
    print(f"Views: {content.get('views', 'N/A')}")
    print(f"Description: {content.get('description', 'N/A')[:150]}...")
    print(f"URL: {content.get('url', 'N/A')}")


def display_song_content(content: dict):
    """Display song content details."""
    print(f"Title: {content.get('title', 'N/A')}")
    print(f"Artist: {content.get('artist', 'N/A')}")
    print(f"Genre: {content.get('genre', 'N/A')}")
    print(f"Duration: {content.get('duration', 'N/A')}")
    print(f"Album: {content.get('album', 'N/A')}")
    print(f"URL: {content.get('url', 'N/A')}")


def display_story_content(content: dict):
    """Display story content details."""
    print(f"Title: {content.get('title', 'N/A')}")
    print(f"Content: {content.get('content', 'N/A')}")
    print(f"Source: {content.get('source', 'N/A')}")
    print(f"Period: {content.get('period', 'N/A')}")
    print(f"URL: {content.get('url', 'N/A')}")
