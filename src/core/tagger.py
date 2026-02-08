"""Audio metadata tagger using Mutagen."""

import logging
from pathlib import Path

from mutagen import File as MutagenFile  # type: ignore[attr-defined]
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3  # type: ignore[attr-defined]
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover

from src.core.exceptions import MetadataError

logger = logging.getLogger(__name__)


def tag_file(
    filepath: Path,
    metadata: dict[str, str],
    cover_path: Path | None = None,
) -> None:
    """
    Apply metadata tags to an audio file.

    Args:
        filepath: Path to the audio file.
        metadata: Dict with keys: title, artist, album, genre.
        cover_path: Optional path to cover art image.

    Raises:
        MetadataError: If tagging fails.
    """
    if not filepath.exists():
        raise MetadataError(f"File not found: {filepath}")

    ext = filepath.suffix.lower()

    try:
        if ext == ".mp3":
            _tag_mp3(filepath, metadata, cover_path)
        elif ext in (".m4a", ".mp4", ".aac"):
            _tag_m4a(filepath, metadata, cover_path)
        else:
            # For opus/ogg/webm, try generic mutagen
            _tag_generic(filepath, metadata)
        logger.info(f"Tagged: {filepath.name}")
    except MetadataError:
        raise
    except Exception as e:
        raise MetadataError(f"Failed to tag {filepath.name}: {e}") from e


def _tag_mp3(
    filepath: Path,
    metadata: dict[str, str],
    cover_path: Path | None = None,
) -> None:
    """Tag an MP3 file using EasyID3."""
    try:
        audio = EasyID3(str(filepath))
    except Exception:
        # No ID3 tag exists, create one
        audio_raw = MP3(str(filepath))
        audio_raw.add_tags()
        audio_raw.save()
        audio = EasyID3(str(filepath))

    audio["title"] = metadata.get("title", "Unknown")
    audio["artist"] = metadata.get("artist", "Unknown")
    audio["album"] = metadata.get("album", "Unknown")

    genre = metadata.get("genre", "")
    if genre:
        audio["genre"] = genre

    audio.save()

    # Embed cover art if provided
    if cover_path and cover_path.exists():
        _embed_cover_mp3(filepath, cover_path)


def _embed_cover_mp3(filepath: Path, cover_path: Path) -> None:
    """Embed cover art in MP3 file."""
    audio = ID3(str(filepath))
    cover_data = cover_path.read_bytes()

    mime = "image/jpeg"
    if cover_path.suffix.lower() == ".png":
        mime = "image/png"

    audio.add(
        APIC(
            encoding=3,
            mime=mime,
            type=3,  # Cover (front)
            desc="Cover",
            data=cover_data,
        )
    )
    audio.save()


def _tag_m4a(
    filepath: Path,
    metadata: dict[str, str],
    cover_path: Path | None = None,
) -> None:
    """Tag an M4A/MP4 file."""
    audio = MP4(str(filepath))

    audio["\xa9nam"] = [metadata.get("title", "Unknown")]
    audio["\xa9ART"] = [metadata.get("artist", "Unknown")]
    audio["\xa9alb"] = [metadata.get("album", "Unknown")]

    genre = metadata.get("genre", "")
    if genre:
        audio["\xa9gen"] = [genre]

    if cover_path and cover_path.exists():
        cover_data = cover_path.read_bytes()
        fmt = MP4Cover.FORMAT_JPEG
        if cover_path.suffix.lower() == ".png":
            fmt = MP4Cover.FORMAT_PNG
        audio["covr"] = [MP4Cover(cover_data, imageformat=fmt)]

    audio.save()


def _tag_generic(filepath: Path, metadata: dict[str, str]) -> None:
    """Tag using generic Mutagen interface (for ogg/opus/etc)."""
    audio = MutagenFile(str(filepath))
    if audio is None:
        raise MetadataError(f"Unsupported format: {filepath.suffix}")

    if audio.tags is None:
        audio.add_tags()

    tags = audio.tags
    assert tags is not None
    tags["title"] = [metadata.get("title", "Unknown")]
    tags["artist"] = [metadata.get("artist", "Unknown")]
    tags["album"] = [metadata.get("album", "Unknown")]

    genre = metadata.get("genre", "")
    if genre:
        tags["genre"] = [genre]

    audio.save()
