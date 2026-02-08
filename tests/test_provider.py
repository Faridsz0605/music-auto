"""Tests for YouTube Music provider."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from src.core.exceptions import AuthenticationError, PlaylistNotFoundError
from src.providers.youtube import YouTubeProvider


class TestYouTubeProvider:
    """Tests for YouTubeProvider class."""

    def test_get_playlists(self, mock_ytmusic: MagicMock) -> None:
        """Fetches and normalizes playlists."""
        provider = YouTubeProvider(mock_ytmusic)
        playlists = provider.get_playlists()

        assert len(playlists) == 2
        assert playlists[0]["title"] == "Rock Classics"
        assert playlists[0]["playlistId"] == "PL001"
        assert playlists[1]["title"] == "Chill Vibes"

    def test_get_playlists_failure_raises_auth_error(
        self, mock_ytmusic: MagicMock
    ) -> None:
        """Playlist fetch failure raises AuthenticationError."""
        mock_ytmusic.get_library_playlists.side_effect = Exception("API Error")
        provider = YouTubeProvider(mock_ytmusic)

        with pytest.raises(AuthenticationError, match="Could not fetch playlists"):
            provider.get_playlists()

    def test_get_liked_songs(self, mock_ytmusic: MagicMock) -> None:
        """Fetches liked songs from tracks key."""
        mock_ytmusic.get_liked_songs.return_value = {
            "tracks": [
                {"title": "Song", "videoId": "v1"},
                {"title": "Song 2", "videoId": "v2"},
            ]
        }
        provider = YouTubeProvider(mock_ytmusic)
        tracks = provider.get_liked_songs()

        assert len(tracks) == 2
        assert tracks[0]["title"] == "Song"
        mock_ytmusic.get_liked_songs.assert_called_once_with(limit=5000)

    def test_get_liked_songs_failure_raises_auth_error(
        self, mock_ytmusic: MagicMock
    ) -> None:
        """Liked songs fetch failure raises AuthenticationError."""
        mock_ytmusic.get_liked_songs.side_effect = Exception("Unauthorized")
        provider = YouTubeProvider(mock_ytmusic)

        with pytest.raises(AuthenticationError, match="Could not fetch liked songs"):
            provider.get_liked_songs()

    def test_get_playlist_tracks(self, mock_ytmusic: MagicMock) -> None:
        """Fetches tracks from specific playlist."""
        mock_ytmusic.get_playlist.return_value = {
            "tracks": [
                {"title": "Track 1"},
                {"title": "Track 2"},
            ]
        }
        provider = YouTubeProvider(mock_ytmusic)
        tracks = provider.get_playlist_tracks("PL001")

        assert len(tracks) == 2
        mock_ytmusic.get_playlist.assert_called_once_with("PL001", limit=5000)

    def test_playlist_not_found(self, mock_ytmusic: MagicMock) -> None:
        """Missing playlist raises PlaylistNotFoundError."""
        mock_ytmusic.get_playlist.side_effect = Exception("Not found")
        provider = YouTubeProvider(mock_ytmusic)

        with pytest.raises(PlaylistNotFoundError, match="PL_INVALID"):
            provider.get_playlist_tracks("PL_INVALID")

    def test_search(self, mock_ytmusic: MagicMock) -> None:
        """Search returns results."""
        mock_ytmusic.search.return_value = [
            {"title": "Result 1", "videoId": "v1"},
            {"title": "Result 2", "videoId": "v2"},
        ]
        provider = YouTubeProvider(mock_ytmusic)
        results = provider.search("test query")

        assert len(results) == 2
        mock_ytmusic.search.assert_called_once_with(
            "test query", filter="songs", limit=20
        )

    def test_search_with_custom_params(self, mock_ytmusic: MagicMock) -> None:
        """Search forwards filter_type and limit."""
        mock_ytmusic.search.return_value = []
        provider = YouTubeProvider(mock_ytmusic)
        provider.search("query", filter_type="albums", limit=5)

        mock_ytmusic.search.assert_called_once_with("query", filter="albums", limit=5)

    def test_search_failure_returns_empty(self, mock_ytmusic: MagicMock) -> None:
        """Failed search returns empty list instead of raising."""
        mock_ytmusic.search.side_effect = Exception("API Error")
        provider = YouTubeProvider(mock_ytmusic)
        results = provider.search("test")
        assert results == []


class TestNormalizeTrack:
    """Tests for track normalization."""

    def test_full_metadata(self, sample_track: dict[str, Any]) -> None:
        """All fields are extracted correctly."""
        result = YouTubeProvider.normalize_track(sample_track)
        assert result["title"] == "Bohemian Rhapsody"
        assert result["artist"] == "Queen"
        assert result["album"] == "A Night at the Opera"
        assert result["video_id"] == "fJ9rUzIMcZQ"
        assert result["duration"] == "5:55"
        assert result["genre"] == "Rock"

    def test_missing_artists(self) -> None:
        """Missing artists defaults to 'Unknown Artist'."""
        track: dict[str, Any] = {"title": "Song", "videoId": "v1"}
        result = YouTubeProvider.normalize_track(track)
        assert result["artist"] == "Unknown Artist"

    def test_empty_artists_list(self) -> None:
        """Empty artists list defaults to 'Unknown Artist'."""
        track: dict[str, Any] = {
            "title": "Song",
            "artists": [],
            "videoId": "v1",
        }
        result = YouTubeProvider.normalize_track(track)
        assert result["artist"] == "Unknown Artist"

    def test_none_artists(self) -> None:
        """None artists defaults to 'Unknown Artist'."""
        track: dict[str, Any] = {
            "title": "Song",
            "artists": None,
            "videoId": "v1",
        }
        result = YouTubeProvider.normalize_track(track)
        assert result["artist"] == "Unknown Artist"

    def test_missing_album(self) -> None:
        """Missing album defaults to 'Unknown Album'."""
        track: dict[str, Any] = {"title": "Song", "videoId": "v1"}
        result = YouTubeProvider.normalize_track(track)
        assert result["album"] == "Unknown Album"

    def test_none_album(self) -> None:
        """None album defaults to 'Unknown Album'."""
        track: dict[str, Any] = {
            "title": "Song",
            "album": None,
            "videoId": "v1",
        }
        result = YouTubeProvider.normalize_track(track)
        assert result["album"] == "Unknown Album"

    def test_multiple_artists(self) -> None:
        """Multiple artists are joined with comma."""
        track: dict[str, Any] = {
            "title": "Collab",
            "artists": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
            "videoId": "v1",
        }
        result = YouTubeProvider.normalize_track(track)
        assert result["artist"] == "A, B, C"

    def test_missing_title(self) -> None:
        """Missing title defaults to 'Unknown Title'."""
        track: dict[str, Any] = {"videoId": "v1"}
        result = YouTubeProvider.normalize_track(track)
        assert result["title"] == "Unknown Title"

    def test_missing_video_id(self) -> None:
        """Missing videoId defaults to empty string."""
        track: dict[str, Any] = {"title": "Song"}
        result = YouTubeProvider.normalize_track(track)
        assert result["video_id"] == ""

    def test_missing_duration(self) -> None:
        """Missing duration defaults to '0:00'."""
        track: dict[str, Any] = {"title": "Song", "videoId": "v1"}
        result = YouTubeProvider.normalize_track(track)
        assert result["duration"] == "0:00"

    def test_genre_from_category(self) -> None:
        """Genre is extracted from category field."""
        track: dict[str, Any] = {
            "title": "Song",
            "videoId": "v1",
            "category": "Electronic",
        }
        result = YouTubeProvider.normalize_track(track)
        assert result["genre"] == "Electronic"

    def test_no_genre_without_category(self) -> None:
        """Genre is empty string when no category present."""
        track: dict[str, Any] = {"title": "Song", "videoId": "v1"}
        result = YouTubeProvider.normalize_track(track)
        assert result["genre"] == ""

    def test_normalize_returns_all_keys(self) -> None:
        """Normalized track has all expected keys."""
        track: dict[str, Any] = {"title": "Song", "videoId": "v1"}
        result = YouTubeProvider.normalize_track(track)
        expected_keys = {"title", "artist", "album", "video_id", "duration", "genre"}
        assert set(result.keys()) == expected_keys
