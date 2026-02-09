<required_reading>
- references/architecture.md
- references/pipeline.md
- src/providers/youtube.py (reference implementation)
</required_reading>

<process>

1. **Create the provider file** at `src/providers/{provider_name}.py`:
   - Define a `{Provider}Provider` class following the `YouTubeProvider` pattern
   - Implement methods: `get_playlists()`, `get_playlist_tracks()`, `search()`, `normalize_track()`
   - Use `@staticmethod` for `normalize_track`
   - Raise appropriate exceptions from `src.core.exceptions`
   - All methods must have full type hints

2. **Create tests** at `tests/test_provider_{name}.py`:
   - Mock all external API calls
   - Test each public method
   - Test error handling paths
   - Test `normalize_track` with various input shapes

3. **Update documentation**:
   - Add provider to AGENTS.md architecture tree
   - Update the Design Principles section if extensibility pattern changes

4. **Verify**:
   ```bash
   ruff check .
   ruff format .
   mypy .
   pytest
   ```

</process>

<success_criteria>
- Provider class follows YouTubeProvider pattern
- All methods have type hints
- Tests cover success and error paths
- normalize_track handles missing/malformed data gracefully
- All verification commands pass
</success_criteria>
