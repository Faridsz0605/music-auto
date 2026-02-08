"""Sync command - the main feature of ymd."""

import logging
from pathlib import Path
from typing import Any

import questionary
import typer

from src.cli.ui import (
    create_download_progress,
    print_error,
    print_header,
    print_info,
    print_success,
    print_sync_summary,
    print_track_table,
    print_warning,
)
from src.core.auth import load_auth
from src.core.config import load_config
from src.core.download import download_track
from src.core.exceptions import (
    AuthenticationError,
    DownloadError,
    MetadataError,
    OrganizationError,
)
from src.core.organizer import cleanup_temp_dir, organize_track
from src.core.sync_state import SyncState
from src.core.tagger import tag_file
from src.providers.youtube import YouTubeProvider

logger = logging.getLogger(__name__)


def sync_command(
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for downloads",
    ),
    liked: bool = typer.Option(False, "--liked", "-l", help="Sync liked songs"),
    playlist_id: list[str] | None = typer.Option(
        None,
        "--playlist-id",
        "-p",
        help="Playlist ID(s) to sync",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-download all tracks",
    ),
) -> None:
    """Sync playlists from YouTube Music and download tracks."""
    config = load_config()
    download_path = output_dir or config.download_dir

    # Authenticate
    print_header("Authenticating with YouTube Music")
    try:
        ytmusic = load_auth()
    except AuthenticationError as e:
        print_error(str(e))
        raise typer.Exit(code=1)

    provider = YouTubeProvider(ytmusic)
    print_success("Authenticated")

    # Determine which playlists to sync
    all_tracks: list[dict[str, str]] = []
    playlist_name = "Liked Songs"

    if liked:
        all_tracks, playlist_name = _fetch_liked(provider)
    elif playlist_id:
        all_tracks = _fetch_by_ids(provider, playlist_id)
    else:
        all_tracks, playlist_name = _interactive_select(provider)

    if not all_tracks:
        print_warning("No tracks to download")
        raise typer.Exit(code=0)

    # Incremental sync - filter already downloaded
    state_file = download_path / ".sync_state.json"
    sync_state = SyncState(state_file)

    if force:
        tracks_to_download = all_tracks
        print_info(f"Force mode: downloading all {len(all_tracks)} tracks")
    else:
        tracks_to_download = sync_state.get_new_tracks(all_tracks)
        skipped = len(all_tracks) - len(tracks_to_download)
        if skipped > 0:
            print_info(f"Skipping {skipped} already downloaded tracks")

    if not tracks_to_download:
        print_success("Everything is up to date!")
        raise typer.Exit(code=0)

    print_track_table(tracks_to_download, title="Tracks to download")

    # Download with progress
    print_header(f"Downloading {len(tracks_to_download)} tracks")

    temp_dir = download_path / ".tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    failed = 0
    skipped_count = len(all_tracks) - len(tracks_to_download)

    progress = create_download_progress()
    with progress:
        task_id = progress.add_task(
            "Downloading...",
            total=len(tracks_to_download),
        )

        for track in tracks_to_download:
            video_id = track.get("video_id", "")
            artist = track.get("artist", "Unknown")
            title = track.get("title", "Unknown")

            progress.update(
                task_id,
                description=f"{artist} - {title}",
            )

            if not video_id:
                logger.warning("Skipping track without video ID: %s", title)
                failed += 1
                progress.advance(task_id)
                continue

            try:
                filepath = _download_and_process(
                    video_id,
                    temp_dir,
                    download_path,
                    track,
                    config,
                    sync_state,
                )
                if filepath:
                    downloaded += 1
                else:
                    failed += 1
            except DownloadError as e:
                logger.error("Download failed: %s", e)
                failed += 1

            progress.advance(task_id)

    # Save sync state
    sync_state.update_last_sync()
    sync_state.save()

    # Cleanup temp directory
    cleanup_temp_dir(temp_dir)

    # Summary
    print_sync_summary(
        total=len(all_tracks),
        downloaded=downloaded,
        skipped=skipped_count,
        failed=failed,
    )


def _fetch_liked(
    provider: YouTubeProvider,
) -> tuple[list[dict[str, str]], str]:
    """Fetch and normalize liked songs."""
    print_header("Fetching liked songs")
    raw_tracks = provider.get_liked_songs()
    tracks = [YouTubeProvider.normalize_track(t) for t in raw_tracks]
    print_info(f"Found {len(tracks)} liked songs")
    return tracks, "Liked Songs"


def _fetch_by_ids(
    provider: YouTubeProvider,
    playlist_ids: list[str],
) -> list[dict[str, str]]:
    """Fetch tracks from specific playlist IDs."""
    all_tracks: list[dict[str, str]] = []
    for pid in playlist_ids:
        print_header(f"Fetching playlist {pid}")
        raw_tracks = provider.get_playlist_tracks(pid)
        normalized = [YouTubeProvider.normalize_track(t) for t in raw_tracks]
        all_tracks.extend(normalized)
        print_info(f"Found {len(normalized)} tracks")
    return all_tracks


def _interactive_select(
    provider: YouTubeProvider,
) -> tuple[list[dict[str, str]], str]:
    """Interactive playlist selection via questionary."""
    print_header("Fetching your playlists")
    playlists = provider.get_playlists()

    if not playlists:
        print_warning("No playlists found")
        raise typer.Exit(code=0)

    choices = [
        questionary.Choice(
            title=f"{pl['title']} ({pl['count']} tracks)",
            value=pl["playlistId"],
        )
        for pl in playlists
    ]
    choices.insert(
        0,
        questionary.Choice(
            title="Liked Songs",
            value="__liked__",
        ),
    )

    selected = questionary.checkbox(
        "Select playlists to sync:",
        choices=choices,
    ).ask()

    if not selected:
        print_warning("No playlists selected")
        raise typer.Exit(code=0)

    all_tracks: list[dict[str, str]] = []
    playlist_name = "Multiple Playlists"

    for sel in selected:
        if sel == "__liked__":
            print_header("Fetching liked songs")
            raw_tracks = provider.get_liked_songs()
            playlist_name = "Liked Songs"
        else:
            print_header(f"Fetching playlist {sel}")
            raw_tracks = provider.get_playlist_tracks(sel)

        normalized = [YouTubeProvider.normalize_track(t) for t in raw_tracks]
        all_tracks.extend(normalized)
        print_info(f"Found {len(normalized)} tracks")

    return all_tracks, playlist_name


def _download_and_process(
    video_id: str,
    temp_dir: Path,
    download_path: Path,
    track: dict[str, str],
    config: Any,
    sync_state: SyncState,
) -> Path | None:
    """Download, tag, organize a single track.

    Returns the final path on success, None on failure.
    """
    title = track.get("title", "Unknown")

    filepath = download_track(
        video_id,
        temp_dir,
        config.audio_format,
        config.fallback_format,
    )

    if filepath is None:
        return None

    # Tag metadata
    try:
        tag_file(filepath, track)
    except MetadataError as e:
        logger.warning("Tagging failed for %s: %s", title, e)

    # Organize into folder structure
    try:
        final_path = organize_track(
            filepath,
            download_path,
            track,
            config.organize_by,
            config.max_filename_length,
            config.default_genre,
        )
    except OrganizationError as e:
        logger.warning("Organization failed for %s: %s", title, e)
        final_path = filepath

    # Update sync state
    sync_state.mark_downloaded(
        video_id,
        str(final_path),
        track,
    )

    return final_path
