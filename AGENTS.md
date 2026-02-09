# AGENTS.md

> **Purpose:** This document is the source of truth for all AI agents (and human developers) working on this repository. It defines operational protocols, code style, and architectural standards to ensure consistency and quality.

---

## 1. Project Context & Architecture

**Name:** ymd (YouTube Music Downloader)
**Goal:** A personal CLI tool to sync YouTube Music playlists and download tracks in the best available quality, organized for playback on a DAP (Digital Audio Player).
**Stack:** Python 3.12, Typer (CLI), ytmusicapi (YouTube Music API, OAuth with custom credentials), yt-dlp (download engine), Mutagen (metadata tagging), Pydantic (config validation), questionary (interactive selection), Rich (UI formatting).

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
│   ├── auth.py               # OAuth via ytmusicapi with OAuthCredentials
│   ├── config.py             # Pydantic AppConfig model (includes client_id, client_secret)
│   ├── download.py           # yt-dlp engine + parallel downloads
│   ├── exceptions.py         # Custom exception hierarchy (base: YMDError)
│   ├── organizer.py          # File organization + name sanitization
│   ├── sync_state.py         # Incremental sync state (.sync_state.json)
│   └── tagger.py             # Mutagen metadata tagging
└── providers/
    ├── __init__.py
    └── youtube.py            # YouTubeProvider (ytmusicapi wrapper)
tests/
├── __init__.py
├── conftest.py
├── test_auth.py
├── test_cli_auth.py
├── test_cli_clean.py
├── test_cli_config.py
├── test_cli_search.py
├── test_cli_status.py
├── test_cli_sync.py
├── test_config.py
├── test_download.py
├── test_integration.py
├── test_organizer.py
├── test_provider.py
├── test_sync_state.py
├── test_tagger.py
└── test_ui.py
.claude/
├── agents/
│   ├── code-reviewer.md      # Reviews code against AGENTS.md standards
│   ├── test-runner.md         # Executes tests and analyzes results
│   ├── lint-checker.md        # Runs ruff + mypy checks
│   ├── security-auditor.md    # Audits for security vulnerabilities
│   └── integration-tester.md  # Validates full pipeline flow
└── skills/
    └── ymd-development/
        ├── SKILL.md           # Main skill (architecture, conventions)
        ├── workflows/         # add-command, add-provider, add-test, debug-pipeline
        ├── references/        # architecture, conventions, pipeline
        └── templates/         # command-template, test-template
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
- **OAuth auth:** Requires custom Google Cloud OAuth credentials (Client ID + Client Secret) stored in `config.json`. Credentials stored in `oauth.json` (gitignored). Uses `ytmusicapi`'s OAuth flow with `OAuthCredentials`.
- **Configuration:** `config.json` validated by Pydantic `AppConfig` model. Template in `config.example.json`.
- **YouTubeProvider** in `src/providers/youtube.py` is the main API interface.

---

## 2. Development Environment & Commands

### Prerequisites
- [mise-en-place](https://mise.jdx.dev/) for Python version management.
- Python 3.12 is pinned in `mise.toml`.
- Google Cloud project with YouTube Data API v3 enabled and OAuth Client ID (type: "TVs and Limited Input devices").

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
pip install -r requirements-dev.txt

# Configure OAuth credentials
ymd config --set client_id=YOUR_CLIENT_ID client_secret=YOUR_CLIENT_SECRET

# Authenticate
ymd auth
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
pytest                                    # All tests (176 tests)
pytest tests/test_download.py             # Specific file
pytest tests/test_tagger.py::test_tag_mp3 # Specific function
pytest tests/test_integration.py          # Integration tests
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
python -m src.cli.main config --show

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
from ytmusicapi import OAuthCredentials, YTMusic

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
- **CLI tests** use `typer.testing.CliRunner`: `test_cli_auth.py`, `test_cli_sync.py`, `test_cli_search.py`, `test_cli_status.py`, `test_cli_clean.py`, `test_cli_config.py`.
- **UI tests** in `test_ui.py` mock the Rich console.
- **Integration tests** in `test_integration.py` validate data flow between pipeline stages.

### Test Structure
- Unit tests: one file per source module
- CLI tests: one file per CLI command (using CliRunner)
- Integration tests: validate interfaces between modules
- All test functions have return type `-> None`
- Use `MagicMock` (not `Console`) as type hint for `@patch` decorated parameters

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
- Uses `ytmusicapi` OAuth flow with **custom credentials** (required since v1.10.0).
- Requires `client_id` and `client_secret` from Google Cloud Console (YouTube Data API v3, OAuth type "TVs and Limited Input devices").
- Credentials config stored in `config.json` (gitignored). OAuth tokens stored in `oauth.json` (gitignored).
- Run `ymd config --set client_id=ID client_secret=SECRET` then `ymd auth` to authenticate.
- The `_get_oauth_credentials()` helper in `src/core/auth.py` loads credentials from config and returns `OAuthCredentials`.
- `load_auth()` passes `OAuthCredentials` when constructing `YTMusic` instances.

### Downloads
- Use `yt-dlp` with best available audio: `bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio`.
- Parallel downloads controlled by `max_concurrent_downloads` config (default: 3).
- Pipeline: download -> tag with Mutagen (artist, title, album, cover art) -> organize to final path.

### File Organization
- Default organization: `downloads/{Genre}/{Artist}/{Track}.{ext}`.
- Filenames sanitized and capped at 120 characters for DAP compatibility.
- `organize_by` config supports: `genre_artist`, `artist_album`, `playlist`.
- Handled by `src/core/organizer.py`.

### Sync State
- `.sync_state.json` in the download directory tracks downloaded songs per playlist.
- Enables incremental sync: only new/unsynced tracks are downloaded on subsequent runs.
- Managed by `src/core/sync_state.py`.

### Configuration
- Settings stored in `config.json` (gitignored).
- Template provided: `config.example.json`.
- Validated at load time by Pydantic `AppConfig` model in `src/core/config.py`.
- Config keys: `download_dir`, `audio_format`, `fallback_format`, `organize_by`, `max_filename_length`, `max_concurrent_downloads`, `default_genre`, `client_id`, `client_secret`.

### Interactive UI
- Playlist selection uses `questionary` checkboxes for multi-select.
- Progress and status output uses Rich with a pacman-inspired theme (see `src/cli/ui.py`).

---

## 6. Agent Behavior Protocols

### Before Making Changes
1. **Read Context:** Always read `AGENTS.md` and related source files before editing.
2. **Understand Architecture:** Check `src/` structure before adding new files. Respect the existing module boundaries.
3. **Check Tests:** Run existing tests to understand expected behavior before modifying code.
4. **Load Skill:** Use the `ymd-development` skill (`.claude/skills/ymd-development/SKILL.md`) for domain-specific guidance.

### During Development
1. **Small Steps:** Verify after every significant change (lint -> format -> type check -> test).
2. **No Placeholders:** Write complete, working code. No `pass` or `# TODO` in commits.
3. **Ask First:** If adding a new dependency, ask the user. If a plan has risk (file deletion, API changes), confirm first.
4. **Use Sub-agents:** After writing code, use `code-reviewer` agent. After running tests, use `test-runner` agent. Before committing, use `lint-checker` agent.
5. **Update AGENTS.md:** After any structural change (new files, new config fields, new commands), update this document.

### Sub-agents Available
| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `code-reviewer` | Reviews code against AGENTS.md standards | After writing/modifying code |
| `test-runner` | Runs tests and analyzes failures | After code changes |
| `lint-checker` | Runs ruff + mypy checks | Before committing |
| `security-auditor` | Checks for credential exposure, injection | When modifying auth/config/download |
| `integration-tester` | Validates pipeline data flow | After modifying pipeline components |

### Communication
- **DO:** Use the chat to ask questions, explain decisions, and seek clarification.
- **DO NOT:** Create markdown files (like `PLAN.md`, `NOTES.md`) to communicate with the user.

---

## 7. Dependencies

### Runtime
- `typer[all]>=0.12.3` - CLI framework with Rich integration
- `ytmusicapi>=1.10.0` - YouTube Music unofficial API (OAuth with custom credentials)
- `yt-dlp>=2024.3.10` - Audio/video downloader
- `mutagen>=1.47.0` - Audio metadata tagging
- `pydantic>=2.9.0` - Configuration validation
- `questionary>=2.0.0` - Interactive terminal prompts

### Development
- `pytest>=8.0.0` - Testing framework
- `pytest-mock>=3.12.0` - Mocking utilities
- `ruff>=0.9.0` - Linter and formatter
- `mypy>=1.8.0` - Static type checker (strict mode)
- `pydantic.mypy` - mypy plugin for Pydantic

---

## 8. Common Pitfalls & Solutions

| Issue | Solution |
|-------|----------|
| OAuth authentication fails | Ensure `client_id` and `client_secret` are set in config.json. Re-run `ymd auth`. |
| "OAuth client_id and client_secret are required" | Run `ymd config --set client_id=YOUR_ID client_secret=YOUR_SECRET` |
| Downloads fail with 403 | Update yt-dlp: `pip install -U yt-dlp` |
| Type errors in tests | Use `MagicMock` as type hint for `@patch` parameters. Check `mypy --strict`. |
| Import errors | Ensure `PYTHONPATH=.` is set (mise.toml handles this) or run as module: `python -m src.cli.main` |
| Filenames too long for DAP | `max_filename_length` in config controls truncation (default: 120) |
| Sync re-downloads everything | Check `.sync_state.json` exists and is not corrupted |
| questionary prompts hang in CI | questionary requires an interactive terminal; mock in tests |

---

**Last Updated:** 2026-02-07
**Python Version:** 3.12
**Maintained By:** Personal project (Faris)
