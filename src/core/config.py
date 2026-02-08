"""Application configuration with Pydantic validation."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

CONFIG_FILE = Path("config.json")
CONFIG_EXAMPLE = Path("config.example.json")


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
        default=120, description="Max filename length for DAP compatibility"
    )
    max_concurrent_downloads: int = Field(
        default=3, description="Max parallel downloads"
    )
    default_genre: str = Field(
        default="Unknown",
        description="Default genre when not available from YTM",
    )

    def save(self, path: Path | None = None) -> None:
        """Save configuration to JSON file."""
        target = path or CONFIG_FILE
        data = self.model_dump(mode="json")
        # Convert Path to string for JSON serialization
        data["download_dir"] = str(data["download_dir"])
        target.write_text(json.dumps(data, indent=2) + "\n")

    @classmethod
    def load(cls, path: Path | None = None) -> "AppConfig":
        """Load configuration from JSON file, or create default."""
        target = path or CONFIG_FILE
        if target.exists():
            data: dict[str, Any] = json.loads(target.read_text())
            return cls(**data)
        return cls()


def load_config(path: Path | None = None) -> AppConfig:
    """Load application config. Creates default if missing."""
    return AppConfig.load(path)


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Save application config to file."""
    config.save(path)
