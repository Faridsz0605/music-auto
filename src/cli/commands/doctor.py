"""Doctor command - system health checks for ymd."""

import json
import shutil
from pathlib import Path

import typer

from src.cli.ui import console, print_error, print_header, print_info, print_success
from src.core.config import CONFIG_FILE, load_config
from src.core.exceptions import ConfigError


def _check_config() -> bool:
    """Check if config.json exists and is valid."""
    if not CONFIG_FILE.exists():
        print_error("config.json not found")
        print_info("Run 'ymd config --init' to create a default config")
        return False

    try:
        load_config()
        print_success("config.json is valid")
        return True
    except ConfigError as e:
        print_error(f"config.json is invalid: {e}")
        return False


def _check_oauth_credentials() -> bool:
    """Check if OAuth credentials are configured."""
    try:
        config = load_config()
    except ConfigError:
        return False

    if not config.client_id or not config.client_secret:
        print_error(
            "OAuth credentials not configured. "
            "Set client_id/client_secret in config.json "
            "or use YMD_CLIENT_ID/YMD_CLIENT_SECRET env vars"
        )
        return False

    print_success("OAuth credentials configured")
    return True


def _check_oauth_tokens() -> bool:
    """Check if oauth.json exists and has valid structure."""
    oauth_file = Path("oauth.json")
    if not oauth_file.exists():
        print_error("oauth.json not found - run 'ymd auth' to authenticate")
        return False

    try:
        data = json.loads(oauth_file.read_text())
        if "access_token" not in data and "token" not in data:
            print_error("oauth.json appears corrupted - run 'ymd auth'")
            return False
        print_success("OAuth tokens present")

        # Check for expiry if available
        if "expires_at" in data:
            from datetime import UTC, datetime

            expires_at = data["expires_at"]
            if isinstance(expires_at, int | float):
                expiry = datetime.fromtimestamp(expires_at, tz=UTC)
                now = datetime.now(UTC)
                if expiry < now:
                    print_info("Token expired - will be refreshed on next use")

        return True
    except (json.JSONDecodeError, OSError) as e:
        print_error(f"Cannot read oauth.json: {e}")
        return False


def _check_yt_dlp() -> bool:
    """Check if yt-dlp is installed and get version."""
    try:
        import yt_dlp

        version = getattr(yt_dlp, "version", None)
        version_str = (
            getattr(version, "__version__", "unknown") if version else "unknown"
        )
        print_success(f"yt-dlp installed (version: {version_str})")
        return True
    except ImportError:
        print_error("yt-dlp not installed - run 'pip install yt-dlp'")
        return False


def _check_ffmpeg() -> bool:
    """Check if ffmpeg is available in PATH."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print_success(f"ffmpeg found: {ffmpeg_path}")
        return True
    else:
        print_error("ffmpeg not found in PATH - required for audio conversion")
        return False


def _check_download_dir() -> bool:
    """Check if download directory is accessible."""
    try:
        config = load_config()
    except ConfigError:
        return False

    download_dir = config.download_dir
    if download_dir.exists():
        if download_dir.is_dir():
            # Check write permission
            test_file = download_dir / ".ymd_write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                print_success(f"Download dir writable: {download_dir}")
                return True
            except OSError:
                print_error(f"Download dir not writable: {download_dir}")
                return False
        else:
            print_error(
                f"Download path exists but is not a directory: " f"{download_dir}"
            )
            return False
    else:
        print_info(
            f"Download dir does not exist yet: {download_dir} "
            "(will be created on first sync)"
        )
        return True


def _check_api_connection() -> bool:
    """Check connection to YouTube Music API."""
    try:
        from src.core.auth import load_auth

        ytmusic = load_auth()
        ytmusic.get_library_playlists(limit=1)
        print_success("YouTube Music API connection OK")
        return True
    except Exception as e:
        print_error(f"Cannot connect to YouTube Music API: {e}")
        return False


def doctor_command(
    skip_api: bool = typer.Option(
        False,
        "--skip-api",
        help="Skip API connection check (offline mode)",
    ),
) -> None:
    """Run system health checks for ymd."""
    print_header("ymd Doctor - System Health Check")
    console.print()

    checks_passed = 0
    checks_total = 0

    checks = [
        ("Configuration", _check_config),
        ("OAuth Credentials", _check_oauth_credentials),
        ("OAuth Tokens", _check_oauth_tokens),
        ("yt-dlp", _check_yt_dlp),
        ("ffmpeg", _check_ffmpeg),
        ("Download Directory", _check_download_dir),
    ]

    for name, check_fn in checks:
        checks_total += 1
        console.print(f"\n  [bold]Checking {name}...[/bold]")
        if check_fn():
            checks_passed += 1

    if not skip_api:
        checks_total += 1
        console.print("\n  [bold]Checking API Connection...[/bold]")
        if _check_api_connection():
            checks_passed += 1
    else:
        print_info("Skipping API connection check (--skip-api)")

    # Summary
    console.print()
    print_header("Results")
    if checks_passed == checks_total:
        print_success(f"All checks passed ({checks_passed}/{checks_total})")
        raise typer.Exit(code=0)
    else:
        failed = checks_total - checks_passed
        print_error(
            f"{failed} check(s) failed " f"({checks_passed}/{checks_total} passed)"
        )
        raise typer.Exit(code=1)
