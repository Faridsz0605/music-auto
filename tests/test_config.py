"""Tests for configuration module."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.config import AppConfig, load_config, save_config
from src.core.exceptions import ConfigError


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
        assert config.client_id == ""
        assert config.client_secret == ""

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

    def test_custom_oauth_values(self) -> None:
        """Config accepts client_id and client_secret."""
        config = AppConfig(
            client_id="my_client_id",
            client_secret="my_client_secret",
        )
        assert config.client_id == "my_client_id"
        assert config.client_secret == "my_client_secret"

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
        assert "client_id" in data
        assert "client_secret" in data

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
            client_id="test_id",
            client_secret="test_secret",
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
        assert loaded.client_id == original.client_id
        assert loaded.client_secret == original.client_secret


class TestConfigValidation:
    """Tests for strict config validation."""

    def test_invalid_audio_format(self) -> None:
        """Rejects unsupported audio_format."""
        with pytest.raises(ValueError, match="audio_format"):
            AppConfig(audio_format="wav")

    def test_invalid_fallback_format(self) -> None:
        """Rejects unsupported fallback_format."""
        with pytest.raises(ValueError, match="fallback_format"):
            AppConfig(fallback_format="flac")

    def test_invalid_organize_by(self) -> None:
        """Rejects unsupported organize_by value."""
        with pytest.raises(ValueError, match="organize_by"):
            AppConfig(organize_by="random_order")

    def test_zero_filename_length(self) -> None:
        """Rejects max_filename_length <= 0."""
        with pytest.raises(ValueError):
            AppConfig(max_filename_length=0)

    def test_negative_filename_length(self) -> None:
        """Rejects negative max_filename_length."""
        with pytest.raises(ValueError):
            AppConfig(max_filename_length=-10)

    def test_filename_length_too_large(self) -> None:
        """Rejects max_filename_length > 255."""
        with pytest.raises(ValueError):
            AppConfig(max_filename_length=300)

    def test_zero_concurrent_downloads(self) -> None:
        """Rejects max_concurrent_downloads <= 0."""
        with pytest.raises(ValueError):
            AppConfig(max_concurrent_downloads=0)

    def test_concurrent_downloads_too_large(self) -> None:
        """Rejects max_concurrent_downloads > 10."""
        with pytest.raises(ValueError):
            AppConfig(max_concurrent_downloads=20)

    def test_valid_all_audio_formats(self) -> None:
        """Accepts all valid audio formats."""
        for fmt in ("best", "mp3", "m4a", "opus"):
            config = AppConfig(audio_format=fmt)
            assert config.audio_format == fmt

    def test_valid_all_organize_by(self) -> None:
        """Accepts all valid organize_by schemes."""
        for scheme in ("genre_artist", "artist_album", "playlist"):
            config = AppConfig(organize_by=scheme)
            assert config.organize_by == scheme

    def test_invalid_json_file_raises_config_error(self, tmp_path: Path) -> None:
        """Loading invalid JSON raises ConfigError."""
        path = tmp_path / "bad.json"
        path.write_text("not valid json {{{")
        with pytest.raises(ConfigError, match="Invalid JSON"):
            AppConfig.load(path)

    def test_invalid_field_value_in_file_raises_config_error(
        self, tmp_path: Path
    ) -> None:
        """Loading config file with invalid field values raises ConfigError."""
        path = tmp_path / "config.json"
        data = {"organize_by": "invalid_scheme"}
        path.write_text(json.dumps(data))
        with pytest.raises(ConfigError, match="Invalid configuration"):
            AppConfig.load(path)


class TestEnvVarOverrides:
    """Tests for environment variable overrides."""

    def test_env_var_overrides_client_id(self, tmp_path: Path) -> None:
        """YMD_CLIENT_ID env var overrides config file value."""
        path = tmp_path / "config.json"
        data = {"client_id": "file_id", "client_secret": "file_secret"}
        path.write_text(json.dumps(data))

        with patch.dict(os.environ, {"YMD_CLIENT_ID": "env_id"}):
            config = AppConfig.load(path)

        assert config.client_id == "env_id"
        assert config.client_secret == "file_secret"

    def test_env_var_overrides_client_secret(self, tmp_path: Path) -> None:
        """YMD_CLIENT_SECRET env var overrides config file value."""
        path = tmp_path / "config.json"
        data = {"client_id": "file_id", "client_secret": "file_secret"}
        path.write_text(json.dumps(data))

        with patch.dict(os.environ, {"YMD_CLIENT_SECRET": "env_secret"}):
            config = AppConfig.load(path)

        assert config.client_id == "file_id"
        assert config.client_secret == "env_secret"

    def test_both_env_vars_override(self, tmp_path: Path) -> None:
        """Both env vars override config file values."""
        path = tmp_path / "config.json"
        data = {"client_id": "file_id", "client_secret": "file_secret"}
        path.write_text(json.dumps(data))

        with patch.dict(
            os.environ,
            {"YMD_CLIENT_ID": "env_id", "YMD_CLIENT_SECRET": "env_secret"},
        ):
            config = AppConfig.load(path)

        assert config.client_id == "env_id"
        assert config.client_secret == "env_secret"

    def test_env_vars_without_config_file(self, tmp_path: Path) -> None:
        """Env vars work even when config file doesn't exist."""
        with patch.dict(
            os.environ,
            {"YMD_CLIENT_ID": "env_id", "YMD_CLIENT_SECRET": "env_secret"},
        ):
            config = AppConfig.load(tmp_path / "nonexistent.json")

        assert config.client_id == "env_id"
        assert config.client_secret == "env_secret"

    def test_empty_env_vars_dont_override(self, tmp_path: Path) -> None:
        """Empty env vars don't override config file values."""
        path = tmp_path / "config.json"
        data = {"client_id": "file_id", "client_secret": "file_secret"}
        path.write_text(json.dumps(data))

        # Ensure env vars are not set
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("YMD_CLIENT_ID", "YMD_CLIENT_SECRET")
        }
        with patch.dict(os.environ, env, clear=True):
            config = AppConfig.load(path)

        assert config.client_id == "file_id"
        assert config.client_secret == "file_secret"


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

    def test_load_config_with_oauth_fields(self, tmp_path: Path) -> None:
        """load_config loads OAuth fields when present."""
        path = tmp_path / "config.json"
        data = {
            "download_dir": "downloads",
            "client_id": "my_id",
            "client_secret": "my_secret",
        }
        path.write_text(json.dumps(data))
        config = load_config(path)
        assert config.client_id == "my_id"
        assert config.client_secret == "my_secret"
