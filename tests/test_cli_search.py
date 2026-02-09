"""Tests for CLI search command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli.main import app
from src.core.exceptions import AuthenticationError

runner = CliRunner()


class TestCliSearch:
    """Tests for the search CLI command."""

    @patch("src.cli.commands.search.load_auth")
    @patch("src.cli.commands.search.load_config")
    def test_search_auth_failure(
        self, mock_config: MagicMock, mock_auth: MagicMock
    ) -> None:
        """Search exits 1 when authentication fails."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_auth.side_effect = AuthenticationError("Not authenticated")
        result = runner.invoke(app, ["search", "test query"])
        assert result.exit_code == 1

    @patch("src.cli.commands.search.YouTubeProvider")
    @patch("src.cli.commands.search.load_auth")
    @patch("src.cli.commands.search.load_config")
    def test_search_no_results(
        self,
        mock_config: MagicMock,
        mock_auth: MagicMock,
        mock_provider_cls: MagicMock,
    ) -> None:
        """Search exits 0 when no results found."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_auth.return_value = MagicMock()
        mock_provider = MagicMock()
        mock_provider.search.return_value = []
        mock_provider_cls.return_value = mock_provider
        result = runner.invoke(app, ["search", "nonexistent song"])
        assert result.exit_code == 0
        assert "No results" in result.output

    @patch("src.cli.commands.search.questionary")
    @patch("src.cli.commands.search.YouTubeProvider")
    @patch("src.cli.commands.search.load_auth")
    @patch("src.cli.commands.search.load_config")
    def test_search_no_selection(
        self,
        mock_config: MagicMock,
        mock_auth: MagicMock,
        mock_provider_cls: MagicMock,
        mock_questionary: MagicMock,
    ) -> None:
        """Search exits 0 when user selects nothing."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_auth.return_value = MagicMock()
        mock_provider = MagicMock()
        mock_provider.search.return_value = [
            {
                "title": "Test Song",
                "artists": [{"name": "Artist"}],
                "album": {"name": "Album"},
                "videoId": "abc123",
                "duration": "3:00",
            }
        ]
        mock_provider_cls.return_value = mock_provider
        mock_questionary.checkbox.return_value.ask.return_value = None
        result = runner.invoke(app, ["search", "test"])
        assert result.exit_code == 0

    def test_search_requires_query(self) -> None:
        """Search command requires a query argument."""
        result = runner.invoke(app, ["search"])
        assert result.exit_code != 0

    @patch("src.cli.commands.search.load_auth")
    @patch("src.cli.commands.search.load_config")
    def test_search_with_limit(
        self, mock_config: MagicMock, mock_auth: MagicMock
    ) -> None:
        """Search accepts --limit option."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_auth.return_value = MagicMock()
        with patch("src.cli.commands.search.YouTubeProvider") as mock_prov_cls:
            mock_prov = MagicMock()
            mock_prov.search.return_value = []
            mock_prov_cls.return_value = mock_prov
            result = runner.invoke(app, ["search", "test", "--limit", "5"])
            assert result.exit_code == 0
            mock_prov.search.assert_called_once_with("test", limit=5)
