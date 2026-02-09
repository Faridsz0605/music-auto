"""YouTube Music OAuth authentication module."""

from pathlib import Path

from rich.console import Console
from ytmusicapi import OAuthCredentials, YTMusic, setup_oauth as ytmusicapi_setup_oauth

from src.core.config import load_config
from src.core.exceptions import AuthenticationError

console = Console()

OAUTH_FILE = Path("oauth.json")


def _validate_credentials() -> tuple[str, str]:
    """Validate and return OAuth client_id and client_secret from config.

    Returns:
        Tuple of (client_id, client_secret).

    Raises:
        AuthenticationError: If client_id or client_secret are not configured.
    """
    config = load_config()
    if not config.client_id or not config.client_secret:
        raise AuthenticationError(
            "OAuth client_id and client_secret are required.\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. Enable the YouTube Data API v3\n"
            "3. Create OAuth credentials (type: 'TVs and Limited Input devices')\n"
            "4. Run 'ymd config --set client_id=YOUR_ID "
            "client_secret=YOUR_SECRET'\n"
            "   Or set YMD_CLIENT_ID and YMD_CLIENT_SECRET env vars"
        )
    return config.client_id, config.client_secret


def _get_oauth_credentials() -> OAuthCredentials:
    """Load OAuth credentials from config as OAuthCredentials object.

    Used for YTMusic() constructor which accepts OAuthCredentials.

    Returns:
        OAuthCredentials instance with client_id and client_secret.

    Raises:
        AuthenticationError: If client_id or client_secret are not configured.
    """
    client_id, client_secret = _validate_credentials()
    return OAuthCredentials(
        client_id=client_id,
        client_secret=client_secret,
    )


def setup_auth() -> bool:
    """
    Interactive OAuth authentication setup for YouTube Music.

    Uses ytmusicapi's OAuth flow with custom client credentials.
    Opens a browser for Google account authorization.

    Returns:
        True if authentication was successful.
    """
    console.print("\n[bold cyan]:: YouTube Music OAuth Setup[/bold cyan]\n")

    try:
        client_id, client_secret = _validate_credentials()
    except AuthenticationError as e:
        console.print(f"[red]{e}[/red]")
        return False

    console.print(
        "This will start a device-code authentication flow."
    )
    console.print(
        "Follow the prompts to grant access to your "
        "YouTube Music library.\n"
    )

    try:
        # setup_oauth takes client_id and client_secret as direct strings
        # (it constructs OAuthCredentials internally)
        ytmusicapi_setup_oauth(
            client_id=client_id,
            client_secret=client_secret,
            filepath=str(OAUTH_FILE),
            open_browser=True,
        )

        # Validate the new credentials
        # YTMusic() accepts OAuthCredentials object
        oauth_credentials = OAuthCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
        ytmusic = YTMusic(
            str(OAUTH_FILE),
            oauth_credentials=oauth_credentials,
        )
        ytmusic.get_library_playlists(limit=1)

        console.print("[green]Authentication successful![/green]")
        console.print(f"[dim]Credentials saved to {OAUTH_FILE}[/dim]")
        return True

    except Exception as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        console.print("\n[yellow]Tips:[/yellow]")
        console.print(
            "  - Ensure client_id and client_secret are correct"
        )
        console.print(
            "  - The OAuth app type must be "
            "'TVs and Limited Input devices'"
        )
        console.print(
            "  - YouTube Data API v3 must be enabled "
            "in your Google Cloud project"
        )
        console.print(
            "  - Make sure you're logged into your Google account"
        )
        return False


def load_auth() -> YTMusic:
    """
    Load saved OAuth credentials and create YTMusic client.

    Returns:
        Authenticated YTMusic instance.

    Raises:
        AuthenticationError: If credentials don't exist or are invalid.
    """
    if not OAUTH_FILE.exists():
        raise AuthenticationError(
            "Not authenticated. Run 'ymd auth' first."
        )

    oauth_credentials = _get_oauth_credentials()

    try:
        ytmusic = YTMusic(
            str(OAUTH_FILE),
            oauth_credentials=oauth_credentials,
        )
        # Validate with a simple request
        ytmusic.get_library_playlists(limit=1)
        return ytmusic
    except Exception as e:
        raise AuthenticationError(
            f"Stored credentials are invalid: {e}. "
            "Run 'ymd auth' to re-authenticate."
        ) from e
