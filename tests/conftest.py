"""Shared test fixtures."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_ytmusic() -> MagicMock:
    """Create a mock YTMusic instance."""
    mock = MagicMock()
    mock.get_library_playlists.return_value = [
        {"playlistId": "PL001", "title": "Rock Classics", "count": 50},
        {"playlistId": "PL002", "title": "Chill Vibes", "count": 30},
    ]
    return mock


@pytest.fixture
def sample_track() -> dict[str, Any]:
    """Sample raw track from ytmusicapi."""
    return {
        "title": "Bohemian Rhapsody",
        "artists": [{"name": "Queen"}],
        "album": {"name": "A Night at the Opera"},
        "videoId": "fJ9rUzIMcZQ",
        "duration": "5:55",
        "category": "Rock",
    }


@pytest.fixture
def sample_tracks() -> list[dict[str, Any]]:
    """Multiple sample tracks."""
    return [
        {
            "title": "Bohemian Rhapsody",
            "artists": [{"name": "Queen"}],
            "album": {"name": "A Night at the Opera"},
            "videoId": "fJ9rUzIMcZQ",
            "duration": "5:55",
            "category": "Rock",
        },
        {
            "title": "Stairway to Heaven",
            "artists": [{"name": "Led Zeppelin"}],
            "album": {"name": "Led Zeppelin IV"},
            "videoId": "QkF3oxziUI4",
            "duration": "8:02",
            "category": "Rock",
        },
        {
            "title": "Hotel California",
            "artists": [{"name": "Eagles"}],
            "album": {"name": "Hotel California"},
            "videoId": "BciS5krYL80",
            "duration": "6:30",
            "category": "Rock",
        },
    ]


@pytest.fixture
def normalized_track() -> dict[str, str]:
    """Pre-normalized track metadata."""
    return {
        "title": "Bohemian Rhapsody",
        "artist": "Queen",
        "album": "A Night at the Opera",
        "video_id": "fJ9rUzIMcZQ",
        "duration": "5:55",
        "genre": "Rock",
    }


@pytest.fixture
def config_data() -> dict[str, Any]:
    """Sample configuration data."""
    return {
        "download_dir": "test_downloads",
        "audio_format": "best",
        "fallback_format": "mp3",
        "organize_by": "genre_artist",
        "max_filename_length": 120,
        "max_concurrent_downloads": 3,
        "default_genre": "Unknown",
    }


@pytest.fixture
def config_file(tmp_path: Path, config_data: dict[str, Any]) -> Path:
    """Create a temporary config file."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config_data))
    return path
