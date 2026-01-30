import argparse
import json
import sys
from pathlib import Path

from jsonschema.exceptions import ValidationError

from fontshow import __version__
from fontshow.schema_validation import validate_inventory_schema
from fontshow.semantic_validation import validate_language_codes


def log_ok(msg: str) -> None:
    print(f"[OK  ] {msg}")


def log_info(msg: str) -> None:
    print(f"[INFO] {msg}")


def log_warn(msg: str) -> None:
    print(f"[WARN] {msg}", file=sys.stderr)


def log_err(msg: str) -> None:
    print(f"[ERR ] {msg}", file=sys.stderr)


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


def add_verbose_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose mode",
    )


def add_quiet_argument(parser: argparse.ArgumentParser) -> None:
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

    if not args.quiet:
        for w in semantic_warnings:
            _log_by_severity(
                w["severity"], f"{w['code']} ({w['font']}): {w['message']}"
            )

        for w in warnings:
            _log_by_severity(w["severity"], f"{w['code']}: {w['message']}")

    if not args.quiet:
        log_ok("Schema validation passed.")
    return 0
