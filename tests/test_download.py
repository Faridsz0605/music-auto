"""Tests for download engine."""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.core.download import (
    BEST_AUDIO_FORMAT,
    _build_yt_dlp_opts,
    _is_retryable_error,
    download_tracks_parallel,
)
from src.core.exceptions import DownloadError


class TestBuildYtDlpOpts:
    """Tests for yt-dlp options builder."""

    def test_default_opts(self, tmp_path: Path) -> None:
        """Default options include best audio format."""
        opts = _build_yt_dlp_opts(tmp_path)
        assert "bestaudio" in opts["format"]
        assert opts["quiet"] is True
        assert opts["writethumbnail"] is True

    def test_format_matches_constant(self, tmp_path: Path) -> None:
        """Default format matches BEST_AUDIO_FORMAT constant."""
        opts = _build_yt_dlp_opts(tmp_path)
        assert opts["format"] == BEST_AUDIO_FORMAT

    def test_mp3_postprocessor(self, tmp_path: Path) -> None:
        """MP3 fallback adds FFmpeg audio extraction postprocessor."""
        opts = _build_yt_dlp_opts(tmp_path, fallback_format="mp3")
        codecs = [
            p.get("preferredcodec")
            for p in opts["postprocessors"]
            if "preferredcodec" in p
        ]
        assert "mp3" in codecs

    def test_output_template(self, tmp_path: Path) -> None:
        """Output template uses video ID."""
        opts = _build_yt_dlp_opts(tmp_path)
        assert "%(id)s" in opts["outtmpl"]

    def test_output_template_uses_output_path(self, tmp_path: Path) -> None:
        """Output template includes the output directory."""
        opts = _build_yt_dlp_opts(tmp_path)
        assert str(tmp_path) in opts["outtmpl"]

    def test_includes_metadata_postprocessor(self, tmp_path: Path) -> None:
        """Options include FFmpegMetadata postprocessor."""
        opts = _build_yt_dlp_opts(tmp_path)
        keys = [p["key"] for p in opts["postprocessors"]]
        assert "FFmpegMetadata" in keys

    def test_includes_embed_thumbnail(self, tmp_path: Path) -> None:
        """Options include EmbedThumbnail postprocessor."""
        opts = _build_yt_dlp_opts(tmp_path)
        keys = [p["key"] for p in opts["postprocessors"]]
        assert "EmbedThumbnail" in keys

    def test_no_warnings(self, tmp_path: Path) -> None:
        """Warnings are suppressed."""
        opts = _build_yt_dlp_opts(tmp_path)
        assert opts["no_warnings"] is True


class TestDownloadTrack:
    """Tests for single track download.

    yt_dlp is imported locally inside download_track(), so we must
    inject a mock via sys.modules before importing the function.
    """

    def _make_mock_yt_dlp(self) -> tuple[MagicMock, MagicMock]:
        """Create a mock yt_dlp module with YoutubeDL context manager."""
        mock_module = MagicMock()
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_module.YoutubeDL.return_value = mock_ydl
        return mock_module, mock_ydl

    def test_successful_download_mp3(self, tmp_path: Path) -> None:
        """Successful download returns path to mp3 file."""
        mock_module, mock_ydl = self._make_mock_yt_dlp()
        mock_ydl.extract_info.return_value = {"id": "testid"}

        # Create fake downloaded file
        fake_file = tmp_path / "testid.mp3"
        fake_file.write_bytes(b"fake audio")

        with patch.dict(sys.modules, {"yt_dlp": mock_module}):
            from src.core.download import download_track

            result = download_track("testid", tmp_path)

        assert result == fake_file

    def test_successful_download_m4a(self, tmp_path: Path) -> None:
        """Successful download returns path to m4a file."""
        mock_module, mock_ydl = self._make_mock_yt_dlp()
        mock_ydl.extract_info.return_value = {"id": "testid"}

        fake_file = tmp_path / "testid.m4a"
        fake_file.write_bytes(b"fake audio")

        with patch.dict(sys.modules, {"yt_dlp": mock_module}):
            from src.core.download import download_track

            result = download_track("testid", tmp_path)

        assert result == fake_file

    def test_download_failure_raises(self, tmp_path: Path) -> None:
        """Download failure raises DownloadError."""
        mock_module, mock_ydl = self._make_mock_yt_dlp()
        mock_ydl.extract_info.side_effect = Exception("Network error")

        with patch.dict(sys.modules, {"yt_dlp": mock_module}):
            from src.core.download import download_track

            with pytest.raises(DownloadError, match="Failed to download"):
                download_track("badid", tmp_path)

    def test_no_info_extracted_raises(self, tmp_path: Path) -> None:
        """None info raises DownloadError."""
        mock_module, mock_ydl = self._make_mock_yt_dlp()
        mock_ydl.extract_info.return_value = None

        with patch.dict(sys.modules, {"yt_dlp": mock_module}):
            from src.core.download import download_track

            with pytest.raises(DownloadError, match="No info extracted"):
                download_track("testid", tmp_path)

    def test_file_not_found_after_download(self, tmp_path: Path) -> None:
        """DownloadError when no file appears after extraction."""
        mock_module, mock_ydl = self._make_mock_yt_dlp()
        mock_ydl.extract_info.return_value = {"id": "testid"}

        # No file created on disk
        with patch.dict(sys.modules, {"yt_dlp": mock_module}):
            from src.core.download import download_track

            with pytest.raises(DownloadError, match="file not found"):
                download_track("testid", tmp_path)

    def test_creates_output_dir(self, tmp_path: Path) -> None:
        """Output directory is created if it doesn't exist."""
        mock_module, mock_ydl = self._make_mock_yt_dlp()

        output = tmp_path / "nested" / "dir"

        def create_file(*args: Any, **kwargs: Any) -> dict[str, str]:
            output.mkdir(parents=True, exist_ok=True)
            (output / "testid.mp3").write_bytes(b"data")
            return {"id": "testid"}

        mock_ydl.extract_info.side_effect = create_file

        with patch.dict(sys.modules, {"yt_dlp": mock_module}):
            from src.core.download import download_track

            result = download_track("testid", output)

        assert result == output / "testid.mp3"


class TestDownloadTracksParallel:
    """Tests for parallel download."""

    @patch("src.core.download.download_track")
    def test_parallel_downloads(self, mock_download: MagicMock, tmp_path: Path) -> None:
        """Parallel download processes multiple tracks."""
        mock_download.return_value = tmp_path / "song.mp3"

        tracks: list[dict[str, str]] = [
            {"video_id": "vid1", "title": "Song 1"},
            {"video_id": "vid2", "title": "Song 2"},
        ]

        results = download_tracks_parallel(tracks, tmp_path, max_workers=2)

        assert len(results) == 2
        assert mock_download.call_count == 2

    @patch("src.core.download.download_track")
    def test_missing_video_id(self, mock_download: MagicMock, tmp_path: Path) -> None:
        """Tracks without video_id are reported as errors."""
        tracks: list[dict[str, str]] = [{"title": "No ID Track"}]
        results = download_tracks_parallel(tracks, tmp_path)

        assert len(results) == 1
        assert results[0]["error"] == "Missing video_id"
        assert results[0]["filepath"] is None
        mock_download.assert_not_called()

    @patch("src.core.download.download_track")
    def test_partial_failure(self, mock_download: MagicMock, tmp_path: Path) -> None:
        """One failed download doesn't block others."""

        def side_effect(video_id: str, *args: Any, **kwargs: Any) -> Path:
            if video_id == "bad":
                raise DownloadError("Failed to download bad")
            return tmp_path / f"{video_id}.mp3"

        mock_download.side_effect = side_effect

        tracks: list[dict[str, str]] = [
            {"video_id": "good", "title": "Good Song"},
            {"video_id": "bad", "title": "Bad Song"},
        ]

        results = download_tracks_parallel(tracks, tmp_path, max_workers=2)
        assert len(results) == 2

        errors = [r for r in results if r["error"] is not None]
        successes = [r for r in results if r["error"] is None]
        assert len(errors) == 1
        assert len(successes) == 1

    @patch("src.core.download.download_track")
    def test_progress_callback(self, mock_download: MagicMock, tmp_path: Path) -> None:
        """Progress callback is called for each track."""
        mock_download.return_value = tmp_path / "song.mp3"
        callback = MagicMock()

        tracks: list[dict[str, str]] = [
            {"video_id": "vid1", "title": "Song 1"},
        ]

        download_tracks_parallel(tracks, tmp_path, progress_callback=callback)

        callback.assert_called_once()

    @patch("src.core.download.download_track")
    def test_empty_tracks_list(self, mock_download: MagicMock, tmp_path: Path) -> None:
        """Empty tracks list returns empty results."""
        results = download_tracks_parallel([], tmp_path)
        assert results == []
        mock_download.assert_not_called()


class TestIsRetryableError:
    """Tests for retry error classification."""

    def test_403_error(self) -> None:
        """HTTP 403 is retryable."""
        assert _is_retryable_error(Exception("HTTP Error 403: Forbidden")) is True

    def test_429_error(self) -> None:
        """HTTP 429 rate limit is retryable."""
        assert _is_retryable_error(Exception("HTTP Error 429")) is True

    def test_connection_error(self) -> None:
        """Connection errors are retryable."""
        assert _is_retryable_error(Exception("Connection reset")) is True

    def test_timeout_error(self) -> None:
        """Timeout errors are retryable."""
        assert _is_retryable_error(Exception("Request timeout")) is True

    def test_non_retryable_error(self) -> None:
        """Permanent errors are not retryable."""
        assert _is_retryable_error(Exception("Video not found")) is False

    def test_format_error(self) -> None:
        """Format errors are not retryable."""
        assert _is_retryable_error(Exception("No suitable format")) is False


class TestDownloadTrackRetry:
    """Tests for download retry with exponential backoff."""

    def _make_mock_yt_dlp(self) -> tuple[MagicMock, MagicMock]:
        """Create a mock yt_dlp module with YoutubeDL context manager."""
        mock_module = MagicMock()
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_module.YoutubeDL.return_value = mock_ydl
        return mock_module, mock_ydl

    @patch("src.core.download.time.sleep")
    def test_retry_on_transient_error(
        self, mock_sleep: MagicMock, tmp_path: Path
    ) -> None:
        """Retries on transient 403 error, then succeeds."""
        mock_module, mock_ydl = self._make_mock_yt_dlp()

        call_count = 0

        def extract_side_effect(*args: Any, **kwargs: Any) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("HTTP Error 403: Forbidden")
            # Second attempt succeeds
            (tmp_path / "testid.mp3").write_bytes(b"audio")
            return {"id": "testid"}

        mock_ydl.extract_info.side_effect = extract_side_effect

        with patch.dict(sys.modules, {"yt_dlp": mock_module}):
            from src.core.download import download_track

            result = download_track("testid", tmp_path, max_retries=3)

        assert result == tmp_path / "testid.mp3"
        mock_sleep.assert_called_once()

    @patch("src.core.download.time.sleep")
    def test_no_retry_on_permanent_error(
        self, mock_sleep: MagicMock, tmp_path: Path
    ) -> None:
        """Does not retry on permanent (non-transient) errors."""
        mock_module, mock_ydl = self._make_mock_yt_dlp()
        mock_ydl.extract_info.side_effect = Exception("Video not found")

        with patch.dict(sys.modules, {"yt_dlp": mock_module}):
            from src.core.download import download_track

            with pytest.raises(DownloadError, match="Failed to download"):
                download_track("badid", tmp_path, max_retries=3)

        mock_sleep.assert_not_called()

    @patch("src.core.download.time.sleep")
    def test_exhausts_all_retries(
        self, mock_sleep: MagicMock, tmp_path: Path
    ) -> None:
        """Raises after exhausting all retry attempts."""
        mock_module, mock_ydl = self._make_mock_yt_dlp()
        mock_ydl.extract_info.side_effect = Exception("HTTP Error 429")

        with patch.dict(sys.modules, {"yt_dlp": mock_module}):
            from src.core.download import download_track

            with pytest.raises(DownloadError, match="after.*attempts"):
                download_track("testid", tmp_path, max_retries=2)

        # Should have slept for each retry attempt
        assert mock_sleep.call_count == 2
