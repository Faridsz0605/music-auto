"""Download engine using yt-dlp for audio extraction."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from src.core.exceptions import DownloadError

logger = logging.getLogger(__name__)

# yt-dlp format selection:
# Best audio quality available, prefer m4a/opus containers
BEST_AUDIO_FORMAT = "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio"
MP3_POSTPROCESS = {
    "key": "FFmpegExtractAudio",
    "preferredcodec": "mp3",
    "preferredquality": "320",
}

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds: 2, 4, 8


def _build_yt_dlp_opts(
    output_path: Path,
    audio_format: str = "best",
    fallback_format: str = "mp3",
) -> dict[str, Any]:
    """
    Build yt-dlp options dictionary.

    Args:
        output_path: Directory to save downloaded file.
        audio_format: Preferred format (best, mp3, m4a, opus).
        fallback_format: Fallback if best format isn't
            DAP-compatible.

    Returns:
        yt-dlp options dictionary.
    """
    # Template: save to temp location, we'll rename after tagging
    outtmpl = str(output_path / "%(id)s.%(ext)s")

    opts: dict[str, Any] = {
        "format": BEST_AUDIO_FORMAT,
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "writethumbnail": True,
        "postprocessors": [
            {
                "key": "FFmpegMetadata",
            },
            {
                "key": "EmbedThumbnail",
            },
        ],
    }

    # If user wants mp3 specifically or as fallback
    if audio_format == "mp3" or fallback_format == "mp3":
        opts["postprocessors"].insert(0, MP3_POSTPROCESS)

    return opts


def _is_retryable_error(error: Exception) -> bool:
    """Check if an error is transient and worth retrying.

    Args:
        error: The exception that occurred.

    Returns:
        True if the error is likely transient (network, rate limit).
    """
    error_str = str(error).lower()
    retryable_patterns = [
        "403",
        "429",
        "http error",
        "connection",
        "timeout",
        "network",
        "temporary",
        "unavailable",
        "rate limit",
    ]
    return any(pattern in error_str for pattern in retryable_patterns)


def download_track(
    video_id: str,
    output_dir: Path,
    audio_format: str = "best",
    fallback_format: str = "mp3",
    max_retries: int = MAX_RETRIES,
) -> Path | None:
    """
    Download a single track from YouTube Music with retry logic.

    Retries up to max_retries times with exponential backoff
    (2s, 4s, 8s) for transient errors (403, 429, network issues).

    Args:
        video_id: YouTube video ID.
        output_dir: Directory to save the downloaded file.
        audio_format: Preferred audio format.
        fallback_format: Fallback format for DAP compatibility.
        max_retries: Maximum number of retry attempts.

    Returns:
        Path to downloaded file, or None if download failed.

    Raises:
        DownloadError: If download fails after all attempts.
    """
    # Import here to avoid import-time side effects
    import yt_dlp

    url = f"https://music.youtube.com/watch?v={video_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    opts = _build_yt_dlp_opts(output_dir, audio_format, fallback_format)

    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    raise DownloadError(f"No info extracted for {video_id}")

                # Find the downloaded file
                # yt-dlp may change extension after postprocessing
                for ext in ["mp3", "m4a", "opus", "webm", "ogg"]:
                    candidate = output_dir / f"{video_id}.{ext}"
                    if candidate.exists():
                        logger.info("Downloaded: %s", candidate)
                        return candidate

                # Check for any file matching the video_id
                for file in output_dir.iterdir():
                    if file.stem == video_id and file.is_file():
                        return file

                raise DownloadError(
                    f"Download completed but file not found for {video_id}"
                )

        except DownloadError:
            raise
        except Exception as e:
            last_error = e
            if attempt < max_retries and _is_retryable_error(e):
                wait_time = RETRY_BACKOFF_BASE ** (attempt + 1)
                logger.warning(
                    "Attempt %d/%d failed for %s: %s. "
                    "Retrying in %ds...",
                    attempt + 1,
                    max_retries + 1,
                    video_id,
                    e,
                    wait_time,
                )
                time.sleep(wait_time)
            else:
                break

    raise DownloadError(
        f"Failed to download {video_id} after "
        f"{max_retries + 1} attempts: {last_error}"
    ) from last_error


def download_tracks_parallel(
    tracks: list[dict[str, str]],
    output_dir: Path,
    audio_format: str = "best",
    fallback_format: str = "mp3",
    max_workers: int = 3,
    progress_callback: Any = None,
) -> list[dict[str, Any]]:
    """
    Download multiple tracks in parallel.

    Args:
        tracks: List of normalized track dicts (must have
            'video_id').
        output_dir: Base download directory.
        audio_format: Preferred audio format.
        fallback_format: Fallback format.
        max_workers: Max concurrent downloads.
        progress_callback: Optional callable(track, filepath, error)
            for progress updates.

    Returns:
        List of result dicts with keys: track, filepath, error.
    """
    results: list[dict[str, Any]] = []

    # Use a temp directory for raw downloads, then organize
    temp_dir = output_dir / ".tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    def _download_one(
        track: dict[str, str],
    ) -> dict[str, Any]:
        video_id = track.get("video_id", "")
        if not video_id:
            return {
                "track": track,
                "filepath": None,
                "error": "Missing video_id",
            }
        try:
            filepath = download_track(video_id, temp_dir, audio_format, fallback_format)
            return {
                "track": track,
                "filepath": filepath,
                "error": None,
            }
        except DownloadError as e:
            logger.error(f"Download failed: {e}")
            return {
                "track": track,
                "filepath": None,
                "error": str(e),
            }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_track = {
            executor.submit(_download_one, track): track for track in tracks
        }

        for future in as_completed(future_to_track):
            result = future.result()
            results.append(result)
            if progress_callback is not None:
                progress_callback(
                    result["track"],
                    result["filepath"],
                    result["error"],
                )

    return results
