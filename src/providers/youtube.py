"""YouTube Music provider - wraps ytmusicapi for playlist and track operations."""

import logging
from typing import Any

from ytmusicapi import YTMusic

from src.core.exceptions import AuthenticationError, PlaylistNotFoundError

logger = logging.getLogger(__name__)


class YouTubeProvider:
    """Interface to YouTube Music API via ytmusicapi."""

    def __init__(self, ytmusic: YTMusic) -> None:
        self._ytmusic = ytmusic

    def get_playlists(self) -> list[dict[str, Any]]:
        """
        Fetch all user playlists.

        Returns:
            List of playlist dicts with keys: playlistId, title, count.
        """
        try:
            playlists = self._ytmusic.get_library_playlists(limit=100)
            return [
                {
                    "playlistId": p.get("playlistId", ""),
                    "title": p.get("title", "Untitled"),
                    "count": p.get("count", 0),
                }
                for p in playlists
            ]
        except Exception as e:
            logger.error(f"Failed to fetch playlists: {e}")
            raise AuthenticationError(f"Could not fetch playlists: {e}") from e

    def get_liked_songs(self) -> list[dict[str, Any]]:
        """
        Fetch user's liked songs.

        Returns:
            List of track dictionaries.
        """
        try:
            result = self._ytmusic.get_liked_songs(limit=5000)
            tracks: list[dict[str, Any]] = result.get("tracks", [])
            logger.info(f"Fetched {len(tracks)} liked songs")
            return tracks
        except Exception as e:
            logger.error(f"Failed to fetch liked songs: {e}")
            raise AuthenticationError(f"Could not fetch liked songs: {e}") from e

    def get_playlist_tracks(self, playlist_id: str) -> list[dict[str, Any]]:
        """
        Fetch tracks from a specific playlist.

        Args:
            playlist_id: YouTube Music playlist ID.

        Returns:
            List of track dictionaries.

        Raises:
            PlaylistNotFoundError: If playlist doesn't exist.
        """
        try:
            playlist = self._ytmusic.get_playlist(playlist_id, limit=5000)
            tracks: list[dict[str, Any]] = playlist.get("tracks", [])
            logger.info(f"Fetched {len(tracks)} tracks from {playlist_id}")
            return tracks
        except Exception as e:
            raise PlaylistNotFoundError(f"Playlist {playlist_id} not found: {e}") from e

    def search(
        self,
        query: str,
        filter_type: str = "songs",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Search YouTube Music.

        Args:
            query: Search query string.
            filter_type: Type filter (songs, albums, artists, playlists).
            limit: Max results.

        Returns:
            List of search result dictionaries.
        """
        try:
            results: list[dict[str, Any]] = self._ytmusic.search(
                query, filter=filter_type, limit=limit
            )
            return results
        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")
            return []

    @staticmethod
    def normalize_track(track: dict[str, Any]) -> dict[str, str]:
        """
        Normalize raw ytmusicapi track dict to standard format.

        Returns:
            Dict with keys: title, artist, album, video_id, duration,
            genre.
        """
        artists = track.get("artists") or []
        artist_name = ", ".join(a.get("name", "Unknown") for a in artists)

        album_data = track.get("album") or {}
        album_name = album_data.get("name", "Unknown Album")

        # ytmusicapi doesn't always provide genre at track level
        # It may be available via album or category
        genre = ""
        if "category" in track:
            genre = track["category"]

        return {
            "title": track.get("title", "Unknown Title"),
            "artist": artist_name or "Unknown Artist",
            "album": album_name,
            "video_id": track.get("videoId", ""),
            "duration": track.get("duration", "0:00"),
            "genre": genre,
        }
