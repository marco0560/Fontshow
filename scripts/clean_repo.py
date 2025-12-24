#!/usr/bin/env python3
"""
clean_repo.py

Remove generated artifacts and ignored files from the Fontshow repository,
bringing the working tree back to a clean state.

By default, the script removes files that are:
- untracked
- ignored by .gitignore

Use --dry-run to preview what would be removed without deleting anything.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path

# Paths that should never be removed, even if ignored by git
PROTECTED_PATHS = {
    ".venv",
}


def git_ignored_paths() -> Iterable[Path]:
    """
    Return a list of paths that are ignored by git and currently present
    in the working tree.
    """
    result = subprocess.run(
        ["git", "status", "--ignored", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )

    for line in result.stdout.splitlines():
        # Lines starting with '!!' are ignored files
        if line.startswith("!! "):
            yield Path(line[3:])


def remove_path(path: Path, dry_run: bool) -> None:
    """
    Remove a file or directory safely.
    If dry_run is True, only print what would be removed.
    """
    if dry_run:
        print(f"[DRY-RUN] Would remove: {path}")
        return

    if path.is_dir():
        shutil.rmtree(path)
        print(f"Removed directory: {path}")
    elif path.exists():
        path.unlink()
        print(f"Removed file: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean repository by removing ignored (untracked) artifacts."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting anything",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()

    print("Cleaning repository (ignored artifacts only)...")
    if args.dry_run:
        print("Running in DRY-RUN mode.\n")
    else:
        print()

    ignored = [
        path for path in git_ignored_paths() if path.parts[0] not in PROTECTED_PATHS
    ]

    if not ignored:
        print("Nothing to clean. Repository is already clean.")
        return

    for path in ignored:
        full_path = repo_root / path
        remove_path(full_path, dry_run=args.dry_run)

    if args.dry_run:
        print("\nDry-run completed. No files were removed.")
    else:
        print("\nDone. Repository is clean.")


if __name__ == "__main__":
    main()
