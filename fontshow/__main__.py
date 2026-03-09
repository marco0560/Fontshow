"""
Fontshow command-line entry point.

This module implements the command-line interface entry point used when
executing Fontshow as a Python module.

Responsibilities
----------------
- Parse command-line arguments for the Fontshow CLI.
- Dispatch CLI commands to the corresponding handler functions.
- Provide consistent exit codes and error reporting for CLI operations.

Design principles
-----------------
The entry point should remain thin and deterministic: argument parsing,
command dispatch, and high-level error handling occur here, while the
actual command implementations live in the ``fontshow.cli`` package.

Architectural role
------------------
This module belongs to the **CLI interface layer** and serves as the
runtime entry point when Fontshow is executed as a module
(``python -m fontshow``).
"""

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fontshow.core.cli_utils import log_err

try:
    import fontshow.preflight
    from fontshow.cli import (
        create_catalog,
        dump_fonts,
        parse_inventory,
        validate_inventory,
    )
    from fontshow.core.logging_utils import log, log_trace_cat
except ModuleNotFoundError as e:
    missing = e.name or "<unknown>"
    log_err(f"Required import '{missing}' not available")
    sys.exit(1)

from fontshow.core.cli_utils import add_common_arguments


def dispatch_command(args: argparse.Namespace) -> int:
    """
    Dispatch a parsed CLI command.

    Invokes the command handler stored in ``args.func`` and converts its
    result into a deterministic process exit code. TRACE "flow" events are
    emitted for start, completion, and crash conditions.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments. Must provide a callable ``func`` attribute
        accepting ``args`` and returning either an integer-like exit code
        or ``None``.

    Returns
    -------
    int
        Process exit code:
        - 0 when the handler returns ``None`` or raises ``SystemExit(None)``,
        - ``int(result)`` when the handler returns a non-None value,
        - ``int(e.code)`` when the handler raises ``SystemExit(code)``,
        - 2 for any other unhandled exception.
    """
    log_trace_cat(
        log,
        "flow",
        "cli dispatch started",
        extra={"cmd": getattr(args, "command", None)},
    )

    try:
        result: Any = args.func(args)
        exit_code: int = int(result) if result is not None else 0

        log_trace_cat(
            log,
            "flow",
            "cli dispatch completed",
            extra={"exit_code": exit_code},
        )

    except SystemExit as e:
        exit_code = int(e.code) if e.code is not None else 0

        log_trace_cat(
            log,
            "flow",
            "cli dispatch completed",
            extra={"exit_code": exit_code},
        )

    except Exception:  # noqa: BLE001
        log_trace_cat(
            log,
            "flow",
            "cli dispatch crashed",
            extra={},
        )
        exit_code = 2

    return exit_code


def main() -> int:
    """
    Build the top-level CLI parser, register subcommands, and run dispatch.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Process exit code. Returns 0 after printing help when no subcommand
        is selected; otherwise returns the exit code produced by
        ``dispatch_command``.

    Notes
    -----
    Logging configuration is intentionally not performed here. Logging is
    handled centrally by the shared logging utilities and by test harnesses.
    The package version is resolved from installed metadata and falls back
    to ``"development"`` when the package is not installed.
    """
    try:
        FONTSHOW_VERSION = version("fontshow")
    except PackageNotFoundError:
        FONTSHOW_VERSION = "development"

    parser = argparse.ArgumentParser(
        prog="fontshow",
        description=(
            "Fontshow – font analysis and catalog generation toolkit\n\n"
            "Typical pipeline:\n"
            "  fontshow preflight\n"
            "  fontshow dump-fonts\n"
            "  fontshow parse-inventory\n"
            "  fontshow validate-inventory\n"
            "  fontshow create-catalog"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"fontshow {FONTSHOW_VERSION}",
    )

    subparsers = parser.add_subparsers(
        title="Available commands",
    )

    # ------------------------------------------------------------------
    # preflight
    preflight_parser = subparsers.add_parser(
        "preflight",
        help="Run environment and dependency checks",
    )
    add_common_arguments(
        preflight_parser,
        include_output=True,
        output_default=None,
        output_help="Write preflight report to file (in addition to console output)",
    )
    fontshow.preflight.register_cli(preflight_parser)

    # ------------------------------------------------------------------
    # dump-fonts
    dump_parser = subparsers.add_parser(
        "dump-fonts",
        help="Extract raw font inventory",
    )
    dump_fonts.register_cli(dump_parser)

    # ------------------------------------------------------------------
    # parse-inventory
    parse_parser = subparsers.add_parser(
        "parse-inventory",
        help="Enrich and validate a font inventory",
    )
    parse_inventory.register_cli(parse_parser)

    # ------------------------------------------------------------------
    # validate-inventory
    validate_parser = subparsers.add_parser(
        "validate-inventory",
        help="Validate a Fontshow inventory file against the JSON schema",
    )
    validate_inventory.build_parser(validate_parser)
    validate_parser.set_defaults(func=validate_inventory.run)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # create-catalog
    catalog_parser = subparsers.add_parser(
        "create-catalog",
        help="Generate output artifacts from an inventory",
    )
    create_catalog.register_cli(catalog_parser)
    # ------------------------------------------------------------------

    args = parser.parse_args()

    if not getattr(args, "func", None):
        parser.print_help()
        return 0

    return dispatch_command(args)


if __name__ == "__main__":
    sys.exit(main())
