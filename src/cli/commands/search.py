"""Search command - search YouTube Music and download."""

import logging
from pathlib import Path

import questionary
import typer

from src.cli.ui import (
    console,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)
from src.core.auth import load_auth
from src.core.config import load_config
from src.core.download import download_track
from src.core.exceptions import AuthenticationError, DownloadError
from src.core.organizer import organize_track
from src.core.tagger import tag_file
from src.providers.youtube import YouTubeProvider

logger = logging.getLogger(__name__)


def search_command(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Output directory"
    ),
) -> None:
    """Search YouTube Music and optionally download results."""
    config = load_config()

    print_header("Authenticating")
    try:
        ytmusic = load_auth()
    except AuthenticationError as e:
        print_error(str(e))
        raise typer.Exit(code=1)

    provider = YouTubeProvider(ytmusic)
    print_success("Authenticated")

    print_header(f'Searching for "{query}"')
    results = provider.search(query, limit=limit)

    if not results:
        print_warning("No results found")
        raise typer.Exit(code=0)

    # Build choices with search results
    choices: list[questionary.Choice] = []
    for result in results:
        normalized = YouTubeProvider.normalize_track(result)
        artist = normalized["artist"]
        title = normalized["title"]
        album = normalized["album"]
        video_id = normalized["video_id"]

        if video_id:
            label = f"{artist} - {title}"
            if album and album != "Unknown Album":
                label += f" [{album}]"
            choices.append(questionary.Choice(title=label, value=normalized))

    if not choices:
        print_warning("No downloadable results")
        raise typer.Exit(code=0)

    # Let user select tracks to download
    selected = questionary.checkbox(
        "Select tracks to download:",
        choices=choices,
    ).ask()

    if not selected:
        print_info("No tracks selected")
        raise typer.Exit(code=0)

    download_path = output_dir or config.download_dir
    temp_dir = download_path / ".tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for track in selected:
        video_id = track["video_id"]
        title = track["title"]
        artist = track["artist"]
        console.print(f"[dim]  -> Downloading {artist} - {title}...[/dim]")

        try:
            filepath = download_track(
                video_id,
                temp_dir,
                config.audio_format,
                config.fallback_format,
            )
            if filepath:
                tag_file(filepath, track)
                final_path = organize_track(
                    filepath,
                    download_path,
                    track,
                    config.organize_by,
                    config.max_filename_length,
                    config.default_genre,
                )
                print_success(f"Saved: {final_path}")
            else:
                print_error(f"Download returned no file for {title}")
        except (DownloadError, Exception) as e:
            print_error(f"Failed: {title} - {e}")
