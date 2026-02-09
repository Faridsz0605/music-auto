<required_reading>
- references/pipeline.md
- references/architecture.md
- src/cli/commands/sync.py (orchestrator)
</required_reading>

<process>

1. **Identify the failing stage** in the pipeline:
   - **Download** (`src/core/download.py`): yt-dlp errors, format issues, 403 errors
   - **Tagging** (`src/core/tagger.py`): Mutagen errors, unsupported formats, missing metadata
   - **Organization** (`src/core/organizer.py`): Path errors, filename issues, permission errors
   - **Sync state** (`src/core/sync_state.py`): Corrupt JSON, missing entries, duplicate tracking
   - **Auth** (`src/core/auth.py`): OAuth expired, missing credentials, invalid client_id/secret

2. **Reproduce the issue** with a minimal test case:
   ```python
   def test_reproduce_bug() -> None:
       """Minimal reproduction of the reported issue."""
       # Setup
       # Action
       # Assert expected behavior (currently failing)
   ```

3. **Trace the error** through the pipeline:
   - Check exception type (should be from `src/core/exceptions.py`)
   - Check if error is caught and re-raised correctly
   - Check if logging provides sufficient context

4. **Fix and verify**:
   - Make the minimal change to fix the issue
   - Ensure the reproduction test now passes
   - Run full test suite to check for regressions

5. **Update documentation** if the fix changes behavior.

</process>

<common_issues>
| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| 403 on download | yt-dlp outdated | `pip install -U yt-dlp` |
| OAuth fails | Missing client_id/client_secret | Check config.json has valid credentials |
| Tags not applied | Wrong file extension mapping | Check `tag_file()` dispatcher in tagger.py |
| Files in wrong directory | organize_by mismatch | Check config organize_by value |
| Sync re-downloads all | Corrupt .sync_state.json | Delete and re-sync |
</common_issues>

<success_criteria>
- Root cause identified and documented
- Reproduction test exists
- Fix is minimal and targeted
- Full test suite passes
- No regressions introduced
</success_criteria>
