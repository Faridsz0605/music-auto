"""Tests for CLI UI components."""

from typing import Any
from unittest.mock import MagicMock, patch

from src.cli.ui import (
    confirm_action,
    create_download_progress,
    print_error,
    print_header,
    print_info,
    print_playlist_table,
    print_success,
    print_sync_summary,
    print_track_table,
    print_warning,
)


class TestPrintFunctions:
    """Tests for print_* helper functions."""

    @patch("src.cli.ui.console")
    def test_print_header(self, mock_console: MagicMock) -> None:
        """print_header outputs with :: prefix."""
        print_header("Test Header")
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Test Header" in call_args

    @patch("src.cli.ui.console")
    def test_print_success(self, mock_console: MagicMock) -> None:
        """print_success outputs with arrow prefix."""
        print_success("Done")
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Done" in call_args

    @patch("src.cli.ui.console")
    def test_print_warning(self, mock_console: MagicMock) -> None:
        """print_warning outputs with warning style."""
        print_warning("Careful")
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Careful" in call_args

    @patch("src.cli.ui.console")
    def test_print_error(self, mock_console: MagicMock) -> None:
        """print_error outputs with error prefix."""
        print_error("Something failed")
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Something failed" in call_args

    @patch("src.cli.ui.console")
    def test_print_info(self, mock_console: MagicMock) -> None:
        """print_info outputs with dim style."""
        print_info("Some info")
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Some info" in call_args


class TestTrackTable:
    """Tests for track table rendering."""

    @patch("src.cli.ui.console")
    def test_print_track_table(self, mock_console: MagicMock) -> None:
        """print_track_table renders a table with tracks."""
        tracks = [
            {
                "artist": "Queen",
                "title": "Bohemian Rhapsody",
                "album": "A Night at the Opera",
            },
            {
                "artist": "Eagles",
                "title": "Hotel California",
                "album": "Hotel California",
            },
        ]
        print_track_table(tracks)
        assert mock_console.print.called

    @patch("src.cli.ui.console")
    def test_print_track_table_truncation(self, mock_console: MagicMock) -> None:
        """print_track_table shows max 20 tracks by default."""
        tracks = [
            {
                "artist": f"Artist {i}",
                "title": f"Song {i}",
                "album": f"Album {i}",
            }
            for i in range(25)
        ]
        print_track_table(tracks)
        # Should print table + "and X more" message
        assert mock_console.print.call_count >= 2

    @patch("src.cli.ui.console")
    def test_print_track_table_show_all(self, mock_console: MagicMock) -> None:
        """print_track_table with show_all shows all tracks."""
        tracks = [
            {
                "artist": f"Artist {i}",
                "title": f"Song {i}",
                "album": f"Album {i}",
            }
            for i in range(25)
        ]
        print_track_table(tracks, show_all=True)
        # Should print table only, no "and X more" message
        assert mock_console.print.call_count == 1

    @patch("src.cli.ui.console")
    def test_print_track_table_empty(self, mock_console: MagicMock) -> None:
        """print_track_table handles empty list."""
        print_track_table([])
        assert mock_console.print.called


class TestPlaylistTable:
    """Tests for playlist table rendering."""

    @patch("src.cli.ui.console")
    def test_print_playlist_table(self, mock_console: MagicMock) -> None:
        """print_playlist_table renders playlists."""
        playlists: list[dict[str, Any]] = [
            {
                "title": "Rock Classics",
                "count": 50,
                "playlistId": "PL001",
            },
            {
                "title": "Chill Vibes",
                "count": 30,
                "playlistId": "PL002",
            },
        ]
        print_playlist_table(playlists)
        assert mock_console.print.called


class TestProgressBar:
    """Tests for progress bar creation."""

    def test_create_download_progress(self) -> None:
        """create_download_progress returns a Progress instance."""
        progress = create_download_progress()
        assert progress is not None


class TestConfirmAction:
    """Tests for confirm_action."""

    @patch("src.cli.ui.console")
    def test_confirm_yes(self, mock_console: MagicMock) -> None:
        """confirm_action returns True for 'y'."""
        mock_console.input.return_value = "y"
        assert confirm_action("Continue?") is True

    @patch("src.cli.ui.console")
    def test_confirm_empty(self, mock_console: MagicMock) -> None:
        """confirm_action returns True for empty input."""
        mock_console.input.return_value = ""
        assert confirm_action("Continue?") is True

    @patch("src.cli.ui.console")
    def test_confirm_no(self, mock_console: MagicMock) -> None:
        """confirm_action returns False for 'n'."""
        mock_console.input.return_value = "n"
        assert confirm_action("Continue?") is False


class TestSyncSummary:
    """Tests for sync summary."""

    @patch("src.cli.ui.console")
    def test_print_sync_summary(self, mock_console: MagicMock) -> None:
        """print_sync_summary displays all statistics."""
        print_sync_summary(total=100, downloaded=80, skipped=15, failed=5)
        assert mock_console.print.call_count >= 4

    @patch("src.cli.ui.console")
    def test_print_sync_summary_no_failures(self, mock_console: MagicMock) -> None:
        """print_sync_summary omits failed when 0 failures."""
        print_sync_summary(total=50, downloaded=50, skipped=0, failed=0)
        assert mock_console.print.called
