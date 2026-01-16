#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def fail(msg: str, *, exit_code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(exit_code)


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
    except subprocess.CalledProcessError as exc:
        fail(f"Command failed with exit code {exc.returncode}: {' '.join(cmd)}")


def check_executable(name: str) -> None:
    if shutil.which(name) is None:
        fail(f"Required executable not found in PATH: {name}")


def main(argv: list[str] | None = None) -> int:
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
