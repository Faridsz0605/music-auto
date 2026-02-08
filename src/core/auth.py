"""YouTube Music OAuth authentication module."""

from pathlib import Path

from rich.console import Console
from ytmusicapi import YTMusic

from src.core.exceptions import AuthenticationError

console = Console()

OAUTH_FILE = Path("oauth.json")


def setup_auth() -> bool:
    """
    Interactive OAuth authentication setup for YouTube Music.

    Uses ytmusicapi's built-in OAuth flow which opens a browser
    for Google account authorization.

    Returns:
        True if authentication was successful.
    """
    console.print("\n[bold cyan]:: YouTube Music OAuth Setup[/bold cyan]\n")
    console.print("This will open your browser for Google account authorization.")
    console.print("Follow the prompts to grant access to your YouTube Music library.\n")

    try:
        YTMusic.setup_oauth(filepath=str(OAUTH_FILE), open_browser=True)  # type: ignore[attr-defined]

        # Validate the new credentials
        ytmusic = YTMusic(str(OAUTH_FILE))
        ytmusic.get_library_playlists(limit=1)

        console.print("[green]Authentication successful![/green]")
        console.print(f"[dim]Credentials saved to {OAUTH_FILE}[/dim]")
        return True

    except Exception as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        console.print("\n[yellow]Tips:[/yellow]")
        console.print("  - Make sure you're logged into your Google account")
        console.print("  - Allow the permissions when prompted in the browser")
        console.print("  - Check your internet connection")
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
        raise AuthenticationError("Not authenticated. Run 'ymd auth' first.")

    try:
        ytmusic = YTMusic(str(OAUTH_FILE))
        # Validate with a simple request
        ytmusic.get_library_playlists(limit=1)
        return ytmusic
    except Exception as e:
        raise AuthenticationError(
            f"Stored credentials are invalid: {e}. "
            "Run 'ymd auth' to re-authenticate."
        ) from e
