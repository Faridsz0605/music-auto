"""Tests for CLI auth command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


class TestCliAuth:
    """Tests for the auth CLI command."""

    @patch("src.cli.commands.auth.setup_auth")
    def test_auth_success(self, mock_setup: MagicMock) -> None:
        """Successful auth exits with code 0."""
        mock_setup.return_value = True
        result = runner.invoke(app, ["auth"])
        assert result.exit_code == 0
        assert "complete" in result.output.lower() or "Authentication" in result.output

    @patch("src.cli.commands.auth.setup_auth")
    def test_auth_failure(self, mock_setup: MagicMock) -> None:
        """Failed auth exits with code 1."""
        mock_setup.return_value = False
        result = runner.invoke(app, ["auth"])
        assert result.exit_code == 1

    @patch("src.cli.commands.auth.setup_auth")
    def test_auth_calls_setup(self, mock_setup: MagicMock) -> None:
        """Auth command calls setup_auth."""
        mock_setup.return_value = True
        runner.invoke(app, ["auth"])
        mock_setup.assert_called_once()
