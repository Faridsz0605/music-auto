<conventions>

## Code Style (from AGENTS.md)

- **Formatter:** ruff format (Black-compatible), 88 char line length
- **Target:** Python 3.12 (py312)
- **Quotes:** Double quotes for strings
- **Imports:** Sorted by ruff. Order: Stdlib -> Third-party -> Local

## Typing Rules

- ALL function signatures MUST have type hints
- Built-in generics: `list[str]`, `dict[str, Any]` (not `List`, `Dict`)
- Union syntax: `X | None` (not `Optional[X]`)
- Paths: `pathlib.Path` (never `str` for paths)
- mypy strict mode: `disallow_untyped_defs = true`

## Naming

- Variables/Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Files/Modules: `snake_case`

## Error Handling

- All exceptions inherit from `YMDError`
- Minimal `try` blocks
- Catch specific exceptions only
- Log with context: `logger.error(f"Failed to download {song_id}: {e}")`
- CLI commands: exit 0 for success, non-zero for failure

## Filesystem

- ALWAYS use `pathlib.Path`
- Validate existence before reading
- Use `Path.read_text()` / `Path.write_text()`

## Testing

- pytest with class-based organization
- Mock all network calls
- Fixtures in conftest.py
- Test files mirror src/ modules
- Type hints on test functions: `def test_foo(self) -> None:`

## Import Order Example

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

</conventions>
