import argparse
import json
import sys
from argparse import _ActionsContainer
from pathlib import Path

from jsonschema.exceptions import ValidationError

from fontshow import __version__
from fontshow.schema_validation import validate_inventory_schema
from fontshow.semantic_validation import validate_language_codes

# ------------------------------------------------------------
# Centralized CLI presentation state
# ------------------------------------------------------------

_QUIET: bool = False
_VERBOSE: bool = False


def set_cli_mode(quiet: bool, verbose: bool) -> None:
    """
    Set global CLI presentation mode.

    quiet   → suppress info/ok
    verbose → enable verbose variants

    quiet overrides verbose.
    """
    global _QUIET, _VERBOSE
    _QUIET = bool(quiet)
    _VERBOSE = bool(verbose) and not _QUIET


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def _format_extra(extra: dict | None) -> str:
    """
    Deterministically format extra key/value pairs for CLI output.

    Output format:
        | key=value | key=value

    Keys sorted for determinism.
    Values stringified via str().
    """
    if not extra:
        return ""

    parts = []
    for k in sorted(extra):
        parts.append(f"{k}={extra[k]}")
    return " | " + " | ".join(parts)


def _select_message(default: str, verbose: str | None) -> str:
    """
    Select message according to CLI mode.
    """
    if _VERBOSE and verbose:
        return verbose
    return default


# ------------------------------------------------------------
# CLI presentation API
# ------------------------------------------------------------


def log_info(
    default: str, verbose: str | None = None, *, extra: dict | None = None
) -> None:
    """
    Emit CLI INFO message.

    Behavior:
    - suppressed in quiet mode
    - verbose message used when verbose mode active
    - deterministic formatting of extra
    """
    if _QUIET:
        return

    message = _select_message(default, verbose)
    message += _format_extra(extra)

    print(f"[INFO] {message}")


def log_ok(
    default: str, verbose: str | None = None, *, extra: dict | None = None
) -> None:
    """
    Emit CLI OK message.

    Same behavior as log_info.
    """
    if _QUIET:
        return

    message = _select_message(default, verbose)
    message += _format_extra(extra)

    print(f"[OK  ] {message}")


def log_warn(message: str) -> None:
    """
    Emit CLI WARNING message (always shown).
    """

    print(f"[WARN] {message}", file=sys.stderr)


def log_err(message: str) -> None:
    """
    Emit CLI ERROR message (always shown).
    """

    print(f"[ERR ] {message}", file=sys.stderr)


def _log_by_severity(severity: str, message: str) -> None:
    sev = (severity or "").strip().lower()
    if sev in {"warn", "warning"}:
        log_warn(message)
    elif sev in {"err", "error"}:
        log_err(message)
    elif sev in {"ok", "success"}:
        log_ok(message)
    else:
        log_info(message)


def add_version_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )


def add_verbose_argument(parser: _ActionsContainer) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose mode",
    )


def add_quiet_argument(parser: _ActionsContainer) -> None:
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Enable quiet mode",
    )


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add CLI arguments common to all Fontshow commands
    (e.g. --version, --verbose, --quiet).
    """
    add_version_argument(parser)

    group = parser.add_mutually_exclusive_group()

    add_verbose_argument(group)
    add_quiet_argument(group)


def cli_validate_inventory() -> int:
    """
    CLI entry point for validating a Fontshow inventory against the JSON schema.
    """
    parser = argparse.ArgumentParser(
        prog="fontshow-validate",
        description="Validate a Fontshow inventory file against the JSON Schema.",
    )
    parser.add_argument(
        "path",
        help="Path to the inventory JSON file to validate",
    )

    args = parser.parse_args()
    inventory_path = Path(args.path)

    if not inventory_path.exists():
        log_err(f"file not found: {inventory_path}")
        return 1

    try:
        raw = inventory_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log_err(f"invalid JSON file: {e}")
        return 1

    try:
        validate_inventory_schema(data)
    except ValidationError as e:
        log_err("Schema validation failed")
        log_err(str(e))
        return 1

    semantic_warnings = validate_language_codes(data)
    warnings = data.get("warnings", [])

    if not _QUIET:
        for w in semantic_warnings:
            _log_by_severity(
                w["severity"], f"{w['code']} ({w['font']}): {w['message']}"
            )

        for w in warnings:
            _log_by_severity(w["severity"], f"{w['code']}: {w['message']}")

    log_ok("Schema validation passed.")
    return 0
