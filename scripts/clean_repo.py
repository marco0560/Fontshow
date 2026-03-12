#!python
"""
Clean repository artifacts.

This maintenance script removes generated artifacts and git-ignored files
from the Fontshow repository so the working tree can be restored to a
clean state before validation, release, or refactoring work.

Responsibilities
----------------
- Discover ignored paths currently present in the repository working tree.
- Remove removable files and directories while respecting protected paths.
- Support dry-run execution so cleanup actions can be reviewed safely.

Design principles
-----------------
Repository cleanup must be deterministic and conservative. The script only
acts on paths reported as ignored by git and explicitly preserves protected
developer directories such as virtual environments or editor metadata.

Architectural role
------------------
This module belongs to the developer tooling layer and provides a local
repository-maintenance utility used outside the production Fontshow
pipeline.
"""

import argparse
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path

# Paths that should never be removed, even if ignored by git
PROTECTED_PATHS = {
    ".venv",
    ".vscode",
    "node_modules",
}


def git_ignored_paths() -> Iterable[Path]:
    """
    Yield paths that are ignored by Git and present in the working tree.

    The function invokes ``git status --ignored --porcelain`` and parses
    its output, yielding paths that are reported as ignored (lines starting
    with ``"!! "``).

    Returns
    -------
    Iterable[pathlib.Path]
        Iterator over paths ignored by Git.

    Raises
    ------
    subprocess.CalledProcessError
        Raised if the Git command fails.
    """
    result = subprocess.run(  # (trusted fixed binary, no user input, no shell)
        ["git", "status", "--ignored", "--porcelain"],  # noqa: S607
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
    Remove a filesystem path representing a file or directory.

    Parameters
    ----------
    path : pathlib.Path
        Path to the file or directory to remove.
    dry_run : bool
        If ``True``, do not delete anything and only print what would
        be removed.

    Returns
    -------
    None

    Raises
    ------
    OSError
        Raised if the removal operation fails.
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
    """
    Clean the repository by removing ignored (untracked) artifacts.

    This command-line entry point scans the current repository for files and
    directories that are ignored by Git (for example build artifacts, caches,
    or generated files) and removes them, excluding paths listed in
    ``PROTECTED_PATHS``.

    A dry-run mode is available to preview the actions without performing
    any deletion.

    Parameters
    ----------
    None

    Returns
    -------
    None
        The function performs filesystem side effects and prints a summary
        of the operation to standard output.

    Raises
    ------
    SystemExit
        Raised by :func:`argparse.ArgumentParser.parse_args` when argument
        parsing fails or when ``--help`` is requested.
    """
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
