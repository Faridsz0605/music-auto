"""Tests for sync state management."""

import json
from pathlib import Path

from src.core.sync_state import SyncState


class TestSyncState:
    """Tests for SyncState class."""

    def test_empty_state(self, tmp_path: Path) -> None:
        """New state has zero tracks and no last sync."""
        state = SyncState(tmp_path / ".sync_state.json")
        assert state.total_tracks == 0
        assert state.last_sync is None

    def test_mark_downloaded(self, tmp_path: Path) -> None:
        """Tracks can be marked as downloaded."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded(
            "vid1",
            "/path/to/song.mp3",
            {"title": "Song", "artist": "Artist"},
        )
        assert state.is_downloaded("vid1")
        assert not state.is_downloaded("vid2")
        assert state.total_tracks == 1

    def test_mark_downloaded_stores_metadata(self, tmp_path: Path) -> None:
        """Downloaded track stores title and artist from metadata."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded(
            "vid1",
            "/path/to/song.mp3",
            {"title": "My Song", "artist": "My Artist"},
        )
        state.save()

        data = json.loads((tmp_path / ".sync_state.json").read_text())
        track = data["tracks"]["vid1"]
        assert track["title"] == "My Song"
        assert track["artist"] == "My Artist"
        assert track["filepath"] == "/path/to/song.mp3"
        assert "downloaded_at" in track

    def test_save_and_reload(self, tmp_path: Path) -> None:
        """State persists across reloads."""
        state_file = tmp_path / ".sync_state.json"

        state = SyncState(state_file)
        state.mark_downloaded("vid1", "/path/song.mp3", {"title": "S"})
        state.save()

        # Reload from disk
        state2 = SyncState(state_file)
        assert state2.is_downloaded("vid1")
        assert state2.total_tracks == 1

    def test_get_new_tracks(self, tmp_path: Path) -> None:
        """Filters out already downloaded tracks."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded("vid1", "/a.mp3", {"title": "A"})

        tracks: list[dict[str, str]] = [
            {"video_id": "vid1", "title": "A"},
            {"video_id": "vid2", "title": "B"},
            {"video_id": "vid3", "title": "C"},
        ]

        new = state.get_new_tracks(tracks)
        assert len(new) == 2
        assert all(t["video_id"] != "vid1" for t in new)

    def test_get_new_tracks_all_new(self, tmp_path: Path) -> None:
        """Returns all tracks when none are downloaded."""
        state = SyncState(tmp_path / ".sync_state.json")
        tracks: list[dict[str, str]] = [
            {"video_id": "vid1", "title": "A"},
            {"video_id": "vid2", "title": "B"},
        ]
        new = state.get_new_tracks(tracks)
        assert len(new) == 2

    def test_get_new_tracks_none_new(self, tmp_path: Path) -> None:
        """Returns empty list when all are downloaded."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded("vid1", "/a.mp3", {"title": "A"})
        state.mark_downloaded("vid2", "/b.mp3", {"title": "B"})

        tracks: list[dict[str, str]] = [
            {"video_id": "vid1", "title": "A"},
            {"video_id": "vid2", "title": "B"},
        ]
        new = state.get_new_tracks(tracks)
        assert len(new) == 0

    def test_get_orphaned_tracks(self, tmp_path: Path) -> None:
        """Detects tracks no longer in remote playlists."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded("vid1", "/a.mp3", {"title": "A"})
        state.mark_downloaded("vid2", "/b.mp3", {"title": "B"})
        state.mark_downloaded("vid3", "/c.mp3", {"title": "C"})

        # Only vid1 and vid3 are still in the playlist
        current = {"vid1", "vid3"}
        orphaned = state.get_orphaned_tracks(current)

        assert len(orphaned) == 1
        assert orphaned[0]["video_id"] == "vid2"

    def test_get_orphaned_tracks_none(self, tmp_path: Path) -> None:
        """Returns empty list when no tracks are orphaned."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded("vid1", "/a.mp3", {"title": "A"})

        orphaned = state.get_orphaned_tracks({"vid1"})
        assert len(orphaned) == 0

    def test_remove_track(self, tmp_path: Path) -> None:
        """Tracks can be removed from state."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded("vid1", "/a.mp3", {"title": "A"})
        assert state.is_downloaded("vid1")

        state.remove_track("vid1")
        assert not state.is_downloaded("vid1")
        assert state.total_tracks == 0

    def test_remove_nonexistent_track(self, tmp_path: Path) -> None:
        """Removing a nonexistent track doesn't crash."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.remove_track("nonexistent")
        assert state.total_tracks == 0

    def test_mark_playlist_synced(self, tmp_path: Path) -> None:
        """Playlist sync info is recorded."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_playlist_synced("PL001", "Rock Mix", 50)

        playlists = state.synced_playlists
        assert "PL001" in playlists
        assert playlists["PL001"]["name"] == "Rock Mix"
        assert playlists["PL001"]["track_count"] == 50
        assert "last_sync" in playlists["PL001"]

    def test_mark_multiple_playlists(self, tmp_path: Path) -> None:
        """Multiple playlists can be tracked."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_playlist_synced("PL001", "Rock", 50)
        state.mark_playlist_synced("PL002", "Pop", 30)

        playlists = state.synced_playlists
        assert len(playlists) == 2
        assert playlists["PL001"]["name"] == "Rock"
        assert playlists["PL002"]["name"] == "Pop"

    def test_update_last_sync(self, tmp_path: Path) -> None:
        """Last sync timestamp is updated."""
        state = SyncState(tmp_path / ".sync_state.json")
        assert state.last_sync is None

        state.update_last_sync()
        assert state.last_sync is not None
        assert isinstance(state.last_sync, str)

    def test_corrupt_state_file(self, tmp_path: Path) -> None:
        """Corrupt state file is handled gracefully."""
        state_file = tmp_path / ".sync_state.json"
        state_file.write_text("not valid json{{{")

        state = SyncState(state_file)
        assert state.total_tracks == 0
        assert state.last_sync is None

    def test_state_version(self, tmp_path: Path) -> None:
        """New state includes version field."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.save()

        data = json.loads((tmp_path / ".sync_state.json").read_text())
        assert data["version"] == 1

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Save creates parent directories if needed."""
        state_file = tmp_path / "nested" / "dir" / ".sync_state.json"
        state = SyncState(state_file)
        state.mark_downloaded("vid1", "/a.mp3", {"title": "A"})
        state.save()

        assert state_file.exists()
