"""Tests for authentication module."""

from unittest.mock import MagicMock, patch

import pytest

from src.core.auth import load_auth, setup_auth
from src.core.exceptions import AuthenticationError


class TestSetupAuth:
    """Tests for OAuth setup flow."""

    @patch("src.core.auth.YTMusic")
    def test_setup_success(self, mock_ytmusic_cls: MagicMock) -> None:
        """Successful OAuth setup returns True."""
        mock_instance = MagicMock()
        mock_instance.get_library_playlists.return_value = [{"title": "Test"}]
        mock_ytmusic_cls.return_value = mock_instance
        mock_ytmusic_cls.setup_oauth.return_value = None

        result = setup_auth()

        assert result is True

    @patch("src.core.auth.YTMusic")
    def test_setup_failure_oauth_error(self, mock_ytmusic_cls: MagicMock) -> None:
        """Failed OAuth setup returns False."""
        mock_ytmusic_cls.setup_oauth.side_effect = Exception("OAuth failed")

        result = setup_auth()
        assert result is False

    @patch("src.core.auth.YTMusic")
    def test_setup_failure_validation_error(self, mock_ytmusic_cls: MagicMock) -> None:
        """Setup returns False when credential validation fails."""
        mock_ytmusic_cls.setup_oauth.return_value = None
        mock_instance = MagicMock()
        mock_instance.get_library_playlists.side_effect = Exception("Bad creds")
        mock_ytmusic_cls.return_value = mock_instance

        result = setup_auth()
        assert result is False


class TestLoadAuth:
    """Tests for loading saved credentials."""

    @patch("src.core.auth.OAUTH_FILE")
    def test_missing_credentials(self, mock_oauth_file: MagicMock) -> None:
        """Raises AuthenticationError when no credentials exist."""
        mock_oauth_file.exists.return_value = False

        with pytest.raises(AuthenticationError, match="Not authenticated"):
            load_auth()

    @patch("src.core.auth.YTMusic")
    @patch("src.core.auth.OAUTH_FILE")
    def test_valid_credentials(
        self, mock_oauth_file: MagicMock, mock_ytmusic_cls: MagicMock
    ) -> None:
        """Valid credentials return YTMusic instance."""
        mock_oauth_file.exists.return_value = True
        mock_oauth_file.configure_mock(
            **{"__str__": MagicMock(return_value="oauth.json")}
        )

        mock_instance = MagicMock()
        mock_instance.get_library_playlists.return_value = [{"title": "T"}]
        mock_ytmusic_cls.return_value = mock_instance

        result = load_auth()

        assert result is mock_instance

    @patch("src.core.auth.YTMusic")
    @patch("src.core.auth.OAUTH_FILE")
    def test_invalid_credentials(
        self, mock_oauth_file: MagicMock, mock_ytmusic_cls: MagicMock
    ) -> None:
        """Invalid credentials raise AuthenticationError."""
        mock_oauth_file.exists.return_value = True
        mock_oauth_file.configure_mock(
            **{"__str__": MagicMock(return_value="oauth.json")}
        )

        mock_instance = MagicMock()
        mock_instance.get_library_playlists.side_effect = Exception("Expired")
        mock_ytmusic_cls.return_value = mock_instance

        with pytest.raises(AuthenticationError, match="invalid"):
            load_auth()

    @patch("src.core.auth.YTMusic")
    @patch("src.core.auth.OAUTH_FILE")
    def test_load_auth_calls_validation(
        self, mock_oauth_file: MagicMock, mock_ytmusic_cls: MagicMock
    ) -> None:
        """load_auth validates credentials with a library request."""
        mock_oauth_file.exists.return_value = True
        mock_oauth_file.configure_mock(
            **{"__str__": MagicMock(return_value="oauth.json")}
        )

        mock_instance = MagicMock()
        mock_instance.get_library_playlists.return_value = []
        mock_ytmusic_cls.return_value = mock_instance

        load_auth()

        mock_instance.get_library_playlists.assert_called_once_with(limit=1)
