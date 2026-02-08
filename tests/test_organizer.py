"""Tests for file organizer module."""

from pathlib import Path

import pytest

from src.core.exceptions import OrganizationError
from src.core.organizer import (
    cleanup_temp_dir,
    organize_track,
    sanitize_dirname,
    sanitize_filename,
)


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_basic_name(self) -> None:
        """Clean name passes through unchanged."""
        assert sanitize_filename("My Song") == "My Song"

    def test_invalid_chars_removed(self) -> None:
        """Invalid filesystem chars are removed."""
        result = sanitize_filename('Song: "Remix" <2024>')
        assert ":" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result

    def test_ampersand_replaced(self) -> None:
        """& is replaced with 'and'."""
        assert "and" in sanitize_filename("Tom & Jerry")

    def test_truncation(self) -> None:
        """Long names are truncated to max_length."""
        long_name = "A" * 200
        result = sanitize_filename(long_name, max_length=120)
        assert len(result) <= 120

    def test_whitespace_collapsed(self) -> None:
        """Multiple spaces are collapsed to one."""
        assert sanitize_filename("My   Song   Title") == "My Song Title"

    def test_empty_name_fallback(self) -> None:
        """Empty name returns 'Unknown'."""
        assert sanitize_filename("") == "Unknown"

    def test_whitespace_only_fallback(self) -> None:
        """Whitespace-only name returns 'Unknown'."""
        assert sanitize_filename("   ") == "Unknown"

    def test_leading_trailing_dots(self) -> None:
        """Leading/trailing dots are removed."""
        result = sanitize_filename("...Song...")
        assert not result.startswith(".")
        assert not result.endswith(".")

    def test_unicode_normalization(self) -> None:
        """Unicode characters are normalized without crashing."""
        result = sanitize_filename("Caf\u00e9 del Mar")
        assert len(result) > 0

    def test_null_bytes_removed(self) -> None:
        """Control characters are stripped."""
        result = sanitize_filename("Song\x00Name")
        assert "\x00" not in result

    def test_pipe_removed(self) -> None:
        """Pipe character is removed."""
        result = sanitize_filename("Song | Remix")
        assert "|" not in result

    def test_question_mark_removed(self) -> None:
        """Question mark is removed."""
        result = sanitize_filename("Why?")
        assert "?" not in result

    def test_multi_dash_collapsed(self) -> None:
        """Multiple dashes are collapsed."""
        result = sanitize_filename("Song --- Remix")
        assert "---" not in result


class TestSanitizeDirname:
    """Tests for directory name sanitization."""

    def test_max_length_shorter(self) -> None:
        """Dir names have shorter default max length of 80."""
        long_name = "A" * 100
        result = sanitize_dirname(long_name)
        assert len(result) <= 80

    def test_basic_dirname(self) -> None:
        """Clean directory name passes through."""
        assert sanitize_dirname("Rock") == "Rock"

    def test_invalid_chars_removed(self) -> None:
        """Invalid chars are removed from dir names too."""
        result = sanitize_dirname('Artist: "The Best"')
        assert ":" not in result
        assert '"' not in result


class TestOrganizeTrack:
    """Tests for track organization."""

    def test_genre_artist_structure(self, tmp_path: Path) -> None:
        """Files are organized as Genre/Artist/Artist - Title.ext."""
        source = tmp_path / "test.mp3"
        source.write_bytes(b"fake mp3 data")

        metadata = {
            "title": "My Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "genre": "Rock",
        }

        result = organize_track(
            source, tmp_path / "output", metadata, organize_by="genre_artist"
        )

        assert result.exists()
        assert "Rock" in str(result)
        assert "Test Artist" in str(result)
        assert "Test Artist - My Song" in result.name

    def test_artist_album_structure(self, tmp_path: Path) -> None:
        """Files organized as Artist/Album/filename."""
        source = tmp_path / "test.mp3"
        source.write_bytes(b"fake mp3 data")

        metadata = {
            "title": "Song",
            "artist": "Artist",
            "album": "Album",
            "genre": "Pop",
        }

        result = organize_track(
            source, tmp_path / "output", metadata, organize_by="artist_album"
        )

        assert result.exists()
        assert "Artist" in str(result)
        assert "Album" in str(result)

    def test_playlist_structure(self, tmp_path: Path) -> None:
        """Files organized as Playlist/filename."""
        source = tmp_path / "test.mp3"
        source.write_bytes(b"fake mp3 data")

        metadata = {
            "title": "Song",
            "artist": "Artist",
            "genre": "Pop",
            "playlist": "My Playlist",
        }

        result = organize_track(
            source, tmp_path / "output", metadata, organize_by="playlist"
        )

        assert result.exists()
        assert "My Playlist" in str(result)

    def test_default_genre_used(self, tmp_path: Path) -> None:
        """Default genre is used when genre is empty."""
        source = tmp_path / "test.mp3"
        source.write_bytes(b"fake mp3 data")

        metadata = {
            "title": "Song",
            "artist": "Artist",
            "album": "Album",
            "genre": "",
        }

        result = organize_track(
            source,
            tmp_path / "output",
            metadata,
            default_genre="Various",
        )

        assert result.exists()
        assert "Various" in str(result)

    def test_duplicate_handling(self, tmp_path: Path) -> None:
        """Duplicate files get a counter suffix."""
        output = tmp_path / "output"

        # Create first file
        source1 = tmp_path / "test1.mp3"
        source1.write_bytes(b"data1")
        metadata = {"title": "Song", "artist": "Artist", "genre": "Rock"}
        result1 = organize_track(source1, output, metadata)

        # Create second file with same metadata
        source2 = tmp_path / "test2.mp3"
        source2.write_bytes(b"data2")
        result2 = organize_track(source2, output, metadata)

        assert result1 != result2
        assert result1.exists()
        assert result2.exists()
        assert "(1)" in result2.name

    def test_source_not_found_raises(self, tmp_path: Path) -> None:
        """OrganizationError raised for missing source."""
        with pytest.raises(OrganizationError, match="Source file not found"):
            organize_track(
                tmp_path / "nonexistent.mp3",
                tmp_path / "output",
                {"title": "X", "artist": "Y"},
            )

    def test_filename_truncation(self, tmp_path: Path) -> None:
        """Long filenames are truncated to max length."""
        source = tmp_path / "test.mp3"
        source.write_bytes(b"data")

        metadata = {
            "title": "A" * 200,
            "artist": "B" * 50,
            "genre": "Rock",
        }

        result = organize_track(
            source,
            tmp_path / "output",
            metadata,
            max_filename_length=80,
        )

        assert result.exists()
        assert len(result.name) <= 80

    def test_preserves_file_extension(self, tmp_path: Path) -> None:
        """File extension is preserved during organization."""
        source = tmp_path / "test.m4a"
        source.write_bytes(b"data")

        metadata = {"title": "Song", "artist": "Artist", "genre": "Rock"}
        result = organize_track(source, tmp_path / "output", metadata)

        assert result.suffix == ".m4a"

    def test_source_removed_after_move(self, tmp_path: Path) -> None:
        """Source file no longer exists after organization."""
        source = tmp_path / "test.mp3"
        source.write_bytes(b"data")

        metadata = {"title": "Song", "artist": "Artist", "genre": "Rock"}
        organize_track(source, tmp_path / "output", metadata)

        assert not source.exists()


class TestCleanupTempDir:
    """Tests for temp directory cleanup."""

    def test_removes_files(self, tmp_path: Path) -> None:
        """Temp files are removed."""
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        (temp_dir / "file1.tmp").write_text("data")
        (temp_dir / "file2.jpg").write_text("data")

        cleanup_temp_dir(temp_dir)

        assert not (temp_dir / "file1.tmp").exists()
        assert not (temp_dir / "file2.jpg").exists()

    def test_nonexistent_dir_noop(self, tmp_path: Path) -> None:
        """Cleaning nonexistent dir doesn't crash."""
        cleanup_temp_dir(tmp_path / "nonexistent")

    def test_empty_dir_removed(self, tmp_path: Path) -> None:
        """Empty temp dir is removed after cleanup."""
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        (temp_dir / "file.tmp").write_text("data")

        cleanup_temp_dir(temp_dir)

        assert not temp_dir.exists()
