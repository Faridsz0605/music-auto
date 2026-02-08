"""CLI UI components - Rich-based, pacman-inspired interface."""

from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.theme import Theme

# Pacman-inspired theme
ymd_theme = Theme(
    {
        "info": "bold cyan",
        "warning": "bold yellow",
        "error": "bold red",
        "success": "bold green",
        "header": "bold white",
        "dim": "dim",
        "track.artist": "cyan",
        "track.title": "white",
        "track.album": "yellow",
    }
)

console = Console(theme=ymd_theme)


def print_header(message: str) -> None:
    """Print a pacman-style section header."""
    console.print(f"\n[info]:: {message}[/info]")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[success] -> {message}[/success]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[warning] -> {message}[/warning]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[error]error: {message}[/error]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[dim] -> {message}[/dim]")


def print_track_table(
    tracks: list[dict[str, str]],
    title: str = "Tracks",
    show_all: bool = False,
) -> None:
    """Display tracks in a formatted table.

    Args:
        tracks: List of normalized track dicts.
        title: Table title.
        show_all: Show all tracks or limit to 20.
    """
    display_tracks = tracks if show_all else tracks[:20]
    total = len(tracks)

    table = Table(
        title=f"{title} ({total} tracks)",
        show_lines=False,
        border_style="dim",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Artist", style="track.artist")
    table.add_column("Title", style="track.title")
    table.add_column("Album", style="track.album", max_width=30)

    for i, track in enumerate(display_tracks, 1):
        table.add_row(
            str(i),
            track.get("artist", "Unknown"),
            track.get("title", "Unknown"),
            track.get("album", ""),
        )

    console.print(table)

    if not show_all and total > 20:
        console.print(f"[dim]  ... and {total - 20} more tracks[/dim]")


def print_playlist_table(
    playlists: list[dict[str, Any]],
) -> None:
    """Display playlists in a table."""
    table = Table(
        title="Your Playlists",
        show_lines=False,
        border_style="dim",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="info")
    table.add_column("Tracks", style="dim", justify="right")
    table.add_column("ID", style="dim")

    for i, pl in enumerate(playlists, 1):
        table.add_row(
            str(i),
            pl.get("title", "Untitled"),
            str(pl.get("count", "?")),
            pl.get("playlistId", ""),
        )

    console.print(table)


def create_download_progress() -> Progress:
    """Create a pacman-inspired download progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        BarColumn(
            bar_width=40,
            complete_style="green",
            finished_style="green",
        ),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("[dim]{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console,
    )


def confirm_action(message: str) -> bool:
    """Ask user to confirm an action."""
    response = console.input(f"\n[warning]:: {message} [Y/n] [/warning]")
    return response.strip().lower() in ("", "y", "yes")


def print_sync_summary(
    total: int,
    downloaded: int,
    skipped: int,
    failed: int,
) -> None:
    """Print a summary after sync operation."""
    console.print("\n[header]:: Sync Summary[/header]")
    console.print(f"   Total tracks:      {total}")
    console.print(f"   [success]Downloaded:        {downloaded}[/success]")
    if skipped > 0:
        console.print(f"   [dim]Already synced:     {skipped}[/dim]")
    if failed > 0:
        console.print(f"   [error]Failed:            {failed}[/error]")
    console.print()
