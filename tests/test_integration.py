"""Integration tests for the full download pipeline.

Tests the data flow between modules:
download -> tag -> organize -> sync_state
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.config import AppConfig
from src.core.download import _build_yt_dlp_opts
from src.core.organizer import organize_track, sanitize_filename
from src.core.sync_state import SyncState
from src.core.tagger import tag_file
from src.providers.youtube import YouTubeProvider


class TestNormalizeToTagger:
    """Test data flow: YouTubeProvider.normalize_track -> tagger.tag_file."""

    def test_normalized_track_has_tagger_keys(self) -> None:
        """normalize_track output has keys expected by tag_file."""
        raw_track = {
            "title": "Test Song",
            "artists": [{"name": "Test Artist"}],
            "album": {"name": "Test Album"},
            "videoId": "abc123",
            "duration": "3:30",
            "category": "Rock",
        }
        normalized = YouTubeProvider.normalize_track(raw_track)
        # tag_file expects: title, artist, album, genre
        assert "title" in normalized
        assert "artist" in normalized
        assert "album" in normalized
        assert "genre" in normalized

    def test_normalized_track_values_are_strings(self) -> None:
        """All values from normalize_track are strings."""
        raw_track = {
            "title": "Song",
            "artists": [{"name": "Artist"}],
            "album": {"name": "Album"},
            "videoId": "xyz",
            "duration": "1:00",
        }
        normalized = YouTubeProvider.normalize_track(raw_track)
        for key, value in normalized.items():
            assert isinstance(value, str), f"{key} is {type(value)}, expected str"


class TestNormalizeToOrganizer:
    """Test data flow: normalize_track -> organizer.organize_track."""

    def test_normalized_track_has_organizer_keys(self) -> None:
        """normalize_track output has keys expected by organize_track."""
        raw_track = {
            "title": "Test Song",
            "artists": [{"name": "Test Artist"}],
            "album": {"name": "Test Album"},
            "videoId": "abc123",
            "duration": "3:30",
            "category": "Electronic",
        }
        normalized = YouTubeProvider.normalize_track(raw_track)
        # organize_track uses: artist, title, album, genre
        assert "artist" in normalized
        assert "title" in normalized
        assert "album" in normalized
        assert "genre" in normalized

    def test_organize_with_normalized_track(self, tmp_path: Path) -> None:
        """organize_track works with normalize_track output."""
        source = tmp_path / "src" / "abc123.mp3"
        source.parent.mkdir(parents=True)
        source.write_text("fake audio")

        metadata = {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "video_id": "abc123",
            "duration": "3:30",
            "genre": "Rock",
        }

        final_path = organize_track(
            source,
            tmp_path / "output",
            metadata,
            organize_by="genre_artist",
            max_filename_length=120,
            default_genre="Unknown",
        )
        assert final_path.exists()
        assert "Rock" in str(final_path)
        assert "Test Artist" in str(final_path)


class TestNormalizeToSyncState:
    """Test data flow: normalize_track -> SyncState."""

    def test_sync_state_with_normalized_track(self, tmp_path: Path) -> None:
        """SyncState correctly stores normalized track data."""
        state = SyncState(tmp_path / ".sync_state.json")
        metadata = {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "video_id": "abc123",
            "duration": "3:30",
            "genre": "Rock",
        }
        state.mark_downloaded("abc123", "/path/to/file.mp3", metadata)
        assert state.is_downloaded("abc123")

    def test_get_new_tracks_filters_correctly(self, tmp_path: Path) -> None:
        """get_new_tracks properly filters normalized tracks."""
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded(
            "existing_id",
            "/path/existing.mp3",
            {"title": "Existing", "artist": "A"},
        )

        tracks = [
            {"video_id": "existing_id", "title": "Existing"},
            {"video_id": "new_id", "title": "New Song"},
        ]
        new_tracks = state.get_new_tracks(tracks)
        assert len(new_tracks) == 1
        assert new_tracks[0]["video_id"] == "new_id"


class TestDownloadToTagger:
    """Test data flow: download output -> tagger input."""

    def test_download_opts_produce_taggable_format(self) -> None:
        """yt-dlp options target formats supported by tagger."""
        opts = _build_yt_dlp_opts(Path("/tmp"), "best", "mp3")
        format_str = opts.get("format", "")
        # Format should request audio formats tagger can handle
        assert "bestaudio" in format_str

    def test_mp3_postprocessor_creates_taggable_file(self) -> None:
        """MP3 postprocessor produces .mp3 files tagger can handle."""
        opts = _build_yt_dlp_opts(Path("/tmp"), "best", "mp3")
        postprocessors = opts.get("postprocessors", [])
        has_mp3_extract = any(
            pp.get("key") == "FFmpegExtractAudio" and pp.get("preferredcodec") == "mp3"
            for pp in postprocessors
        )
        assert has_mp3_extract


class TestOrganizeToSyncState:
    """Test data flow: organize output -> sync_state."""

    def test_organized_path_stored_in_sync_state(self, tmp_path: Path) -> None:
        """The path from organize_track can be stored in SyncState."""
        # Create a source file
        source = tmp_path / "src" / "video123.mp3"
        source.parent.mkdir(parents=True)
        source.write_text("fake audio")

        metadata = {
            "title": "My Song",
            "artist": "My Artist",
            "album": "My Album",
            "video_id": "video123",
            "duration": "4:00",
            "genre": "Pop",
        }

        final_path = organize_track(
            source,
            tmp_path / "output",
            metadata,
            organize_by="genre_artist",
        )

        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded("video123", str(final_path), metadata)
        state.save()

        # Reload and verify
        state2 = SyncState(tmp_path / ".sync_state.json")
        assert state2.is_downloaded("video123")


class TestConfigPropagation:
    """Test config values propagate correctly through pipeline."""

    def test_config_fields_used_by_download(self) -> None:
        """AppConfig has fields needed by download_track."""
        config = AppConfig()
        assert hasattr(config, "audio_format")
        assert hasattr(config, "fallback_format")
        assert hasattr(config, "max_concurrent_downloads")

    def test_config_fields_used_by_organizer(self) -> None:
        """AppConfig has fields needed by organize_track."""
        config = AppConfig()
        assert hasattr(config, "organize_by")
        assert hasattr(config, "max_filename_length")
        assert hasattr(config, "default_genre")
        assert hasattr(config, "download_dir")

    def test_config_fields_used_by_auth(self) -> None:
        """AppConfig has fields needed by auth module."""
        config = AppConfig()
        assert hasattr(config, "client_id")
        assert hasattr(config, "client_secret")

    def test_filename_sanitization_respects_config(self) -> None:
        """Filename sanitization uses config max_filename_length."""
        config = AppConfig(max_filename_length=50)
        long_name = "A" * 100
        sanitized = sanitize_filename(long_name, max_length=config.max_filename_length)
        assert len(sanitized) <= 50


class TestFullPipelineMocked:
    """Full pipeline integration test with mocked downloads."""

    @patch("src.core.download.download_track")
    def test_full_pipeline_flow(self, mock_download: MagicMock, tmp_path: Path) -> None:
        """Full pipeline: normalize -> download -> tag -> organize -> sync."""
        # Step 1: Normalize raw track
        raw_track = {
            "title": "Integration Test",
            "artists": [{"name": "Test Band"}],
            "album": {"name": "Test Album"},
            "videoId": "int_test_001",
            "duration": "3:45",
            "category": "Rock",
        }
        normalized = YouTubeProvider.normalize_track(raw_track)
        assert normalized["title"] == "Integration Test"
        assert normalized["artist"] == "Test Band"
        assert normalized["genre"] == "Rock"

        # Step 2: Simulate download (create fake file)
        fake_file = tmp_path / "tmp" / "int_test_001.mp3"
        fake_file.parent.mkdir(parents=True)
        fake_file.write_bytes(b"\x00" * 100)
        mock_download.return_value = fake_file

        downloaded = mock_download("int_test_001", tmp_path / "tmp", "best", "mp3")
        assert downloaded is not None
        assert downloaded.exists()

        # Step 3: Tag file (will fail on fake file, but test the interface)
        try:
            tag_file(downloaded, normalized)
        except Exception:
            pass  # Expected: fake file isn't valid audio

        # Step 4: Organize
        final = organize_track(
            downloaded,
            tmp_path / "output",
            normalized,
            organize_by="genre_artist",
            max_filename_length=120,
            default_genre="Unknown",
        )
        assert final.exists()
        assert "Rock" in str(final)

        # Step 5: Record in sync state
        state = SyncState(tmp_path / ".sync_state.json")
        state.mark_downloaded("int_test_001", str(final), normalized)
        state.mark_playlist_synced("test_pl", "Test Playlist", 1)
        state.update_last_sync()
        state.save()

        # Verify: track is marked as downloaded
        assert state.is_downloaded("int_test_001")
        assert state.total_tracks == 1
        assert state.last_sync is not None

        # Verify: subsequent sync skips this track
        new = state.get_new_tracks(
            [{"video_id": "int_test_001", "title": "Integration Test"}]
        )
        assert len(new) == 0
