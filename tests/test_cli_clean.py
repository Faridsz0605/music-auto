"""Tests for CLI clean command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli.main import app
from src.core.exceptions import AuthenticationError

runner = CliRunner()


class TestCliClean:
    """Tests for the clean CLI command."""

    @patch("src.cli.commands.clean.SyncState")
    @patch("src.cli.commands.clean.load_config")
    def test_clean_no_sync_state(
        self, mock_config: MagicMock, mock_sync_cls: MagicMock
    ) -> None:
        """Clean exits 0 when no sync state exists."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_state = MagicMock()
        mock_state.total_tracks = 0
        mock_sync_cls.return_value = mock_state
        result = runner.invoke(app, ["clean"])
        assert result.exit_code == 0
        assert "sync" in result.output.lower()

    @patch("src.cli.commands.clean.YouTubeProvider")
    @patch("src.cli.commands.clean.load_auth")
    @patch("src.cli.commands.clean.SyncState")
    @patch("src.cli.commands.clean.load_config")
    def test_clean_auth_failure(
        self,
        mock_config: MagicMock,
        mock_sync_cls: MagicMock,
        mock_auth: MagicMock,
        mock_provider_cls: MagicMock,
    ) -> None:
        """Clean exits 1 when authentication fails."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_state = MagicMock()
        mock_state.total_tracks = 5
        mock_sync_cls.return_value = mock_state
        mock_auth.side_effect = AuthenticationError("No auth")
        result = runner.invoke(app, ["clean"])
        assert result.exit_code == 1

    @patch("src.cli.commands.clean.YouTubeProvider")
    @patch("src.cli.commands.clean.load_auth")
    @patch("src.cli.commands.clean.SyncState")
    @patch("src.cli.commands.clean.load_config")
    def test_clean_no_orphans(
        self,
        mock_config: MagicMock,
        mock_sync_cls: MagicMock,
        mock_auth: MagicMock,
        mock_provider_cls: MagicMock,
    ) -> None:
        """Clean exits 0 when no orphaned tracks found."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_state = MagicMock()
        mock_state.total_tracks = 5
        mock_state.synced_playlists = {}
        mock_state.get_orphaned_tracks.return_value = []
        mock_sync_cls.return_value = mock_state
        mock_auth.return_value = MagicMock()
        mock_provider = MagicMock()
        mock_provider.get_liked_songs.return_value = []
        mock_provider_cls.return_value = mock_provider
        result = runner.invoke(app, ["clean"])
        assert result.exit_code == 0
        assert "No orphaned" in result.output or "in sync" in result.output

    @patch("src.cli.commands.clean.YouTubeProvider")
    @patch("src.cli.commands.clean.load_auth")
    @patch("src.cli.commands.clean.SyncState")
    @patch("src.cli.commands.clean.load_config")
    def test_clean_dry_run(
        self,
        mock_config: MagicMock,
        mock_sync_cls: MagicMock,
        mock_auth: MagicMock,
        mock_provider_cls: MagicMock,
    ) -> None:
        """Clean with --dry-run shows orphans but doesn't delete."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_state = MagicMock()
        mock_state.total_tracks = 5
        mock_state.synced_playlists = {}
        mock_state.get_orphaned_tracks.return_value = [
            {
                "artist": "Old Artist",
                "title": "Old Song",
                "filepath": "/tmp/old.mp3",
                "video_id": "old1",
            }
        ]
        mock_sync_cls.return_value = mock_state
        mock_auth.return_value = MagicMock()
        mock_provider = MagicMock()
        mock_provider.get_liked_songs.return_value = []
        mock_provider_cls.return_value = mock_provider
        result = runner.invoke(app, ["clean", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.output or "dry run" in result.output.lower()
