# fontshow/__main__.py

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

import fontshow.create_catalog
import fontshow.dump_fonts
import fontshow.parse_font_inventory
import fontshow.preflight
from fontshow.cli_utils import add_common_arguments
from fontshow.logging_utils import log, log_trace_cat


def dispatch_command(args):
    log_trace_cat(
        log,
        "flow",
        "cli dispatch started",
        extra={
            "command": getattr(args, "command", None),
        },
    )
    try:
        # args.func is set by the subparser via set_defaults(func=...)
        log_trace_cat(
            log,
            "flow",
            "cli command resolved",
            extra={
                "command": getattr(args, "command", None),
                "handler": getattr(getattr(args, "func", None), "__name__", None),
            },
        )
        result = args.func(args)

        exit_code = int(result) if result is not None else 0
        log_trace_cat(
            log,
            "flow",
            "cli dispatch completed",
            extra={
                "command": getattr(args, "command", None),
                "exit_code": exit_code,
            },
        )

        # Normalize return value to exit code

    except SystemExit as e:
        exit_code = int(e.code) if e.code is not None else 0
        log_trace_cat(
            log,
            "flow",
            "cli dispatch completed",
            extra={
                "command": getattr(args, "command", None),
                "exit_code": exit_code,
                "system_exit": True,
            },
        )

    except Exception:  # noqa: BLE001
        # (Top-level crash barrier: convert unexpected failure → exit code 2)
        log_trace_cat(
            log,
            "flow",
            "cli dispatch completed",
            extra={
                "command": getattr(args, "command", None),
                "exit_code": 2,
                "exception": True,
            },
        )
        exit_code = 2
    finally:
        pass

    return exit_code


def main() -> int:
    """
    CLI entrypoint.

    NOTE:
    Logging configuration is intentionally NOT performed here.
    Logging is handled centrally via `fontshow.logging_utils`
    and test harnesses (pytest caplog).
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
