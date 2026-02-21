import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fontshow.cli_utils import log_err

try:
    import fontshow.create_catalog
    import fontshow.dump_fonts
    import fontshow.parse_font_inventory
    import fontshow.preflight
    from fontshow.logging_utils import log, log_trace_cat
except ModuleNotFoundError as e:
    missing = e.name or "<unknown>"
    log_err(f"Required import '{missing}' not available")
    sys.exit(1)

from fontshow.cli_utils import add_common_arguments


def dispatch_command(args: argparse.Namespace) -> int:
    """
    Dispatch a parsed CLI command.

    The function invokes the command handler stored in `args.func`,
    captures its return value, and converts it into a deterministic
    process exit code. TRACE "flow" events are emitted for start,
    completion, and crash conditions.

    Args:
        args: Parsed CLI arguments. Must provide a callable `func` attribute
            that accepts `args` and returns either an integer-like exit code or
            `None`.

    Returns:
        Process exit code:
        - 0 when the handler returns `None` or raises `SystemExit(None)`,
        - `int(result)` when the handler returns a non-None value,
        - `int(e.code)` when the handler raises `SystemExit(code)`,
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
    CLI entrypoint.

    NOTE:
    Logging configuration is intentionally NOT performed here.
    Logging is handled centrally via `fontshow.logging_utils`
    and test harnesses (pytest caplog).

    Parameters
    ----------
    None

    Returns
    -------
    int
        Process exit code (0 for success, non-zero for failure).
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
    add_common_arguments(preflight_parser)
    fontshow.preflight.register_cli(preflight_parser)

    # ------------------------------------------------------------------
    # dump-fonts
    dump_parser = subparsers.add_parser(
        "dump-fonts",
        help="Extract raw font inventory",
    )
    fontshow.dump_fonts.register_cli(dump_parser)

    # ------------------------------------------------------------------
    # parse-inventory
    parse_parser = subparsers.add_parser(
        "parse-inventory",
        help="Enrich and validate a font inventory",
    )
    fontshow.parse_font_inventory.register_cli(parse_parser)

    # ------------------------------------------------------------------
    # create-catalog
    catalog_parser = subparsers.add_parser(
        "create-catalog",
        help="Generate output artifacts from an inventory",
    )
    fontshow.create_catalog.register_cli(catalog_parser)
    # ------------------------------------------------------------------

    args = parser.parse_args()

    if not getattr(args, "func", None):
        parser.print_help()
        return 0

    return dispatch_command(args)


if __name__ == "__main__":
    sys.exit(main())
