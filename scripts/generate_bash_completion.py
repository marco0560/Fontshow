#!/usr/bin/env python3
"""
Generate the checked-in Fontshow Bash completion script.

This script renders the completion script from the current argparse CLI
definition and writes it to ``scripts/completions/fontshow.bash``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fontshow.cli.bash_completion import render_bash_completion

DEFAULT_OUTPUT = Path("scripts/completions/fontshow.bash")


def build_parser() -> argparse.ArgumentParser:
    """
    Build the argument parser for the completion generator script.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.ArgumentParser
        Parser configured for the script's output controls.
    """
    parser = argparse.ArgumentParser(
        prog="generate_bash_completion.py",
        description="Generate the Fontshow Bash completion script.",
        epilog=(
            "Examples:\n"
            "  python scripts/generate_bash_completion.py\n"
            "  python scripts/generate_bash_completion.py --stdout\n"
            "  python scripts/generate_bash_completion.py --output /tmp/fontshow.bash"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination path for the generated Bash completion script.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write the generated script to stdout instead of a file.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse CLI arguments for the completion generator script.

    Parameters
    ----------
    argv : list[str] | None, optional
        Explicit argument vector to parse. When ``None``, arguments are
        read from ``sys.argv``.

    Returns
    -------
    argparse.Namespace
        Parsed output configuration.
    """
    return build_parser().parse_args(list(argv) if argv is not None else None)


def main(argv: list[str] | None = None) -> int:
    """
    Execute the Bash completion generation script.

    Parameters
    ----------
    argv : list[str] | None, optional
        Explicit argument vector to parse. When ``None``, arguments are
        read from ``sys.argv``.

    Returns
    -------
    int
        Process exit code. Returns ``0`` on success.
    """
    args = parse_args(argv)
    content = render_bash_completion()

    if args.stdout:
        print(content, end="")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
