"""Tests for CLI sync command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli.main import app
from src.core.exceptions import AuthenticationError

runner = CliRunner()


class TestCliSync:
    """Tests for the sync CLI command."""

    @patch("src.cli.commands.sync.load_auth")
    @patch("src.cli.commands.sync.load_config")
    def test_sync_auth_failure(
        self, mock_config: MagicMock, mock_auth: MagicMock
    ) -> None:
        """Sync exits 1 when authentication fails."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_auth.side_effect = AuthenticationError("Not authenticated")
        result = runner.invoke(app, ["sync", "--liked"])
        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    @patch("src.cli.commands.sync.SyncState")
    @patch("src.cli.commands.sync.YouTubeProvider")
    @patch("src.cli.commands.sync.load_auth")
    @patch("src.cli.commands.sync.load_config")
    def test_sync_liked_no_tracks(
        self,
        mock_config: MagicMock,
        mock_auth: MagicMock,
        mock_provider_cls: MagicMock,
        mock_sync_state: MagicMock,
    ) -> None:
        """Sync exits 0 when liked songs returns no tracks."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_auth.return_value = MagicMock()
        mock_provider = MagicMock()
        mock_provider.get_liked_songs.return_value = []
        mock_provider_cls.return_value = mock_provider
        result = runner.invoke(app, ["sync", "--liked"])
        assert result.exit_code == 0

    @patch("src.cli.commands.sync.cleanup_temp_dir")
    @patch("src.cli.commands.sync.download_track")
    @patch("src.cli.commands.sync.tag_file")
    @patch("src.cli.commands.sync.organize_track")
    @patch("src.cli.commands.sync.SyncState")
    @patch("src.cli.commands.sync.YouTubeProvider")
    @patch("src.cli.commands.sync.load_auth")
    @patch("src.cli.commands.sync.load_config")
    def test_sync_liked_with_tracks(
        self,
        mock_config: MagicMock,
        mock_auth: MagicMock,
        mock_provider_cls: MagicMock,
        mock_sync_state_cls: MagicMock,
        mock_organize: MagicMock,
        mock_tag: MagicMock,
        mock_download: MagicMock,
        mock_cleanup: MagicMock,
    ) -> None:
        """Sync downloads new tracks from liked songs."""
        mock_config.return_value = MagicMock(
            download_dir=Path("downloads"),
            audio_format="best",
            fallback_format="mp3",
            organize_by="genre_artist",
            max_filename_length=120,
            default_genre="Unknown",
        )
        mock_auth.return_value = MagicMock()

        mock_provider = MagicMock()
        mock_provider.get_liked_songs.return_value = [
            {
                "title": "Test Song",
                "artists": [{"name": "Artist"}],
                "album": {"name": "Album"},
                "videoId": "abc123",
                "duration": "3:00",
            }
        ]
        mock_provider_cls.return_value = mock_provider

        mock_state = MagicMock()
        mock_state.get_new_tracks.return_value = [
            {
                "title": "Test Song",
                "artist": "Artist",
                "album": "Album",
                "video_id": "abc123",
                "duration": "3:00",
                "genre": "",
            }
        ]
        mock_sync_state_cls.return_value = mock_state

        mock_download.return_value = Path("downloads/.tmp/abc123.mp3")
        mock_organize.return_value = Path(
            "downloads/Unknown/Artist/Artist - Test Song.mp3"
        )

        result = runner.invoke(app, ["sync", "--liked"])
        assert result.exit_code == 0
        mock_download.assert_called_once()

    @patch("src.cli.commands.sync.SyncState")
    @patch("src.cli.commands.sync.YouTubeProvider")
    @patch("src.cli.commands.sync.load_auth")
    @patch("src.cli.commands.sync.load_config")
    def test_sync_all_up_to_date(
        self,
        mock_config: MagicMock,
        mock_auth: MagicMock,
        mock_provider_cls: MagicMock,
        mock_sync_state_cls: MagicMock,
    ) -> None:
        """Sync exits 0 when all tracks already downloaded."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        mock_auth.return_value = MagicMock()

        mock_provider = MagicMock()
        mock_provider.get_liked_songs.return_value = [
            {
                "title": "Test",
                "artists": [{"name": "A"}],
                "album": {"name": "B"},
                "videoId": "xyz",
                "duration": "1:00",
            }
        ]
        mock_provider_cls.return_value = mock_provider

        mock_state = MagicMock()
        mock_state.get_new_tracks.return_value = []
        mock_sync_state_cls.return_value = mock_state

        result = runner.invoke(app, ["sync", "--liked"])
        assert result.exit_code == 0
        assert "up to date" in result.output.lower()

    @patch("src.cli.commands.sync.load_config")
    def test_sync_with_output_dir(self, mock_config: MagicMock) -> None:
        """Sync accepts --output-dir option."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        # Will fail at auth, but we verify the option is accepted
        with patch(
            "src.cli.commands.sync.load_auth",
            side_effect=AuthenticationError("No auth"),
        ):
            result = runner.invoke(
                app, ["sync", "--liked", "--output-dir", "/tmp/test"]
            )
            assert result.exit_code == 1
