#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_CONFIG = ".releaserc.json"


def fail(msg: str, *, exit_code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(exit_code)


def check_executable(name: str) -> None:
    if shutil.which(name) is None:
        fail(f"Required executable not found in PATH: {name}")


def run(cmd: list[str], *, verbose: bool = False) -> None:
    if verbose:
        print("+", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        fail(f"Command failed with exit code {exc.returncode}: {' '.join(cmd)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="release-preview",
        description="Run semantic-release in dry-run mode (local preview only).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(DEFAULT_CONFIG),
        help="semantic-release config file (default: .releaserc.local.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print executed commands",
    )

    args = parser.parse_args(argv)

    # --- Preconditions -------------------------------------------------

    check_executable("node")
    check_executable("npx")

    if not args.config.exists():
        fail(f"Config file not found: {args.config}")

    # Check semantic-release is available locally (node_modules)
    try:
        subprocess.run(  # (trusted fixed binary, no user input, no shell)
            ["npx", "--no-install", "semantic-release", "--version"],  # noqa: S607
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError:
        fail(
            "semantic-release is not installed locally.\n"
            "Hint: run `npm install --save-dev semantic-release`"
        )

    # --- Run semantic-release dry-run -----------------------------------

    print("Running semantic-release preview (dry-run)")
    print(f"Config: {args.config}")
    print()

    cmd = [
        "npx",
        "semantic-release",
        "--dry-run",
        "--config",
        str(args.config),
    ]

    run(cmd, verbose=args.verbose)

    print()
    print("Release preview completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
