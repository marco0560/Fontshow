"""
Fontshow validate-inventory CLI command.

This module implements the inventory validation stage of the Fontshow
pipeline.

Responsibilities
----------------
- Validate inventory structure against the JSON schema.
- Run semantic validation checks on inventory metadata.
- Report validation results and warnings to the CLI.

Design principles
-----------------
Validation logic itself resides in the inventory subsystem. This
module only orchestrates the validation workflow and formats CLI
output while delegating the actual checks to domain modules.

Architectural role
------------------
This module belongs to the **CLI interface layer** and implements the
inventory validation entry point for the Fontshow CLI.
"""

import argparse
import json
import sys
from pathlib import Path

from jsonschema.exceptions import ValidationError

from fontshow.core.cli_utils import (
    _log_by_severity,
    log_err,
    log_ok,
    set_cli_mode,
)
from fontshow.core.json_boundary import normalize_loaded_enums
from fontshow.inventory.schema_validation import validate_inventory_schema
from fontshow.inventory.semantic_validation import validate_language_codes


def build_parser(parser: argparse.ArgumentParser) -> None:
    """
    Register validate-inventory CLI arguments on a parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser instance to configure for the validation command.

    Returns
    -------
    None

    Notes
    -----
    The parser is configured in place so the command can be registered
    both under the top-level dispatcher and under a standalone
    module-local ``__main__`` block.
    """
    parser.prog = "validate-inventory"
    parser.description = "Validate a Fontshow inventory file against the JSON Schema."
    parser.add_argument(
        "path",
        help="Path to the inventory JSON file to validate",
    )


def register_cli(parser: argparse.ArgumentParser) -> None:
    """
    Register validate-inventory CLI arguments on an existing parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser instance configured by the top-level dispatcher.

    Returns
    -------
    None

    Notes
    -----
    Used by the top-level Fontshow dispatcher to bind the
    ``validate-inventory`` command to the shared validation entrypoint.
    """
    build_parser(parser)
    parser.set_defaults(func=main)


def run(args) -> int:
    """
    CLI entry point for validating a Fontshow inventory against the JSON schema.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments containing the inventory path and common
        verbosity flags.

    Returns
    -------
    int
        Exit code:
        - 0 if validation succeeds
        - 1 if the file is missing, invalid JSON, schema validation fails,
          or semantic validation emits blocking errors.

    Raises
    ------
    OSError
        May propagate if the inventory file exists but cannot be read.

    Notes
    -----
    - Loads and normalizes enum values from the inventory.
    - Performs JSON schema validation.
    - Performs semantic validation of language codes.
    - Emits CLI output according to severity and current CLI mode.
    - `jsonschema.exceptions.ValidationError` is handled internally and
      converted into exit code ``1``.
    """
    set_cli_mode(args.quiet, args.verbose)
    inventory_path = Path(args.path)

    if not inventory_path.exists():
        log_err(f"file not found: {inventory_path}")
        return 1

    try:
        raw = inventory_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        normalize_loaded_enums(data)
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

    for w in semantic_warnings:
        _log_by_severity(w["severity"], f"{w['code']} ({w['font']}): {w['message']}")

    for w in warnings:
        _log_by_severity(w["severity"], f"{w['code']}: {w['message']}")

    log_ok("Schema validation passed.")
    return 0


def main(args) -> int:
    """
    Public CLI entrypoint for validate-inventory.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments containing the inventory path and common
        verbosity flags.

    Returns
    -------
    int
        Process exit code returned by ``run(args)``.

    Notes
    -----
    Thin wrapper around ``run`` kept consistent with the other top-level
    CLI modules so the command can be used uniformly through the
    dispatcher and through module-local execution.
    """
    return run(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="validate-inventory")
    build_parser(parser)
    sys.exit(main(parser.parse_args()))
