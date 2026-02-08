"""Tests for metadata tagger."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import MetadataError
from src.core.tagger import tag_file


class TestTagFile:
    """Tests for audio file tagging."""

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """MetadataError raised for nonexistent file."""
        with pytest.raises(MetadataError, match="File not found"):
            tag_file(
                tmp_path / "nonexistent.mp3",
                {"title": "Song", "artist": "Artist"},
            )

    @patch("src.core.tagger._tag_mp3")
    def test_mp3_file_dispatched(self, mock_tag: MagicMock, tmp_path: Path) -> None:
        """MP3 files are dispatched to _tag_mp3."""
        mp3_file = tmp_path / "song.mp3"
        mp3_file.write_bytes(b"fake")

        metadata = {"title": "Song", "artist": "Artist"}
        tag_file(mp3_file, metadata)

        mock_tag.assert_called_once_with(mp3_file, metadata, None)

    @patch("src.core.tagger._tag_m4a")
    def test_m4a_file_dispatched(self, mock_tag: MagicMock, tmp_path: Path) -> None:
        """M4A files are dispatched to _tag_m4a."""
        m4a_file = tmp_path / "song.m4a"
        m4a_file.write_bytes(b"fake")

        metadata = {"title": "Song", "artist": "Artist"}
        tag_file(m4a_file, metadata)

        mock_tag.assert_called_once_with(m4a_file, metadata, None)

    @patch("src.core.tagger._tag_m4a")
    def test_mp4_file_dispatched(self, mock_tag: MagicMock, tmp_path: Path) -> None:
        """MP4 files are dispatched to _tag_m4a."""
        mp4_file = tmp_path / "song.mp4"
        mp4_file.write_bytes(b"fake")

        metadata = {"title": "Song", "artist": "Artist"}
        tag_file(mp4_file, metadata)

        mock_tag.assert_called_once_with(mp4_file, metadata, None)

    @patch("src.core.tagger._tag_m4a")
    def test_aac_file_dispatched(self, mock_tag: MagicMock, tmp_path: Path) -> None:
        """AAC files are dispatched to _tag_m4a."""
        aac_file = tmp_path / "song.aac"
        aac_file.write_bytes(b"fake")

        metadata = {"title": "Song", "artist": "Artist"}
        tag_file(aac_file, metadata)

        mock_tag.assert_called_once_with(aac_file, metadata, None)

    @patch("src.core.tagger._tag_generic")
    def test_ogg_file_dispatched(self, mock_tag: MagicMock, tmp_path: Path) -> None:
        """OGG files are dispatched to _tag_generic."""
        ogg_file = tmp_path / "song.ogg"
        ogg_file.write_bytes(b"fake")

        metadata = {"title": "Song", "artist": "Artist"}
        tag_file(ogg_file, metadata)

        mock_tag.assert_called_once_with(ogg_file, metadata)

    @patch("src.core.tagger._tag_generic")
    def test_opus_file_dispatched(self, mock_tag: MagicMock, tmp_path: Path) -> None:
        """Opus files are dispatched to _tag_generic."""
        opus_file = tmp_path / "song.opus"
        opus_file.write_bytes(b"fake")

        metadata = {"title": "Song", "artist": "Artist"}
        tag_file(opus_file, metadata)

        mock_tag.assert_called_once_with(opus_file, metadata)

    @patch("src.core.tagger._tag_generic")
    def test_webm_file_dispatched(self, mock_tag: MagicMock, tmp_path: Path) -> None:
        """WebM files are dispatched to _tag_generic."""
        webm_file = tmp_path / "song.webm"
        webm_file.write_bytes(b"fake")

        metadata = {"title": "Song", "artist": "Artist"}
        tag_file(webm_file, metadata)

        mock_tag.assert_called_once_with(webm_file, metadata)

    @patch("src.core.tagger._tag_mp3")
    def test_cover_path_passed(self, mock_tag: MagicMock, tmp_path: Path) -> None:
        """Cover path is forwarded to format-specific tagger."""
        mp3_file = tmp_path / "song.mp3"
        mp3_file.write_bytes(b"fake")
        cover = tmp_path / "cover.jpg"
        cover.write_bytes(b"fake image")

        metadata = {"title": "Song", "artist": "Artist"}
        tag_file(mp3_file, metadata, cover_path=cover)

        mock_tag.assert_called_once_with(mp3_file, metadata, cover)

    @patch("src.core.tagger._tag_mp3")
    def test_tagger_exception_wrapped(
        self, mock_tag: MagicMock, tmp_path: Path
    ) -> None:
        """Exceptions from format taggers are wrapped in MetadataError."""
        mp3_file = tmp_path / "song.mp3"
        mp3_file.write_bytes(b"fake")
        mock_tag.side_effect = ValueError("Corrupt file")

        with pytest.raises(MetadataError, match="Failed to tag"):
            tag_file(mp3_file, {"title": "Song", "artist": "Artist"})
