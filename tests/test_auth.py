"""Tests for authentication module."""

from unittest.mock import MagicMock, patch

import pytest

from src.core.auth import (
    _get_oauth_credentials,
    _validate_credentials,
    load_auth,
    setup_auth,
)
from src.core.exceptions import AuthenticationError


class TestValidateCredentials:
    """Tests for _validate_credentials helper."""

    @patch("src.core.auth.load_config")
    def test_valid_credentials(self, mock_config: MagicMock) -> None:
        """Returns tuple of (client_id, client_secret) from config."""
        mock_config.return_value = MagicMock(
            client_id="test_id", client_secret="test_secret"
        )
        client_id, client_secret = _validate_credentials()
        assert client_id == "test_id"
        assert client_secret == "test_secret"

    @patch("src.core.auth.load_config")
    def test_missing_client_id(self, mock_config: MagicMock) -> None:
        """Raises AuthenticationError when client_id is empty."""
        mock_config.return_value = MagicMock(
            client_id="", client_secret="test_secret"
        )
        with pytest.raises(AuthenticationError, match="client_id"):
            _validate_credentials()

    @patch("src.core.auth.load_config")
    def test_missing_client_secret(self, mock_config: MagicMock) -> None:
        """Raises AuthenticationError when client_secret is empty."""
        mock_config.return_value = MagicMock(
            client_id="test_id", client_secret=""
        )
        with pytest.raises(AuthenticationError, match="client_id"):
            _validate_credentials()


class TestGetOAuthCredentials:
    """Tests for _get_oauth_credentials helper."""

    @patch("src.core.auth.load_config")
    def test_valid_credentials(self, mock_config: MagicMock) -> None:
        """Returns OAuthCredentials when config has client_id and secret."""
        mock_config.return_value = MagicMock(
            client_id="test_id", client_secret="test_secret"
        )
        creds = _get_oauth_credentials()
        assert creds.client_id == "test_id"
        assert creds.client_secret == "test_secret"

    @patch("src.core.auth.load_config")
    def test_missing_client_id(self, mock_config: MagicMock) -> None:
        """Raises AuthenticationError when client_id is empty."""
        mock_config.return_value = MagicMock(
            client_id="", client_secret="test_secret"
        )
        with pytest.raises(AuthenticationError, match="client_id"):
            _get_oauth_credentials()


class TestSetupAuth:
    """Tests for OAuth setup flow."""

    @patch("src.core.auth.YTMusic")
    @patch("src.core.auth.ytmusicapi_setup_oauth")
    @patch("src.core.auth._validate_credentials")
    def test_setup_success(
        self,
        mock_validate: MagicMock,
        mock_setup_oauth: MagicMock,
        mock_ytmusic_cls: MagicMock,
    ) -> None:
        """Successful OAuth setup returns True."""
        mock_validate.return_value = ("test_id", "test_secret")

        mock_instance = MagicMock()
        mock_instance.get_library_playlists.return_value = [{"title": "Test"}]
        mock_ytmusic_cls.return_value = mock_instance
        mock_setup_oauth.return_value = None

        result = setup_auth()

        assert result is True
        mock_setup_oauth.assert_called_once_with(
            client_id="test_id",
            client_secret="test_secret",
            filepath="oauth.json",
            open_browser=True,
        )

    @patch("src.core.auth._validate_credentials")
    def test_setup_failure_missing_credentials(
        self,
        mock_validate: MagicMock,
    ) -> None:
        """Setup returns False when OAuth credentials are missing."""
        mock_validate.side_effect = AuthenticationError("Missing creds")

        result = setup_auth()
        assert result is False

    @patch("src.core.auth.ytmusicapi_setup_oauth")
    @patch("src.core.auth._validate_credentials")
    def test_setup_failure_oauth_error(
        self,
        mock_validate: MagicMock,
        mock_setup_oauth: MagicMock,
    ) -> None:
        """Failed OAuth setup returns False."""
        mock_validate.return_value = ("test_id", "test_secret")
        mock_setup_oauth.side_effect = Exception("OAuth failed")

        result = setup_auth()
        assert result is False

    @patch("src.core.auth.YTMusic")
    @patch("src.core.auth.ytmusicapi_setup_oauth")
    @patch("src.core.auth._validate_credentials")
    def test_setup_failure_validation_error(
        self,
        mock_validate: MagicMock,
        mock_setup_oauth: MagicMock,
        mock_ytmusic_cls: MagicMock,
    ) -> None:
        """Setup returns False when credential validation fails."""
        mock_validate.return_value = ("test_id", "test_secret")
        mock_setup_oauth.return_value = None
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
    @patch("src.core.auth._get_oauth_credentials")
    @patch("src.core.auth.OAUTH_FILE")
    def test_valid_credentials(
        self,
        mock_oauth_file: MagicMock,
        mock_get_creds: MagicMock,
        mock_ytmusic_cls: MagicMock,
    ) -> None:
        """Valid credentials return YTMusic instance."""
        mock_oauth_file.exists.return_value = True
        mock_oauth_file.configure_mock(
            **{"__str__": MagicMock(return_value="oauth.json")}
        )
        mock_get_creds.return_value = MagicMock()

        mock_instance = MagicMock()
        mock_instance.get_library_playlists.return_value = [{"title": "T"}]
        mock_ytmusic_cls.return_value = mock_instance

        result = load_auth()

        assert result is mock_instance

    @patch("src.core.auth.YTMusic")
    @patch("src.core.auth._get_oauth_credentials")
    @patch("src.core.auth.OAUTH_FILE")
    def test_invalid_credentials(
        self,
        mock_oauth_file: MagicMock,
        mock_get_creds: MagicMock,
        mock_ytmusic_cls: MagicMock,
    ) -> None:
        """Invalid credentials raise AuthenticationError."""
        mock_oauth_file.exists.return_value = True
        mock_oauth_file.configure_mock(
            **{"__str__": MagicMock(return_value="oauth.json")}
        )
        mock_get_creds.return_value = MagicMock()

        mock_instance = MagicMock()
        mock_instance.get_library_playlists.side_effect = Exception("Expired")
        mock_ytmusic_cls.return_value = mock_instance

        with pytest.raises(AuthenticationError, match="invalid"):
            load_auth()

    @patch("src.core.auth.YTMusic")
    @patch("src.core.auth._get_oauth_credentials")
    @patch("src.core.auth.OAUTH_FILE")
    def test_load_auth_calls_validation(
        self,
        mock_oauth_file: MagicMock,
        mock_get_creds: MagicMock,
        mock_ytmusic_cls: MagicMock,
    ) -> None:
        """load_auth validates credentials with a library request."""
        mock_oauth_file.exists.return_value = True
        mock_oauth_file.configure_mock(
            **{"__str__": MagicMock(return_value="oauth.json")}
        )
        mock_get_creds.return_value = MagicMock()

        mock_instance = MagicMock()
        mock_instance.get_library_playlists.return_value = []
        mock_ytmusic_cls.return_value = mock_instance

        load_auth()

        mock_instance.get_library_playlists.assert_called_once_with(limit=1)

    @patch("src.core.auth._get_oauth_credentials")
    @patch("src.core.auth.OAUTH_FILE")
    def test_load_auth_missing_oauth_credentials(
        self,
        mock_oauth_file: MagicMock,
        mock_get_creds: MagicMock,
    ) -> None:
        """load_auth raises when config lacks client_id/secret."""
        mock_oauth_file.exists.return_value = True
        mock_get_creds.side_effect = AuthenticationError("Missing creds")

        with pytest.raises(AuthenticationError, match="Missing creds"):
            load_auth()
