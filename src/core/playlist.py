"""Playlist fetching and management."""

from typing import Any

from rich.console import Console
from ytmusicapi import YTMusic

from src.core.exceptions import PlaylistNotFoundError

console = Console()


def fetch_liked_songs(ytmusic: YTMusic) -> list[dict[str, Any]]:
    """
    Fetch user's liked songs from YouTube Music.

    Args:
        ytmusic: Authenticated YTMusic instance.

    Returns:
        List of song dictionaries with metadata.
    """
    console.print("[cyan]Fetching liked songs...[/cyan]")
    try:
        liked_songs = ytmusic.get_liked_songs(limit=5000)
        tracks: list[dict[str, Any]] = liked_songs.get("tracks", [])
        console.print(f"[green]Found {len(tracks)} liked songs[/green]")
        return tracks
    except Exception as e:
        console.print(f"[red]Error fetching liked songs:[/red] {e}")
        return []


def fetch_playlist(ytmusic: YTMusic, playlist_id: str) -> list[dict[str, Any]]:
    """
    Fetch a specific playlist from YouTube Music.

    Args:
        ytmusic: Authenticated YTMusic instance.
        playlist_id: YouTube Music playlist ID.

    Returns:
        List of song dictionaries with metadata.

    Raises:
        PlaylistNotFoundError: If playlist doesn't exist or is inaccessible.
    """
    console.print(f"[cyan]Fetching playlist {playlist_id}...[/cyan]")
    try:
        playlist = ytmusic.get_playlist(playlist_id, limit=5000)
        tracks: list[dict[str, Any]] = playlist.get("tracks", [])
        console.print(f"[green]Found {len(tracks)} tracks in playlist[/green]")
        return tracks
    except Exception as e:
        raise PlaylistNotFoundError(
            f"Failed to fetch playlist {playlist_id}: {e}"
        ) from e


def normalize_track_metadata(track: dict[str, Any]) -> dict[str, str]:
    """
    Extract and normalize metadata from a YouTube Music track object.

    Args:
        track: Raw track dictionary from ytmusicapi.

    Returns:
        Dictionary with normalized keys: title, artist, album, video_id.
    """
    # Extract artists (can be multiple)
    artists = track.get("artists", [])
    artist_name = ", ".join(a.get("name", "Unknown") for a in artists)

    # Extract album info
    album = track.get("album", {})
    album_name = album.get("name", "Unknown Album") if album else "Unknown Album"

    return {
        "title": track.get("title", "Unknown Title"),
        "artist": artist_name or "Unknown Artist",
        "album": album_name,
        "video_id": track.get("videoId", ""),
        "duration": track.get("duration", ""),
    }
