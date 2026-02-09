"""YMD - YouTube Music Downloader CLI."""

import logging

import typer

from src.cli.commands.auth import auth
from src.cli.commands.clean import clean_command
from src.cli.commands.config_cmd import config_command
from src.cli.commands.doctor import doctor_command
from src.cli.commands.search import search_command
from src.cli.commands.status import status_command
from src.cli.commands.sync import sync_command

app = typer.Typer(
    name="ymd",
    help="YMD - Sync and download YouTube Music playlists for your DAP",
    add_completion=False,
    no_args_is_help=True,
)


def _setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: If True, set DEBUG level; otherwise WARNING.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@app.callback()
def app_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose/debug logging output",
    ),
) -> None:
    """YMD - YouTube Music Downloader for DAP devices."""
    _setup_logging(verbose)


app.command(name="auth")(auth)
app.command(name="sync")(sync_command)
app.command(name="search")(search_command)
app.command(name="status")(status_command)
app.command(name="clean")(clean_command)
app.command(name="config")(config_command)
app.command(name="doctor")(doctor_command)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
