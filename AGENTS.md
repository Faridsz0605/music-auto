# AGENTS.md

> **Purpose:** This document is the source of truth for all AI agents (and human developers) working on this repository. It defines operational protocols, code style, and architectural standards to ensure consistency and quality.

---

## 1. Project Context & Architecture

**Name:** ymd (YouTube Music Downloader)
**Goal:** A personal CLI tool to sync YouTube Music playlists and download tracks in the best available quality, organized for playback on a DAP (Digital Audio Player).
**Stack:** Python 3.12, Typer (CLI), ytmusicapi (YouTube Music API, OAuth), yt-dlp (download engine), Mutagen (metadata tagging), Pydantic (config validation), questionary (interactive selection), Rich (UI formatting).

### Architecture
```
src/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py              # Typer app, registers all commands
│   ├── ui.py                # Rich UI components (pacman-inspired)
│   └── commands/
│       ├── __init__.py
│       ├── auth.py           # OAuth authentication
│       ├── sync.py           # Main sync command
│       ├── search.py         # Search + download
│       ├── status.py         # Sync status display
│       ├── clean.py          # Orphan cleanup
│       └── config_cmd.py     # Config management
├── core/
│   ├── __init__.py
│   ├── auth.py               # OAuth via ytmusicapi
│   ├── config.py             # Pydantic AppConfig model
│   ├── download.py           # yt-dlp engine + parallel downloads
│   ├── exceptions.py         # Custom exception hierarchy (base: YMDError)
│   ├── organizer.py          # File organization + name sanitization
│   ├── playlist.py           # Legacy (kept for reference)
│   ├── sync_state.py         # Incremental sync state (.sync_state.json)
│   └── tagger.py             # Mutagen metadata tagging
└── providers/
    ├── __init__.py
    └── youtube.py            # YouTubeProvider (ytmusicapi wrapper)
tests/
├── __init__.py
├── conftest.py
├── test_auth.py
├── test_config.py
├── test_download.py
├── test_organizer.py
├── test_provider.py
├── test_sync_state.py
└── test_tagger.py
```

### Design Principles
- **Simplicity:** Personal use. No over-engineering.
- **Modularity:** Provider pattern for future extensibility (e.g., Soulseek, Deezer).
- **User-Centric:** Interactive flows with clear feedback via Rich and questionary.
- **DAP-First:** File organization, naming, and format choices target DAP compatibility (120 char filename limit, Genre/Artist/Track structure, MP3/FLAC fallback).

### CLI Commands
| Command  | Description                                      |
|----------|--------------------------------------------------|
| `auth`   | Interactive OAuth authentication with YouTube Music |
| `sync`   | Sync playlists (incremental, with interactive selection) |
| `search` | Search YouTube Music and download individual tracks |
| `status` | Display current sync state and statistics         |
| `clean`  | Remove orphaned files not in any synced playlist  |
| `config` | View and manage configuration settings            |

### Key Concepts
- **Download pipeline:** yt-dlp download -> Mutagen tagging -> organizer (move to Genre/Artist/Track).
- **Incremental sync:** `.sync_state.json` tracks which songs have been downloaded per playlist. Only new tracks are processed on subsequent runs.
- **OAuth auth:** Credentials stored in `oauth.json` (gitignored). Uses `ytmusicapi`'s OAuth flow.
- **Configuration:** `config.json` validated by Pydantic `AppConfig` model. Template in `config.example.json`.
- **YouTubeProvider** in `src/providers/youtube.py` is the main API interface. `src/core/playlist.py` is legacy code kept for reference only.

---

## 2. Development Environment & Commands

### Prerequisites
- [mise-en-place](https://mise.jdx.dev/) for Python version management.
- Python 3.12 is pinned in `mise.toml`.

### Initial Setup
```bash
# mise installs Python 3.12 automatically from mise.toml
mise install

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install project and dependencies
pip install -e ".[dev]"
# Or from requirements if available:
pip install -r requirements.txt
```

### Verification Commands (Run before EVERY commit)
```bash
ruff check .              # Linting
ruff format .             # Auto-formatting
mypy .                    # Type checking (strict mode)
pytest                    # Full test suite
```

### Running Tests
```bash
pytest                                    # All tests
pytest tests/test_download.py             # Specific file
pytest tests/test_tagger.py::test_tag_mp3 # Specific function
pytest -s                                 # With stdout output
pytest -v                                 # Verbose mode
```

### CLI Usage (Development)
```bash
# Via module
python -m src.cli.main --help
python -m src.cli.main auth
python -m src.cli.main sync
python -m src.cli.main search "artist name - song title"
python -m src.cli.main status
python -m src.cli.main clean
python -m src.cli.main config

# Via entry point (after pip install -e .)
ymd --help
ymd sync
```

---

## 3. Code Style & Conventions

### Formatting & Syntax
- **Formatter:** `ruff format` (Black-compatible).
- **Line Length:** 88 characters maximum.
- **Target:** Python 3.12 (`target-version = "py312"` in pyproject.toml).
- **Quotes:** Double quotes `"` for strings.
- **Imports:** Sorted by `ruff`. Order: Stdlib -> Third-party -> Local.

### Typing (Strict)
- **ALL** function signatures MUST have type hints.
- Use built-in generics: `list[str]`, `dict[str, Any]` (Python 3.12 style).
- Use `X | None` instead of `Optional[X]`.
- Use `pathlib.Path` for file system paths, not `str`.
- mypy runs in strict mode with `disallow_untyped_defs = true`.

### Naming Conventions
- **Variables/Functions:** `snake_case` (e.g., `fetch_playlist`, `song_title`)
- **Classes:** `PascalCase` (e.g., `AppConfig`, `YouTubeProvider`)
- **Constants:** `UPPER_CASE` (e.g., `DEFAULT_TIMEOUT = 30`)
- **Files/Modules:** `snake_case` (e.g., `sync_state.py`, `config_cmd.py`)

### Error Handling
- All custom exceptions inherit from `YMDError` (defined in `src/core/exceptions.py`).
- Exception hierarchy: `YMDError` -> `AuthenticationError`, `DownloadError`, `MetadataError`, `ConfigError`, `SyncError`, `OrganizationError`, `PlaylistNotFoundError`.
- Keep `try` blocks minimal. Catch **specific** exceptions, never bare `except:`.
- CLI commands return `0` for success, non-zero for failure.
- Log errors with context: `logger.error(f"Failed to download {song_id}: {e}")`.

### File System Operations
- **ALWAYS** use `pathlib.Path` instead of `os.path` strings.
- Validate paths exist before reading: `if path.exists(): ...`
- Use `Path.read_text()` / `Path.write_text()` for simple file I/O.

### Imports Order Example
```python
# Standard library
import json
from pathlib import Path

# Third-party
import typer
from ytmusicapi import YTMusic

# Local
from src.core.config import load_config
from src.core.exceptions import DownloadError
from src.providers.youtube import YouTubeProvider
```

---

## 4. Testing Guidelines

### Principles
- **Coverage:** Critical paths (auth, download, tagging, sync state, organizer) require high coverage.
- **Mocking:** Network calls MUST be mocked in unit tests. Use `unittest.mock` or `pytest-mock`.
- **Fixtures:** Use `@pytest.fixture` in `conftest.py` for shared setup/teardown.
- **Test files** mirror `src/` modules: `test_auth.py`, `test_config.py`, `test_download.py`, `test_organizer.py`, `test_provider.py`, `test_sync_state.py`, `test_tagger.py`.

### Example Test Structure
```python
def test_playlist_fetch(mock_ytmusic: MagicMock) -> None:
    """Test fetching liked songs from YouTube Music."""
    mock_ytmusic.get_liked_songs.return_value = {
        "tracks": [
            {"title": "Test Song", "artists": [{"name": "Artist"}]}
        ]
    }
    provider = YouTubeProvider(mock_ytmusic)
    result = provider.get_liked_songs()
    assert len(result) == 1
    assert result[0]["title"] == "Test Song"
```

---

## 5. Project-Specific Rules

### Authentication
- Uses `ytmusicapi` OAuth flow (not cookie/header-based).
- Credentials stored in `oauth.json` (gitignored).
- Run `ymd auth` to authenticate interactively.
- Validate credentials on startup and provide clear error messages if expired or missing.

### Downloads
- Use `yt-dlp` with best available audio: `bestaudio[ext=m4a]/bestaudio`.
- Parallel downloads controlled by `max_concurrent_downloads` config (default: 3).
- Pipeline: download -> tag with Mutagen (artist, title, album, cover art) -> organize to final path.

### File Organization
- Default organization: `downloads/{Genre}/{Artist}/{Track}.{ext}`.
- Filenames sanitized and capped at 120 characters for DAP compatibility.
- `organize_by` config supports: `genre_artist`, `artist_album`, `playlist`.
- Handled by `src/core/organizer.py`.

### Sync State
- `.sync_state.json` in the project root tracks downloaded songs per playlist.
- Enables incremental sync: only new/unsynced tracks are downloaded on subsequent runs.
- Managed by `src/core/sync_state.py`.

### Configuration
- Settings stored in `config.json` (gitignored).
- Template provided: `config.example.json`.
- Validated at load time by Pydantic `AppConfig` model in `src/core/config.py`.
- Config keys: `download_dir`, `audio_format`, `fallback_format`, `organize_by`, `max_filename_length`, `max_concurrent_downloads`, `default_genre`.

### Interactive UI
- Playlist selection uses `questionary` checkboxes for multi-select.
- Progress and status output uses Rich with a pacman-inspired theme (see `src/cli/ui.py`).

---

## 6. Agent Behavior Protocols

### Before Making Changes
1. **Read Context:** Always read `AGENTS.md` and related source files before editing.
2. **Understand Architecture:** Check `src/` structure before adding new files. Respect the existing module boundaries.
3. **Check Tests:** Run existing tests to understand expected behavior before modifying code.

### During Development
1. **Small Steps:** Verify after every significant change (lint -> format -> type check -> test).
2. **No Placeholders:** Write complete, working code. No `pass` or `# TODO` in commits.
3. **Ask First:** If adding a new dependency, ask the user. If a plan has risk (file deletion, API changes), confirm first.
4. **Legacy Awareness:** `src/core/playlist.py` is legacy code. Main playlist/API logic lives in `src/providers/youtube.py`.

### Communication
- **DO:** Use the chat to ask questions, explain decisions, and seek clarification.
- **DO NOT:** Create markdown files (like `PLAN.md`, `NOTES.md`) to communicate with the user.

---

## 7. Dependencies

### Runtime
- `typer[all]>=0.12.3` - CLI framework with Rich integration
- `ytmusicapi>=1.7.0` - YouTube Music unofficial API (OAuth)
- `yt-dlp>=2024.3.10` - Audio/video downloader
- `mutagen>=1.47.0` - Audio metadata tagging
- `pydantic>=2.9.0` - Configuration validation
- `questionary>=2.0.0` - Interactive terminal prompts

### Development
- `pytest` - Testing framework
- `pytest-mock` - Mocking utilities
- `ruff` - Linter and formatter
- `mypy` - Static type checker (strict mode)
- `pydantic.mypy` - mypy plugin for Pydantic

---

## 8. Common Pitfalls & Solutions

| Issue | Solution |
|-------|----------|
| OAuth authentication fails | Re-run `ymd auth` to re-authenticate. Delete `oauth.json` if corrupt. |
| Downloads fail with 403 | Update yt-dlp: `pip install -U yt-dlp` |
| Type errors in tests | Ensure mock objects have proper type annotations. Check `mypy --strict`. |
| Import errors | Ensure `PYTHONPATH=.` is set (mise.toml handles this) or run as module: `python -m src.cli.main` |
| Filenames too long for DAP | `max_filename_length` in config controls truncation (default: 120) |
| Sync re-downloads everything | Check `.sync_state.json` exists and is not corrupted |
| questionary prompts hang in CI | questionary requires an interactive terminal; mock in tests |
| `src/core/playlist.py` confusion | This is legacy code. Use `src/providers/youtube.py` (`YouTubeProvider`) instead. |

---

**Last Updated:** 2026-02-05
**Python Version:** 3.12
**Maintained By:** Personal project (Faris)
