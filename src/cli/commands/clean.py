"""Clean command - remove orphaned downloaded files."""

import logging
from pathlib import Path

import typer

from src.cli.ui import (
    confirm_action,
    console,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)
from src.core.auth import load_auth
from src.core.config import load_config
from src.core.exceptions import AuthenticationError
from src.core.sync_state import SyncState
from src.providers.youtube import YouTubeProvider

logger = logging.getLogger(__name__)


def clean_command(
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Downloads directory"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Only show what would be removed",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Remove files that are no longer in your playlists."""
    config = load_config()
    download_path = output_dir or config.download_dir

    state_file = download_path / ".sync_state.json"
    sync_state = SyncState(state_file)

    if sync_state.total_tracks == 0:
        print_warning("No sync state found. Run 'ymd sync' first.")
        raise typer.Exit(code=0)

    # Fetch current playlist contents
    print_header("Authenticating")
    try:
        ytmusic = load_auth()
    except AuthenticationError as e:
        print_error(str(e))
        raise typer.Exit(code=1)

    provider = YouTubeProvider(ytmusic)
    print_success("Authenticated")

    print_header("Checking for orphaned tracks")

    # Gather current video IDs from all synced playlists
    current_ids: set[str] = set()

    playlists = sync_state.synced_playlists
    for pid in playlists:
        try:
            raw_tracks = provider.get_playlist_tracks(pid)
            for t in raw_tracks:
                vid = t.get("videoId", "")
                if vid:
                    current_ids.add(vid)
        except Exception as e:
            logger.warning("Could not fetch playlist %s: %s", pid, e)

    # Also check liked songs if they were synced
    try:
        liked = provider.get_liked_songs()
        for t in liked:
            vid = t.get("videoId", "")
            if vid:
                current_ids.add(vid)
    except Exception as e:
        logger.warning("Could not fetch liked songs: %s", e)

    orphaned = sync_state.get_orphaned_tracks(current_ids)

    if not orphaned:
        print_success("No orphaned tracks found. Everything is in sync!")
        raise typer.Exit(code=0)

    # Display orphaned tracks
    console.print(f"\n[warning]Found {len(orphaned)} " f"orphaned tracks:[/warning]")
    for track in orphaned:
        artist = track.get("artist", "Unknown")
        title = track.get("title", "Unknown")
        filepath = track.get("filepath", "")
        console.print(f"  [dim]-[/dim] {artist} - {title}")
        if filepath:
            console.print(f"    [dim]{filepath}[/dim]")

    if dry_run:
        print_info("Dry run - no files were removed")
        raise typer.Exit(code=0)

    # Confirm deletion
    if not yes and not confirm_action(f"Remove {len(orphaned)} orphaned tracks?"):
        print_info("Cancelled")
        raise typer.Exit(code=0)

    # Remove files and update state
    removed = 0
    for track in orphaned:
        filepath_str = track.get("filepath", "")
        video_id = track.get("video_id", "")

        if filepath_str:
            filepath = Path(filepath_str)
            if filepath.exists():
                try:
                    filepath.unlink()
                    removed += 1
                    # Remove empty parent directories
                    parent = filepath.parent
                    if parent.exists() and not any(parent.iterdir()):
                        parent.rmdir()
                except OSError as e:
                    print_error(f"Could not remove {filepath}: {e}")

        sync_state.remove_track(video_id)

    sync_state.save()
    print_success(f"Removed {removed} files")
