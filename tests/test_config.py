"""Tests for configuration module."""

import json
from pathlib import Path

from src.core.config import AppConfig, load_config, save_config


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_default_values(self) -> None:
        """Default config has sensible values."""
        config = AppConfig()
        assert config.download_dir == Path("downloads")
        assert config.audio_format == "best"
        assert config.fallback_format == "mp3"
        assert config.organize_by == "genre_artist"
        assert config.max_filename_length == 120
        assert config.max_concurrent_downloads == 3
        assert config.default_genre == "Unknown"

    def test_custom_values(self) -> None:
        """Config accepts custom values."""
        config = AppConfig(
            download_dir=Path("/music"),
            audio_format="mp3",
            max_filename_length=80,
        )
        assert config.download_dir == Path("/music")
        assert config.audio_format == "mp3"
        assert config.max_filename_length == 80

    def test_save_and_load(self, tmp_path: Path) -> None:
        """Config can be saved and loaded from disk."""
        config_path = tmp_path / "config.json"
        config = AppConfig(download_dir=Path("my_music"))
        config.save(config_path)

        loaded = AppConfig.load(config_path)
        assert loaded.download_dir == Path("my_music")
        assert loaded.audio_format == "best"

    def test_load_missing_file(self, tmp_path: Path) -> None:
        """Loading from nonexistent file returns defaults."""
        config = AppConfig.load(tmp_path / "nonexistent.json")
        assert config.download_dir == Path("downloads")

    def test_save_creates_valid_json(self, tmp_path: Path) -> None:
        """Saved config is valid JSON."""
        config_path = tmp_path / "config.json"
        config = AppConfig()
        config.save(config_path)
        data = json.loads(config_path.read_text())
        assert "download_dir" in data
        assert isinstance(data["download_dir"], str)

    def test_save_preserves_all_fields(self, tmp_path: Path) -> None:
        """Saved config includes every field."""
        config_path = tmp_path / "config.json"
        config = AppConfig()
        config.save(config_path)
        data = json.loads(config_path.read_text())
        assert "audio_format" in data
        assert "fallback_format" in data
        assert "organize_by" in data
        assert "max_filename_length" in data
        assert "max_concurrent_downloads" in data
        assert "default_genre" in data

    def test_roundtrip_all_fields(self, tmp_path: Path) -> None:
        """All fields survive a save/load cycle."""
        config_path = tmp_path / "config.json"
        original = AppConfig(
            download_dir=Path("custom"),
            audio_format="opus",
            fallback_format="m4a",
            organize_by="artist_album",
            max_filename_length=80,
            max_concurrent_downloads=5,
            default_genre="Electronic",
        )
        original.save(config_path)
        loaded = AppConfig.load(config_path)

        assert loaded.download_dir == original.download_dir
        assert loaded.audio_format == original.audio_format
        assert loaded.fallback_format == original.fallback_format
        assert loaded.organize_by == original.organize_by
        assert loaded.max_filename_length == original.max_filename_length
        assert loaded.max_concurrent_downloads == original.max_concurrent_downloads
        assert loaded.default_genre == original.default_genre


class TestLoadSaveConfig:
    """Tests for module-level functions."""

    def test_load_config_default(self, tmp_path: Path) -> None:
        """load_config returns defaults for missing file."""
        config = load_config(tmp_path / "missing.json")
        assert config.audio_format == "best"

    def test_load_config_from_file(self, config_file: Path) -> None:
        """load_config loads from existing file."""
        config = load_config(config_file)
        assert config.download_dir == Path("test_downloads")

    def test_save_config(self, tmp_path: Path) -> None:
        """save_config writes config to disk."""
        path = tmp_path / "config.json"
        config = AppConfig(audio_format="mp3")
        save_config(config, path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["audio_format"] == "mp3"

    def test_load_config_preserves_custom_fields(self, tmp_path: Path) -> None:
        """load_config preserves all fields from file."""
        path = tmp_path / "config.json"
        data = {
            "download_dir": "/custom/path",
            "audio_format": "opus",
            "fallback_format": "m4a",
            "organize_by": "playlist",
            "max_filename_length": 60,
            "max_concurrent_downloads": 1,
            "default_genre": "Jazz",
        }
        path.write_text(json.dumps(data))
        config = load_config(path)
        assert config.download_dir == Path("/custom/path")
        assert config.organize_by == "playlist"
        assert config.default_genre == "Jazz"
