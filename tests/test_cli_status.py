"""Tests for CLI status command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


class TestCliStatus:
    """Tests for the status CLI command."""

    @patch("src.cli.commands.status.SyncState")
    @patch("src.cli.commands.status.load_config")
    def test_status_never_synced(
        self, mock_config: MagicMock, mock_sync_cls: MagicMock
    ) -> None:
        """Status shows warning when never synced."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_state = MagicMock()
        mock_state.last_sync = None
        mock_sync_cls.return_value = mock_state
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Never synced" in result.output

    @patch("src.cli.commands.status.SyncState")
    @patch("src.cli.commands.status.load_config")
    def test_status_with_sync_data(
        self, mock_config: MagicMock, mock_sync_cls: MagicMock
    ) -> None:
        """Status displays sync info when state exists."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_state = MagicMock()
        mock_state.last_sync = "2026-02-07T10:00:00"
        mock_state.total_tracks = 50
        mock_state.synced_playlists = {
            "PL001": {
                "name": "Rock Classics",
                "track_count": 50,
                "last_sync": "2026-02-07T10:00:00",
            }
        }
        mock_sync_cls.return_value = mock_state
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "50" in result.output

    @patch("src.cli.commands.status.SyncState")
    @patch("src.cli.commands.status.load_config")
    def test_status_with_output_dir(
        self, mock_config: MagicMock, mock_sync_cls: MagicMock
    ) -> None:
        """Status accepts --output-dir option."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_state = MagicMock()
        mock_state.last_sync = None
        mock_sync_cls.return_value = mock_state
        result = runner.invoke(app, ["status", "--output-dir", "/tmp/music"])
        assert result.exit_code == 0
