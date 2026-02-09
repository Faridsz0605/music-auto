"""Tests for CLI doctor command."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


class TestCliDoctor:
    """Tests for the doctor CLI command."""

    @patch("src.cli.commands.doctor._check_api_connection")
    @patch("src.cli.commands.doctor._check_download_dir")
    @patch("src.cli.commands.doctor._check_ffmpeg")
    @patch("src.cli.commands.doctor._check_yt_dlp")
    @patch("src.cli.commands.doctor._check_oauth_tokens")
    @patch("src.cli.commands.doctor._check_oauth_credentials")
    @patch("src.cli.commands.doctor._check_config")
    def test_all_checks_pass(
        self,
        mock_config: MagicMock,
        mock_creds: MagicMock,
        mock_tokens: MagicMock,
        mock_ytdlp: MagicMock,
        mock_ffmpeg: MagicMock,
        mock_dldir: MagicMock,
        mock_api: MagicMock,
    ) -> None:
        """All checks passing exits with code 0."""
        mock_config.return_value = True
        mock_creds.return_value = True
        mock_tokens.return_value = True
        mock_ytdlp.return_value = True
        mock_ffmpeg.return_value = True
        mock_dldir.return_value = True
        mock_api.return_value = True

        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "passed" in result.output.lower()

    @patch("src.cli.commands.doctor._check_api_connection")
    @patch("src.cli.commands.doctor._check_download_dir")
    @patch("src.cli.commands.doctor._check_ffmpeg")
    @patch("src.cli.commands.doctor._check_yt_dlp")
    @patch("src.cli.commands.doctor._check_oauth_tokens")
    @patch("src.cli.commands.doctor._check_oauth_credentials")
    @patch("src.cli.commands.doctor._check_config")
    def test_some_checks_fail(
        self,
        mock_config: MagicMock,
        mock_creds: MagicMock,
        mock_tokens: MagicMock,
        mock_ytdlp: MagicMock,
        mock_ffmpeg: MagicMock,
        mock_dldir: MagicMock,
        mock_api: MagicMock,
    ) -> None:
        """Some failing checks exits with code 1."""
        mock_config.return_value = True
        mock_creds.return_value = False
        mock_tokens.return_value = False
        mock_ytdlp.return_value = True
        mock_ffmpeg.return_value = True
        mock_dldir.return_value = True
        mock_api.return_value = True

        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 1
        assert "failed" in result.output.lower()

    @patch("src.cli.commands.doctor._check_download_dir")
    @patch("src.cli.commands.doctor._check_ffmpeg")
    @patch("src.cli.commands.doctor._check_yt_dlp")
    @patch("src.cli.commands.doctor._check_oauth_tokens")
    @patch("src.cli.commands.doctor._check_oauth_credentials")
    @patch("src.cli.commands.doctor._check_config")
    def test_skip_api_flag(
        self,
        mock_config: MagicMock,
        mock_creds: MagicMock,
        mock_tokens: MagicMock,
        mock_ytdlp: MagicMock,
        mock_ffmpeg: MagicMock,
        mock_dldir: MagicMock,
    ) -> None:
        """--skip-api skips the API connection check."""
        mock_config.return_value = True
        mock_creds.return_value = True
        mock_tokens.return_value = True
        mock_ytdlp.return_value = True
        mock_ffmpeg.return_value = True
        mock_dldir.return_value = True

        result = runner.invoke(app, ["doctor", "--skip-api"])
        assert result.exit_code == 0
        assert "skip" in result.output.lower()


class TestDoctorChecks:
    """Tests for individual doctor check functions."""

    @patch("src.cli.commands.doctor.CONFIG_FILE")
    def test_check_config_missing(self, mock_path: MagicMock) -> None:
        """_check_config returns False when config.json missing."""
        mock_path.exists.return_value = False
        from src.cli.commands.doctor import _check_config

        assert _check_config() is False

    @patch("src.cli.commands.doctor.load_config")
    @patch("src.cli.commands.doctor.CONFIG_FILE")
    def test_check_config_valid(
        self, mock_path: MagicMock, mock_load: MagicMock
    ) -> None:
        """_check_config returns True when config is valid."""
        mock_path.exists.return_value = True
        mock_load.return_value = MagicMock()
        from src.cli.commands.doctor import _check_config

        assert _check_config() is True

    @patch("src.cli.commands.doctor.load_config")
    def test_check_oauth_credentials_missing(
        self, mock_load: MagicMock
    ) -> None:
        """_check_oauth_credentials returns False when creds empty."""
        mock_load.return_value = MagicMock(client_id="", client_secret="")
        from src.cli.commands.doctor import _check_oauth_credentials

        assert _check_oauth_credentials() is False

    @patch("src.cli.commands.doctor.load_config")
    def test_check_oauth_credentials_present(
        self, mock_load: MagicMock
    ) -> None:
        """_check_oauth_credentials returns True when creds present."""
        mock_load.return_value = MagicMock(
            client_id="test_id", client_secret="test_secret"
        )
        from src.cli.commands.doctor import _check_oauth_credentials

        assert _check_oauth_credentials() is True

    def test_check_oauth_tokens_missing(self, tmp_path: Path) -> None:
        """_check_oauth_tokens returns False when file missing."""
        with patch("src.cli.commands.doctor.Path") as mock_path_cls:
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_path_cls.return_value = mock_file
            from src.cli.commands.doctor import _check_oauth_tokens

            assert _check_oauth_tokens() is False

    def test_check_ffmpeg_found(self) -> None:
        """_check_ffmpeg returns True when ffmpeg in PATH."""
        with patch("src.cli.commands.doctor.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            from src.cli.commands.doctor import _check_ffmpeg

            assert _check_ffmpeg() is True

    def test_check_ffmpeg_not_found(self) -> None:
        """_check_ffmpeg returns False when ffmpeg not in PATH."""
        with patch("src.cli.commands.doctor.shutil.which") as mock_which:
            mock_which.return_value = None
            from src.cli.commands.doctor import _check_ffmpeg

            assert _check_ffmpeg() is False
