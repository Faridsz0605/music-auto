---
name: ymd-development
description: Domain expertise for the ymd (YouTube Music Downloader) CLI project. Use when developing, extending, debugging, or testing ymd features. Triggers on any work involving src/, tests/, CLI commands, providers, download pipeline, sync state, or file organization.
---

<objective>
Provide domain-specific guidance for developing and maintaining the ymd CLI tool. This skill encodes the project's architecture, conventions, patterns, and common workflows so agents produce code that integrates correctly with the existing codebase.
</objective>

<essential_principles>

<principle name="agents_md_is_source_of_truth">
ALWAYS read AGENTS.md before making any code changes. It defines the authoritative standards for this project. Any deviation from AGENTS.md must be flagged and discussed with the user.
</principle>

<principle name="strict_typing">
ALL function signatures MUST have type hints. Use Python 3.12 built-in generics (`list[str]`, `dict[str, Any]`). Use `X | None` instead of `Optional[X]`. Use `pathlib.Path` for filesystem paths. mypy runs in strict mode.
</principle>

<principle name="error_hierarchy">
All custom exceptions inherit from `YMDError` in `src/core/exceptions.py`. The hierarchy: `YMDError` -> `AuthenticationError`, `DownloadError`, `MetadataError`, `ConfigError`, `SyncError`, `OrganizationError`, `PlaylistNotFoundError`. Never use bare `except:`. Catch specific exceptions only.
</principle>

<principle name="provider_pattern">
`src/providers/youtube.py` (`YouTubeProvider`) is the ONLY API interface. It wraps `ytmusicapi.YTMusic`. All playlist/track fetching goes through this class.
</principle>

<principle name="download_pipeline">
The pipeline is: yt-dlp download -> Mutagen tagging -> organizer (move to Genre/Artist/Track). Each stage is a separate module: `download.py`, `tagger.py`, `organizer.py`. The sync command in `src/cli/commands/sync.py` orchestrates the full pipeline.
</principle>

<principle name="oauth_with_custom_credentials">
ytmusicapi v1.10.0+ requires custom OAuth Client ID and Client Secret from Google Cloud (YouTube Data API v3, application type "TVs and Limited Input devices"). These are stored in `config.json` as `client_id` and `client_secret`. The `OAuthCredentials` class must be passed when constructing `YTMusic`.
</principle>

<principle name="incremental_sync">
`.sync_state.json` tracks downloaded songs per playlist via `SyncState` class. Only new/unsynced tracks are processed. The state file stores video_id, filepath, metadata, and timestamps.
</principle>

<principle name="dap_compatibility">
File organization targets DAP (Digital Audio Player) compatibility: 120 char filename limit, FAT32-safe characters, Genre/Artist/Track structure. Configured via `organize_by` in config.
</principle>

<principle name="verification_before_commit">
Run these commands before every commit: `ruff check .`, `ruff format .`, `mypy .`, `pytest`. All must pass with zero errors.
</principle>

</essential_principles>

<architecture_map>
```
src/
  cli/           - Typer commands and Rich UI
    main.py      - App entry point, command registration
    ui.py        - Rich theme, tables, progress bars
    commands/    - One file per CLI command
  core/          - Business logic (no CLI dependency)
    auth.py      - OAuth setup/load with OAuthCredentials
    config.py    - Pydantic AppConfig model
    download.py  - yt-dlp engine + parallel downloads
    exceptions.py - YMDError hierarchy
    organizer.py - File organization + sanitization
    sync_state.py - Incremental sync tracking
    tagger.py    - Mutagen metadata tagging
  providers/     - External API wrappers
    youtube.py   - YouTubeProvider (ytmusicapi)
tests/           - Mirrors src/ structure
  conftest.py    - Shared fixtures (mock_ytmusic, sample_tracks, etc.)
```
</architecture_map>

<intake>
What would you like to do?

1. Add a new CLI command
2. Add a new provider
3. Add or update tests
4. Debug a pipeline issue
5. Get architecture guidance

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Workflow |
|----------|----------|
| 1, "command", "new command", "CLI" | workflows/add-command.md |
| 2, "provider", "new provider" | workflows/add-provider.md |
| 3, "test", "tests", "coverage" | workflows/add-test.md |
| 4, "debug", "fix", "pipeline", "error" | workflows/debug-pipeline.md |
| 5, "architecture", "guidance", "how" | Read references/ as needed |

**After reading the workflow, follow it exactly.**
</routing>

<references_index>
**For architecture questions:** references/architecture.md
**For code conventions:** references/conventions.md
**For pipeline understanding:** references/pipeline.md
**For extending CLI:** references/architecture.md + workflows/add-command.md
**For testing patterns:** references/conventions.md + workflows/add-test.md
</references_index>

<success_criteria>
Code produced by agents using this skill:
- Passes `ruff check .` with zero errors
- Passes `ruff format --check .` with zero changes
- Passes `mypy .` with zero errors
- Passes `pytest` with zero failures
- Follows AGENTS.md conventions exactly
- Has type hints on ALL function signatures
- Uses `pathlib.Path` for all filesystem operations
- Uses custom exceptions from `src/core/exceptions.py`
- Has corresponding tests for any new functionality
</success_criteria>
