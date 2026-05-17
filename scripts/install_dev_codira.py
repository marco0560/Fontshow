#!/usr/bin/env python3
"""Install codira tooling from the local sibling checkout."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CODIRA_ROOT = (REPO_ROOT / "../codira").resolve()


def build_install_command(
    *,
    python: str,
    codira_root: Path,
) -> tuple[str, ...]:
    """
    Build the codira first-party install command for the current repository.

    Parameters
    ----------
    python : str
        Python interpreter that should receive the editable codira install.
    codira_root : pathlib.Path
        Root directory of the sibling codira checkout.

    Returns
    -------
    tuple[str, ...]
        Deterministic command invoking the codira install helper.
    """
    return (
        "uv",
        "run",
        "python",
        str(codira_root / "scripts" / "install_first_party_packages.py"),
        "--python",
        python,
        "--include-core",
        "--core-extra",
        "semantic",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments for the codira install wrapper.

    Parameters
    ----------
    argv : list[str] | None, optional
        Optional argument override.

    Returns
    -------
    argparse.Namespace
        Parsed wrapper arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Install codira from the local sibling checkout into the current "
            "repository virtual environment."
        )
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter that should receive the editable codira install.",
    )
    parser.add_argument(
        "--codira-root",
        type=Path,
        default=DEFAULT_CODIRA_ROOT,
        help="Path to the sibling codira checkout.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved install command without executing it.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """
    Install codira into the current repository environment.

    Parameters
    ----------
    argv : list[str] | None, optional
        Optional argument override.

    Returns
    -------
    int
        Process exit code.

    Raises
    ------
    FileNotFoundError
        Raised when the expected sibling codira helper script does not exist.
    subprocess.CalledProcessError
        Raised when the delegated install command fails.
    """
    args = parse_args(argv)
    codira_root = args.codira_root.resolve()
    helper_script = codira_root / "scripts" / "install_first_party_packages.py"

    if not helper_script.is_file():
        msg = f"Codira install helper not found: {helper_script}"
        raise FileNotFoundError(msg)

    command = build_install_command(python=args.python, codira_root=codira_root)
    print(" ".join(shlex.quote(arg) for arg in command))
    if args.dry_run:
        return 0

    subprocess.run(command, cwd=REPO_ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
