<template name="cli-command">

## File: src/cli/commands/{name}.py

```python
"""{Description} command."""

import logging
from pathlib import Path

import typer

from src.cli.ui import print_error, print_header, print_info, print_success, print_warning
from src.core.config import load_config
from src.core.exceptions import YMDError

logger = logging.getLogger(__name__)


def {name}_command(
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Override download directory"
    ),
) -> None:
    """{Description of the command}."""
    try:
        config = load_config()
        base_dir = output_dir or config.download_dir
        print_header("{Command Title}")

        # Implementation here

        print_success("Operation completed successfully.")

    except YMDError as e:
        print_error(str(e))
        logger.error(f"{name} failed: {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.exception(f"Unexpected error in {name}")
        raise typer.Exit(code=1) from e
```

## Registration in src/cli/main.py

```python
from src.cli.commands.{name} import {name}_command
app.command(name="{name}")(${name}_command)
```

</template>
