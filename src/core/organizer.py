"""File organizer - moves and renames downloaded tracks for DAP compatibility."""

import logging
import re
import shutil
import unicodedata
from pathlib import Path

from src.core.exceptions import OrganizationError

logger = logging.getLogger(__name__)

# Characters not allowed in filenames on FAT32/NTFS
INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Multiple spaces/dots/dashes cleanup
MULTI_SPACE = re.compile(r"\s+")
MULTI_DASH = re.compile(r"-{2,}")


def sanitize_filename(name: str, max_length: int = 120) -> str:
    """
    Sanitize a string for use as a filename.

    Removes invalid characters, normalizes unicode, and truncates
    to max_length for DAP filesystem compatibility.

    Args:
        name: Raw filename string.
        max_length: Maximum character length.

    Returns:
        Sanitized filename string.
    """
    # Normalize unicode characters
    name = unicodedata.normalize("NFKD", name)

    # Remove invalid filesystem characters
    name = INVALID_CHARS.sub("", name)

    # Replace common problematic patterns
    name = name.replace("&", "and")

    # Collapse whitespace and trim
    name = MULTI_SPACE.sub(" ", name).strip()
    name = MULTI_DASH.sub("-", name)

    # Remove leading/trailing dots and spaces
    name = name.strip(". ")

    # Truncate to max length
    if len(name) > max_length:
        name = name[:max_length].rstrip(". ")

    # Fallback for empty names
    if not name:
        name = "Unknown"

    return name


def sanitize_dirname(name: str, max_length: int = 80) -> str:
    """
    Sanitize a string for use as a directory name.

    More restrictive than filename sanitization.

    Args:
        name: Raw directory name.
        max_length: Maximum character length.

    Returns:
        Sanitized directory name.
    """
    return sanitize_filename(name, max_length)


def organize_track(
    source_path: Path,
    base_dir: Path,
    metadata: dict[str, str],
    organize_by: str = "genre_artist",
    max_filename_length: int = 120,
    default_genre: str = "Unknown",
) -> Path:
    """
    Move a downloaded track to its organized location.

    Creates directory structure based on organization scheme and
    renames file with sanitized artist - title format.

    Args:
        source_path: Path to the downloaded file.
        base_dir: Base download directory.
        metadata: Track metadata dict with title, artist, album,
            genre.
        organize_by: Organization scheme
            (genre_artist, artist_album, playlist).
        max_filename_length: Max filename character length.
        default_genre: Default genre when not available.

    Returns:
        Path to the organized file.

    Raises:
        OrganizationError: If file operations fail.
    """
    if not source_path.exists():
        raise OrganizationError(f"Source file not found: {source_path}")

    ext = source_path.suffix
    artist = sanitize_dirname(metadata.get("artist", "Unknown Artist"))
    title = sanitize_filename(
        metadata.get("title", "Unknown Title"), max_filename_length
    )
    album = sanitize_dirname(metadata.get("album", "Unknown Album"))
    genre = sanitize_dirname(metadata.get("genre", "") or default_genre)

    # Build target directory based on organization scheme
    if organize_by == "genre_artist":
        target_dir = base_dir / genre / artist
    elif organize_by == "artist_album":
        target_dir = base_dir / artist / album
    elif organize_by == "playlist":
        playlist_name = sanitize_dirname(metadata.get("playlist", "Unknown Playlist"))
        target_dir = base_dir / playlist_name
    else:
        target_dir = base_dir / genre / artist

    # Build filename: "Artist - Title.ext"
    filename = f"{artist} - {title}"

    # Ensure total filename (with ext) fits in max_filename_length
    max_name_len = max_filename_length - len(ext)
    if len(filename) > max_name_len:
        filename = filename[:max_name_len].rstrip(". ")

    filename = f"{filename}{ext}"

    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename

    # Handle duplicates by adding a counter
    counter = 1
    while target_path.exists():
        stem = f"{artist} - {title} ({counter})"
        if len(stem) > max_name_len:
            stem = stem[:max_name_len].rstrip(". ")
        target_path = target_dir / f"{stem}{ext}"
        counter += 1

    try:
        shutil.move(str(source_path), str(target_path))
        logger.info(f"Organized: {target_path}")
        return target_path
    except OSError as e:
        raise OrganizationError(
            f"Failed to move {source_path} to {target_path}: {e}"
        ) from e


def cleanup_temp_dir(temp_dir: Path) -> None:
    """
    Remove temporary download directory and any leftover files.

    Args:
        temp_dir: Path to the temp directory.
    """
    if temp_dir.exists() and temp_dir.is_dir():
        # Remove thumbnail files and other temp artifacts
        for file in temp_dir.iterdir():
            if file.is_file():
                try:
                    file.unlink()
                except OSError as e:
                    logger.warning(f"Could not remove temp file {file}: {e}")
        try:
            temp_dir.rmdir()
        except OSError:
            pass  # Directory not empty, leave it
