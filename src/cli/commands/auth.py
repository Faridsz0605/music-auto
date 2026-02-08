"""Authentication command."""

import typer

from src.cli.ui import console, print_error, print_header, print_success
from src.core.auth import setup_auth


def auth(ctx: typer.Context) -> None:
    """Authenticate with YouTube Music via OAuth."""
    print_header("YouTube Music Authentication")

    if setup_auth():
        print_success("Authentication complete!")
        console.print("You can now use [bold]ymd sync[/bold] to download music.")
        raise typer.Exit(code=0)
    else:
        print_error("Authentication failed. See tips above.")
        raise typer.Exit(code=1)
