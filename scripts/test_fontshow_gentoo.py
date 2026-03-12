#!python
"""
Run a local Gentoo-style Fontshow end-to-end test.

This maintenance script exercises the installed Fontshow command-line
workflow in a temporary working directory, covering preflight,
inventory generation, parsing, and validation in a local environment.

Responsibilities
----------------
- Verify the availability of required Fontshow executables.
- Execute the end-to-end CLI workflow in a temporary workspace.
- Report failures early and preserve the workspace when requested.

Design principles
-----------------
End-to-end verification must mimic a real local user workflow while
remaining isolated from the repository state. The script uses a temporary
working directory and explicit command execution so failures are easy to
diagnose and the workflow remains reproducible.

Architectural role
------------------
This module belongs to the developer tooling layer and provides a local
integration-test utility outside the production Fontshow pipeline.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def fail(msg: str, *, exit_code: int = 1) -> None:
    """
    Print an error message and terminate the test script.

    Parameters
    ----------
    msg : str
        Error message describing the failure.
    exit_code : int, optional
        Exit code used when terminating the program (default is ``1``).

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        Always raised with the specified exit code.
    """
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(exit_code)


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    """
    Execute a subprocess command and terminate on failure.

    The command is printed before execution to provide a simple execution
    trace during the test run.

    Parameters
    ----------
    cmd : list[str]
        Command and arguments to execute.
    cwd : pathlib.Path or None, optional
        Working directory in which the command should be executed.
        If ``None``, the current process working directory is used.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        Raised if the command exits with a non-zero status code.
    """
    print("+", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
    except subprocess.CalledProcessError as exc:
        fail(f"Command failed with exit code {exc.returncode}: {' '.join(cmd)}")


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


def main(argv: list[str] | None = None) -> int:
    """
    Run a local end-to-end Fontshow workflow test.

    This command performs a simplified workflow similar to what a
    distribution build environment (such as Gentoo) would execute. It
    validates that the main CLI commands run successfully and that the
    expected output artifacts are produced.

    The test performs the following steps:

    * Verify required executables are available.
    * Run basic CLI checks.
    * Execute the ``preflight`` command.
    * Generate a font inventory using ``dump-fonts``.
    * Enrich the inventory with ``parse-inventory``.
    * Validate the resulting dataset with ``fontshow-validate``.

    Parameters
    ----------
    argv : list[str] or None, optional
        Command-line arguments passed to the parser. If ``None``,
        arguments are read from ``sys.argv``.

    Returns
    -------
    int
        Exit status code. Returns ``0`` when the workflow completes
        successfully.

    Raises
    ------
    SystemExit
        Raised if required executables are missing or if any command
        invoked during the workflow fails.
    """
    parser = argparse.ArgumentParser(
        prog="test-fontshow-gentoo",
        description="Local end-to-end Fontshow test (Gentoo-style workflow).",
    )
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Do not delete the temporary working directory",
    )

    args = parser.parse_args(argv)

    # --- Preconditions -------------------------------------------------
    check_executable("fontshow")
    check_executable("fontshow-validate")

    # --- Working directory ---------------------------------------------
    tmpdir_obj = tempfile.TemporaryDirectory(prefix="fontshow-gentoo-")
    workdir = Path(tmpdir_obj.name)

    print(f"Working directory: {workdir}")
    print()

    try:
        # --- Basic checks ----------------------------------------------
        run(["fontshow", "-h"])
        run(["fontshow", "-V"])

        # --- Preflight --------------------------------------------------
        run(["fontshow", "preflight"])

        # --- Dump fonts -------------------------------------------------
        inventory = workdir / "inventory.json"
        run(
            [
                "fontshow",
                "dump-fonts",
                "--output",
                str(inventory),
            ]
        )

        if not inventory.exists():
            fail("dump-fonts did not produce inventory.json")

        # --- Parse inventory -------------------------------------------
        enriched = workdir / "inventory_enriched.json"
        run(
            [
                "fontshow",
                "parse-inventory",
                "--input",
                str(inventory),
                "--output",
                str(enriched),
            ]
        )

        if not enriched.exists():
            fail("parse-inventory did not produce inventory_enriched.json")

        # --- Validate ---------------------------------------------------
        run(["fontshow-validate", str(enriched)])

        print()
        print("Fontshow Gentoo-style test completed successfully.")
        return 0

    finally:
        if args.keep_workdir:
            print()
            print(f"Keeping working directory: {workdir}")
            tmpdir_obj.cleanup = lambda: None
        else:
            tmpdir_obj.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
