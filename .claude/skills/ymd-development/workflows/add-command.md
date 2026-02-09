<required_reading>
- references/architecture.md
- references/conventions.md
- AGENTS.md (sections 1, 3, 4)
</required_reading>

<process>

1. **Create the command file** at `src/cli/commands/{command_name}.py`:
   - Import `typer` and relevant UI functions from `src.cli.ui`
   - Import business logic from `src.core.*` and `src.providers.*`
   - Define the command function with full type hints
   - Use Typer options/arguments with help text
   - Handle exceptions from `src.core.exceptions` with user-friendly messages
   - Call `raise typer.Exit(code=1)` on failure

2. **Register the command** in `src/cli/main.py`:
   - Import the command function
   - Add `app.command(name="{command_name}")(command_function)`

3. **Create tests** at `tests/test_cli_{command_name}.py`:
   - Use `typer.testing.CliRunner` to invoke the command
   - Mock all network calls and external dependencies
   - Test success path, error paths, and edge cases
   - Verify exit codes (0 for success, 1 for failure)

4. **Update AGENTS.md**:
   - Add the command to the CLI Commands table
   - Update the Architecture tree if new files were added

5. **Verify**:
   ```bash
   ruff check .
   ruff format .
   mypy .
   pytest
   ```

</process>

<template>
```python
"""CLI command: {command_name}."""

import logging
from pathlib import Path

import typer

from src.cli.ui import print_error, print_header, print_success
from src.core.config import load_config

logger = logging.getLogger(__name__)


def {command_name}_command(
    # Add Typer options here
) -> None:
    """{Description of what this command does}."""
    try:
        config = load_config()
        print_header("{Command Name}")
        # Implementation here
        print_success("Done.")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(code=1) from e
```
</template>

<success_criteria>
- Command file exists at `src/cli/commands/{name}.py`
- Command registered in `src/cli/main.py`
- Test file exists at `tests/test_cli_{name}.py`
- All verification commands pass
- AGENTS.md updated
</success_criteria>
