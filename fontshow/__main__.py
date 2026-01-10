# fontshow/__main__.py

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

import fontshow.create_catalog
import fontshow.dump_fonts
import fontshow.parse_font_inventory
import fontshow.preflight
from fontshow.cli_utils import add_common_arguments


def main() -> int:
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
    preflight_parser.set_defaults(func=fontshow.preflight.main)

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

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
