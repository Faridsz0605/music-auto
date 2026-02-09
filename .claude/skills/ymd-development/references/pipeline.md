<pipeline>

## Download Pipeline

The ymd download pipeline processes tracks through three sequential stages:

### Stage 1: Download (src/core/download.py)

**Input:** video_id, output_dir, audio_format, fallback_format
**Output:** Path to downloaded audio file (or None on failure)

- Uses yt-dlp with format: `bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio`
- If fallback_format is "mp3", adds FFmpegExtractAudio postprocessor (320kbps)
- Also includes FFmpegMetadata and EmbedThumbnail postprocessors
- Output template: `{output_dir}/{video_id}.{ext}`
- Parallel downloads via ThreadPoolExecutor (max_workers from config)

**Error handling:** Raises `DownloadError` on failure. Common causes:
- 403 Forbidden (yt-dlp outdated)
- No info extracted (invalid video_id)
- File not found after download (postprocessor failure)

### Stage 2: Tagging (src/core/tagger.py)

**Input:** filepath, metadata dict (title, artist, album, genre), optional cover_path
**Output:** Tagged file in-place

- Dispatches based on file extension:
  - `.mp3` -> EasyID3 tags + APIC cover art
  - `.m4a/.mp4/.aac` -> MP4 atoms + MP4Cover
  - `.ogg/.opus/.webm` -> Generic Mutagen tags (no cover support for some)
- Metadata keys: title, artist, album, genre

**Error handling:** Raises `MetadataError`. Wraps all Mutagen exceptions.

### Stage 3: Organization (src/core/organizer.py)

**Input:** source_path, base_dir, metadata, organize_by, max_filename_length, default_genre
**Output:** Final path after moving

- Sanitizes filename and directory names (FAT32/NTFS safe)
- Truncates to max_filename_length (default 120)
- Organization schemes:
  - `genre_artist`: `{base}/{Genre}/{Artist}/{Artist - Title}.{ext}`
  - `artist_album`: `{base}/{Artist}/{Album}/{Artist - Title}.{ext}`
  - `playlist`: `{base}/{Playlist}/{Artist - Title}.{ext}`
- Handles duplicates with `(1)`, `(2)` counter suffix
- Moves file using `shutil.move`

**Error handling:** Raises `OrganizationError`. Common causes:
- Source file not found
- Permission errors on destination
- Path too long for filesystem

### Sync State Integration (src/core/sync_state.py)

After successful pipeline completion:
1. `SyncState.mark_downloaded(video_id, filepath, metadata)` records the track
2. `SyncState.mark_playlist_synced(playlist_id, name, count)` records playlist
3. `SyncState.save()` persists to `.sync_state.json`

On subsequent runs:
1. `SyncState.get_new_tracks(tracks)` filters out already-downloaded tracks
2. Only new tracks enter the pipeline

</pipeline>
