# ymd

YouTube Music Downloader -- sync playlists and download tracks for offline playback on a DAP.

## Features

- Sync YouTube Music playlists with interactive selection
- Download tracks in best available audio quality via yt-dlp
- Automatic metadata tagging (artist, title, album, cover art) with Mutagen
- File organization by Genre/Artist/Track, with configurable patterns
- Incremental sync -- only downloads new tracks on subsequent runs
- Search and download individual tracks by name
- DAP-friendly: 120-character filename limit, MP3/FLAC fallback support
- Pacman-inspired terminal UI with Rich

## Quick Start

### 1. Install Python 3.12

If using [mise](https://mise.jdx.dev/):

```bash
mise install    # reads mise.toml, installs Python 3.12
```

### 2. Set Up Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Authenticate

```bash
ymd auth
```

Follow the OAuth prompts to link your YouTube Music account.

### 4. Sync

```bash
ymd sync
```

Select playlists interactively, then ymd downloads, tags, and organizes the tracks.

## Commands

| Command    | Description                              | Example                       |
|------------|------------------------------------------|-------------------------------|
| `auth`     | OAuth authentication with YouTube Music  | `ymd auth`                    |
| `sync`     | Sync playlists (incremental)             | `ymd sync`                    |
| `search`   | Search and download individual tracks    | `ymd search "Bohemian Rhapsody"` |
| `status`   | Show sync state and statistics           | `ymd status`                  |
| `clean`    | Remove orphaned files not in any playlist| `ymd clean`                   |
| `config`   | View and manage settings                 | `ymd config`                  |

Run `ymd --help` or `ymd <command> --help` for full usage details.

## Configuration

Settings are stored in `config.json`. Copy the template to get started:

```bash
cp config.example.json config.json
```

```json
{
  "download_dir": "downloads",
  "audio_format": "best",
  "fallback_format": "mp3",
  "organize_by": "genre_artist",
  "max_filename_length": 120,
  "max_concurrent_downloads": 3,
  "default_genre": "Unknown"
}
```

| Key                        | Description                                                |
|----------------------------|------------------------------------------------------------|
| `download_dir`             | Base directory for downloaded files                        |
| `audio_format`             | Preferred format: `best`, `mp3`, `m4a`, `opus`             |
| `fallback_format`          | Format to use when `best` is not DAP-compatible            |
| `organize_by`              | File structure: `genre_artist`, `artist_album`, `playlist` |
| `max_filename_length`      | Truncate filenames to this length (DAP compatibility)      |
| `max_concurrent_downloads` | Number of parallel downloads                               |
| `default_genre`            | Genre tag when YouTube Music does not provide one          |

## File Organization

With the default `genre_artist` organization:

```
downloads/
  Rock/
    Queen/
      Bohemian Rhapsody.mp3
      Don't Stop Me Now.mp3
  Electronic/
    Daft Punk/
      Get Lucky.mp3
  Unknown/
    Some Artist/
      Untitled Track.mp3
```

Filenames are sanitized (special characters removed) and capped at 120 characters to avoid issues with DAP file systems.

## Notes

- YouTube Music does not provide lossless audio. Downloads are limited to the best available lossy format (typically AAC 256kbps or Opus). FLAC transcoding is available but does not improve actual quality.
- Sync state is tracked in `.sync_state.json`. Delete this file to force a full re-download.
- This is a personal tool. Respect YouTube's terms of service and copyright law.
