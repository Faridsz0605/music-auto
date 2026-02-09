"""Config command - view and edit configuration."""

import typer

from src.cli.ui import console, print_header, print_info, print_success
from src.core.config import AppConfig, load_config, save_config

CONFIG_FILE = "config.json"
SENSITIVE_KEYS = {"client_id", "client_secret"}


def _mask_sensitive(key: str, value: str) -> str:
    """Mask sensitive config values for display.

    Shows first 4 and last 4 characters for values longer than 8,
    otherwise fully masked.

    Args:
        key: Configuration key name.
        value: Configuration value.

    Returns:
        Masked or original value string.
    """
    if key not in SENSITIVE_KEYS or not value:
        return value
    if len(value) > 8:
        return value[:4] + "****" + value[-4:]
    return "****"


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
            display = _mask_sensitive(key, str(value))
            console.print(f"  {key}: [bold]{display}[/bold]")
        print_info(f"Config file: {CONFIG_FILE}")
