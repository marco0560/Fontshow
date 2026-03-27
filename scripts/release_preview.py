#!python
"""
Run a local semantic-release preview.

This maintenance script validates the local release-preview environment
and runs semantic-release in dry-run mode so release metadata can be
checked before performing an actual release workflow.

Responsibilities
----------------
- Verify that required release executables are available.
- Validate the configured semantic-release configuration path.
- Execute a local dry-run release preview command.

Design principles
-----------------
Release preview must be explicit, local, and non-destructive. The script
checks preconditions before execution and limits itself to dry-run
operations so release logic can be inspected without mutating repository
state.

Architectural role
------------------
This module belongs to the developer tooling layer and provides a
release-maintenance utility outside the production Fontshow runtime.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_CONFIG = ".releaserc.json"


def fail(msg: str, *, exit_code: int = 1) -> None:
    """
    Print an error message and terminate the program.

    Parameters
    ----------
    msg : str
        Human-readable error message to print to standard error.
    exit_code : int, optional
        Process exit code used when terminating (default is ``1``).

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        Always raised with the provided exit code.
    """
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(exit_code)


def check_executable(name: str) -> None:
    """
    Verify that an executable is available in the system ``PATH``.

    Parameters
    ----------
    name : str
        Name of the executable to locate.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        Raised if the executable cannot be found in ``PATH``.
    """
    if shutil.which(name) is None:
        fail(f"Required executable not found in PATH: {name}")


def run(cmd: list[str], *, verbose: bool = False) -> None:
    """
    Execute a subprocess command with optional logging.

    Parameters
    ----------
    cmd : list[str]
        Command and arguments to execute.
    verbose : bool, optional
        If ``True``, print the command before executing it.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        Raised if the subprocess exits with a non-zero status code.
    """
    if verbose:
        print("+", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        fail(f"Command failed with exit code {exc.returncode}: {' '.join(cmd)}")


def main(argv: list[str] | None = None) -> int:
    """
    Run a local preview of semantic-release in dry-run mode.

    This command verifies the presence of required executables and a valid
    semantic-release configuration file, then executes semantic-release
    using ``--dry-run`` to show what would be released without publishing
    anything.

    Parameters
    ----------
    argv : list[str] or None, optional
        Command-line arguments to parse. If ``None``, arguments are read
        from ``sys.argv``.

    Returns
    -------
    int
        Exit status code. Returns ``0`` when the preview completes
        successfully.

    Raises
    ------
    SystemExit
        Raised if required executables or configuration files are missing,
        or if semantic-release is not installed locally.
    """
    parser = argparse.ArgumentParser(
        prog="release-preview",
        description="Run semantic-release in dry-run mode (local preview only).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(DEFAULT_CONFIG),
        help="semantic-release config file (default: .releaserc.json)",
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
