"""Status command - show sync status information."""

from pathlib import Path

import typer

from src.cli.ui import console, print_header, print_info, print_warning
from src.core.config import load_config
from src.core.sync_state import SyncState


def status_command(
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Downloads directory"
    ),
) -> None:
    """Show the current sync status."""
    config = load_config()
    download_path = output_dir or config.download_dir

    state_file = download_path / ".sync_state.json"
    sync_state = SyncState(state_file)

    print_header("Sync Status")

    last_sync = sync_state.last_sync
    if last_sync:
        console.print(f"  Last sync:     {last_sync}")
    else:
        print_warning("Never synced")
        return

    console.print(f"  Total tracks:  {sync_state.total_tracks}")
    console.print(f"  Download dir:  {download_path}")

    playlists = sync_state.synced_playlists
    if playlists:
        console.print("\n  [bold]Synced Playlists:[/bold]")
        for pid, info in playlists.items():
            name = info.get("name", pid)
            count = info.get("track_count", "?")
            last = info.get("last_sync", "unknown")
            console.print(f"    {name}: {count} tracks (synced: {last})")

    print_info(f"State file: {state_file}")
