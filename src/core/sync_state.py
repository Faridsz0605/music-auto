"""Sync state management for incremental downloads."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SyncState:
    """
    Manages the state of synced tracks for incremental downloads.

    Tracks which songs have been downloaded to avoid re-downloading.
    State is persisted as a JSON file alongside the downloads.
    """

    def __init__(self, state_file: Path) -> None:
        self._file = state_file
        self._state: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """Load state from disk."""
        if self._file.exists():
            try:
                data: dict[str, Any] = json.loads(self._file.read_text())
                return data
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load sync state: {e}")
        return {
            "version": 1,
            "last_sync": None,
            "tracks": {},
            "playlists": {},
        }

    def save(self) -> None:
        """Persist state to disk."""
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(self._state, indent=2, default=str) + "\n")

    def is_downloaded(self, video_id: str) -> bool:
        """Check if a track has already been downloaded."""
        return video_id in self._state.get("tracks", {})

    def mark_downloaded(
        self,
        video_id: str,
        filepath: str,
        metadata: dict[str, str],
    ) -> None:
        """
        Mark a track as downloaded.

        Args:
            video_id: YouTube video ID.
            filepath: Path where file was saved.
            metadata: Track metadata for reference.
        """
        if "tracks" not in self._state:
            self._state["tracks"] = {}

        self._state["tracks"][video_id] = {
            "filepath": filepath,
            "title": metadata.get("title", ""),
            "artist": metadata.get("artist", ""),
            "downloaded_at": (datetime.now(UTC).isoformat()),
        }

    def mark_playlist_synced(
        self,
        playlist_id: str,
        playlist_name: str,
        track_count: int,
    ) -> None:
        """Record that a playlist was synced."""
        if "playlists" not in self._state:
            self._state["playlists"] = {}

        self._state["playlists"][playlist_id] = {
            "name": playlist_name,
            "track_count": track_count,
            "last_sync": (datetime.now(UTC).isoformat()),
        }

    def update_last_sync(self) -> None:
        """Update the global last sync timestamp."""
        self._state["last_sync"] = datetime.now(UTC).isoformat()

    def get_new_tracks(self, tracks: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        Filter tracks to only those not yet downloaded.

        Args:
            tracks: List of normalized track dicts with 'video_id'.

        Returns:
            List of tracks that need downloading.
        """
        return [t for t in tracks if not self.is_downloaded(t.get("video_id", ""))]

    def get_orphaned_tracks(self, current_video_ids: set[str]) -> list[dict[str, Any]]:
        """
        Find tracks in state that are no longer in the remote
        playlist.

        Args:
            current_video_ids: Set of video IDs currently in
                playlists.

        Returns:
            List of orphaned track entries from state.
        """
        orphaned: list[dict[str, Any]] = []
        for vid, info in self._state.get("tracks", {}).items():
            if vid not in current_video_ids:
                orphaned.append({"video_id": vid, **info})
        return orphaned

    def remove_track(self, video_id: str) -> None:
        """Remove a track from the sync state."""
        tracks = self._state.get("tracks", {})
        if video_id in tracks:
            del tracks[video_id]

    @property
    def last_sync(self) -> str | None:
        """Get last sync timestamp."""
        result: str | None = self._state.get("last_sync")
        return result

    @property
    def total_tracks(self) -> int:
        """Get total number of synced tracks."""
        return len(self._state.get("tracks", {}))

    @property
    def synced_playlists(self) -> dict[str, Any]:
        """Get synced playlists info."""
        result: dict[str, Any] = self._state.get("playlists", {})
        return result
