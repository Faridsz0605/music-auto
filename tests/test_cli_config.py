"""Tests for CLI config command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


class TestCliConfig:
    """Tests for the config CLI command."""

    @patch("src.cli.commands.config_cmd.save_config")
    def test_config_init(self, mock_save: MagicMock) -> None:
        """Config --init creates default config."""
        result = runner.invoke(app, ["config", "--init"])
        assert result.exit_code == 0
        mock_save.assert_called_once()
        assert "Created" in result.output or "config" in result.output.lower()

    @patch("src.cli.commands.config_cmd.load_config")
    def test_config_show(self, mock_load: MagicMock) -> None:
        """Config --show displays current configuration."""
        mock_load.return_value = MagicMock(
            model_dump=MagicMock(
                return_value={
                    "download_dir": "downloads",
                    "audio_format": "best",
                    "fallback_format": "mp3",
                    "organize_by": "genre_artist",
                    "max_filename_length": 120,
                    "max_concurrent_downloads": 3,
                    "default_genre": "Unknown",
                    "client_id": "",
                    "client_secret": "",
                }
            )
        )
        result = runner.invoke(app, ["config", "--show"])
        assert result.exit_code == 0
        assert "download_dir" in result.output

    @patch("src.cli.commands.config_cmd.save_config")
    @patch("src.cli.commands.config_cmd.load_config")
    def test_config_set_value(self, mock_load: MagicMock, mock_save: MagicMock) -> None:
        """Config --set updates a config value."""
        mock_load.return_value = MagicMock(
            model_dump=MagicMock(
                return_value={
                    "download_dir": "downloads",
                    "audio_format": "best",
                    "fallback_format": "mp3",
                    "organize_by": "genre_artist",
                    "max_filename_length": 120,
                    "max_concurrent_downloads": 3,
                    "default_genre": "Unknown",
                    "client_id": "",
                    "client_secret": "",
                }
            )
        )
        result = runner.invoke(app, ["config", "--set", "audio_format=mp3"])
        assert result.exit_code == 0
        mock_save.assert_called_once()

    @patch("src.cli.commands.config_cmd.load_config")
    def test_config_set_invalid_format(self, mock_load: MagicMock) -> None:
        """Config --set with invalid format exits 1."""
        mock_load.return_value = MagicMock(
            model_dump=MagicMock(return_value={"download_dir": "downloads"})
        )
        result = runner.invoke(app, ["config", "--set", "invalid_no_equals"])
        assert result.exit_code == 1

    @patch("src.cli.commands.config_cmd.load_config")
    def test_config_set_unknown_key(self, mock_load: MagicMock) -> None:
        """Config --set with unknown key exits 1."""
        mock_load.return_value = MagicMock(
            model_dump=MagicMock(return_value={"download_dir": "downloads"})
        )
        result = runner.invoke(app, ["config", "--set", "nonexistent_key=value"])
        assert result.exit_code == 1
        assert "Unknown" in result.output
