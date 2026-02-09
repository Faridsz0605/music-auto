"""Application configuration with Pydantic validation."""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.core.exceptions import ConfigError

CONFIG_FILE = Path("config.json")
CONFIG_EXAMPLE = Path("config.example.json")

VALID_AUDIO_FORMATS = {"best", "mp3", "m4a", "opus"}
VALID_ORGANIZE_BY = {"genre_artist", "artist_album", "playlist"}


class AppConfig(BaseModel):
    """Application configuration model."""

    download_dir: Path = Field(
        default=Path("downloads"), description="Download directory"
    )
    audio_format: str = Field(
        default="best",
        description="Preferred audio format: best, mp3, m4a, opus",
    )
    fallback_format: str = Field(
        default="mp3",
        description="Fallback format when best is not DAP-compatible",
    )
    organize_by: str = Field(
        default="genre_artist",
        description="Organization: genre_artist, artist_album, playlist",
    )
    max_filename_length: int = Field(
        default=120,
        description="Max filename length for DAP compatibility",
        gt=0,
        le=255,
    )
    max_concurrent_downloads: int = Field(
        default=3,
        description="Max parallel downloads",
        gt=0,
        le=10,
    )
    default_genre: str = Field(
        default="Unknown",
        description="Default genre when not available from YTM",
    )
    client_id: str = Field(
        default="",
        description="Google OAuth Client ID for YouTube Data API",
    )
    client_secret: str = Field(
        default="",
        description="Google OAuth Client Secret for YouTube Data API",
    )

    @field_validator("audio_format")
    @classmethod
    def validate_audio_format(cls, v: str) -> str:
        """Validate audio_format is a supported value."""
        if v not in VALID_AUDIO_FORMATS:
            raise ValueError(
                f"audio_format must be one of {VALID_AUDIO_FORMATS}, got '{v}'"
            )
        return v

    @field_validator("fallback_format")
    @classmethod
    def validate_fallback_format(cls, v: str) -> str:
        """Validate fallback_format is a supported value."""
        allowed = {"mp3", "m4a", "opus"}
        if v not in allowed:
            raise ValueError(
                f"fallback_format must be one of {allowed}, got '{v}'"
            )
        return v

    @field_validator("organize_by")
    @classmethod
    def validate_organize_by(cls, v: str) -> str:
        """Validate organize_by is a supported scheme."""
        if v not in VALID_ORGANIZE_BY:
            raise ValueError(
                f"organize_by must be one of {VALID_ORGANIZE_BY}, got '{v}'"
            )
        return v

    def save(self, path: Path | None = None) -> None:
        """Save configuration to JSON file.

        Note: client_id and client_secret are saved to the file.
        For better security, consider using YMD_CLIENT_ID and
        YMD_CLIENT_SECRET environment variables instead.
        """
        target = path or CONFIG_FILE
        data = self.model_dump(mode="json")
        # Convert Path to string for JSON serialization
        data["download_dir"] = str(data["download_dir"])
        target.write_text(json.dumps(data, indent=2) + "\n")

    @classmethod
    def load(cls, path: Path | None = None) -> "AppConfig":
        """Load configuration from JSON file, with env var overrides.

        Environment variables take precedence over config file values:
        - YMD_CLIENT_ID overrides client_id
        - YMD_CLIENT_SECRET overrides client_secret

        Returns:
            Loaded AppConfig instance.

        Raises:
            ConfigError: If config file contains invalid values.
        """
        target = path or CONFIG_FILE
        data: dict[str, Any] = {}
        if target.exists():
            try:
                data = json.loads(target.read_text())
            except json.JSONDecodeError as e:
                raise ConfigError(
                    f"Invalid JSON in {target}: {e}"
                ) from e

        # Environment variables override config file for secrets
        env_client_id = os.environ.get("YMD_CLIENT_ID")
        env_client_secret = os.environ.get("YMD_CLIENT_SECRET")
        if env_client_id:
            data["client_id"] = env_client_id
        if env_client_secret:
            data["client_secret"] = env_client_secret

        try:
            return cls(**data)
        except Exception as e:
            raise ConfigError(f"Invalid configuration: {e}") from e


def load_config(path: Path | None = None) -> AppConfig:
    """Load application config. Creates default if missing."""
    return AppConfig.load(path)


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Save application config to file."""
    config.save(path)
