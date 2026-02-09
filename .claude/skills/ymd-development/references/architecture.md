<architecture>

## Module Responsibilities

### src/cli/ - Command Layer
- **main.py**: Typer app instance, registers all commands. Entry point: `ymd = src.cli.main:main`.
- **ui.py**: Rich theme (pacman-inspired), console instance, helper functions for formatted output (print_header, print_success, print_error, print_warning, print_info), table renderers (print_track_table, print_playlist_table), progress bar factory (create_download_progress), sync summary.
- **commands/**: One file per CLI command. Each command function receives Typer-parsed arguments, loads config/auth, calls business logic, and handles errors with user-friendly messages.

### src/core/ - Business Logic
- **auth.py**: `setup_auth()` runs interactive OAuth flow with custom OAuthCredentials. `load_auth()` loads saved credentials and returns authenticated YTMusic instance. Uses `client_id` and `client_secret` from config.json.
- **config.py**: Pydantic `AppConfig` model with fields: download_dir, audio_format, fallback_format, organize_by, max_filename_length, max_concurrent_downloads, default_genre, client_id, client_secret. `load_config()` and `save_config()` handle file I/O.
- **download.py**: `download_track()` uses yt-dlp to download a single track. `download_tracks_parallel()` uses ThreadPoolExecutor. `_build_yt_dlp_opts()` constructs yt-dlp options dict.
- **exceptions.py**: Exception hierarchy rooted at `YMDError`.
- **organizer.py**: `sanitize_filename()` and `sanitize_dirname()` for FAT32/NTFS safety. `organize_track()` moves files to organized directory structure. `cleanup_temp_dir()` removes temp files.
- **sync_state.py**: `SyncState` class manages `.sync_state.json`. Tracks downloads per video_id, playlist sync metadata, orphan detection.
- **tagger.py**: `tag_file()` dispatches to format-specific taggers (_tag_mp3, _tag_m4a, _tag_generic). Handles cover art embedding.

### src/providers/ - External APIs
- **youtube.py**: `YouTubeProvider` wraps `ytmusicapi.YTMusic`. Methods: `get_playlists()`, `get_liked_songs()`, `get_playlist_tracks()`, `search()`. Static method: `normalize_track()` converts raw API data to standard dict.

### tests/ - Test Suite
- Mirrors src/ structure: test_auth.py, test_config.py, test_download.py, test_organizer.py, test_provider.py, test_sync_state.py, test_tagger.py.
- CLI command tests: test_cli_auth.py, test_cli_sync.py, test_cli_search.py, test_cli_status.py, test_cli_clean.py, test_cli_config.py.
- conftest.py provides shared fixtures.

## Data Flow

```
User runs `ymd sync`
  -> auth.load_auth() -> YTMusic client
  -> YouTubeProvider.get_playlists() -> playlist list
  -> User selects playlists (questionary)
  -> For each playlist:
     -> YouTubeProvider.get_playlist_tracks() -> raw tracks
     -> YouTubeProvider.normalize_track() -> normalized tracks
     -> SyncState.get_new_tracks() -> filter already-downloaded
     -> For each new track:
        -> download.download_track() -> temp file
        -> tagger.tag_file() -> tagged file
        -> organizer.organize_track() -> final path
        -> SyncState.mark_downloaded()
     -> SyncState.mark_playlist_synced()
  -> SyncState.save()
```

</architecture>
