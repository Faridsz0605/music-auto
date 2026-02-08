"""Config command - view and edit configuration."""

import typer

from src.cli.ui import console, print_header, print_info, print_success
from src.core.config import AppConfig, load_config, save_config

CONFIG_FILE = "config.json"


def config_command(
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Show current configuration",
    ),
    init: bool = typer.Option(
        False,
        "--init",
        help="Create default configuration file",
    ),
    set_value: list[str] | None = typer.Option(
        None,
        "--set",
        help="Set a config value (key=value)",
    ),
) -> None:
    """View or edit YMD configuration."""
    if init:
        config = AppConfig()
        save_config(config)
        print_success(f"Created default config at {CONFIG_FILE}")
        return

    config = load_config()

    if set_value:
        data = config.model_dump()
        for kv in set_value:
            if "=" not in kv:
                console.print(
                    f"[error]Invalid format: {kv} " f"(use key=value)[/error]"
                )
                raise typer.Exit(code=1)
            key, value = kv.split("=", 1)
            key = key.strip()
            if key not in data:
                console.print(f"[error]Unknown config key: {key}[/error]")
                console.print("[dim]Valid keys: " f"{', '.join(data.keys())}[/dim]")
                raise typer.Exit(code=1)

            # Cast to the right type
            current = data[key]
            if isinstance(current, int):
                data[key] = int(value)
            elif isinstance(current, bool):
                data[key] = value.lower() in (
                    "true",
                    "1",
                    "yes",
                )
            else:
                data[key] = value

        config = AppConfig(**data)
        save_config(config)
        print_success("Configuration updated")

    # Show config (always shown after set, or with --show)
    if show or set_value:
        print_header("Configuration")
        data = config.model_dump(mode="json")
        for key, value in data.items():
            console.print(f"  {key}: [bold]{value}[/bold]")
        print_info(f"Config file: {CONFIG_FILE}")
