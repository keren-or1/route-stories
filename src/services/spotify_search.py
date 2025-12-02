"""Spotify API integration for music search."""

import os
import base64
import requests
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger
from src.services.music_search_utils import format_duration_ms

logger = get_logger("spotify_search")


class SpotifyAuth:
    """Handle Spotify authentication."""

    @staticmethod
    def get_token(client_id: str, client_secret: str) -> Optional[str]:
        """Get Spotify API token."""
        try:
            auth_str = f"{client_id}:{client_secret}"
            auth_bytes = auth_str.encode("utf-8")
            auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

            headers = {
                "Authorization": f"Basic {auth_base64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers=headers,
                data={"grant_type": "client_credentials"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()["access_token"]
        except Exception as e:
            logger.error(f"Failed to get Spotify token: {e}")
            return None


def search_spotify_tracks(query: str, token: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search for tracks on Spotify."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "q": query,
            "type": "track",
            "limit": max_results
        }

        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        tracks = response.json().get("tracks", {}).get("items", [])
        results = []

        for track in tracks:
            results.append({
                "title": track["name"],
                "artist": ", ".join([a["name"] for a in track["artists"]]),
                "album": track["album"]["name"],
                "duration": format_duration_ms(track["duration_ms"]),
                "url": track["external_urls"].get("spotify", ""),
                "genre": "Music"
            })

        return results
    except Exception as e:
        logger.error(f"Spotify search error: {e}")
        return []
