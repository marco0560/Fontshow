#!python
"""
Clean repository artifacts.

This maintenance script removes generated artifacts and git-ignored files
from the Fontshow repository so the working tree can be restored to a
clean state before validation, release, or refactoring work.

Responsibilities
----------------
- Discover ignored paths currently present in the repository working tree.
- Discover known pytest/runtime artifact directories even when Git cannot
  traverse them.
- Remove removable files and directories while respecting protected paths.
- Support dry-run execution so cleanup actions can be reviewed safely.

Design principles
-----------------
Repository cleanup must be deterministic and conservative. The script only
acts on paths reported as ignored by git and explicitly preserves protected
developer directories such as virtual environments or editor metadata.
Known pytest artifact paths are included explicitly because permission issues
can prevent Git from reporting their children reliably.

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
    ".codira",
    "guidelines.tar.xz",
}

KNOWN_ARTIFACT_PATTERNS = (
    ".mypy_cache",
    ".pytest_cache",
    ".pytest_tmp",
    ".pytest-basetemp",
    ".ruff_cache",
    ".tmp",
    "pytest-cache-files-*",
    "pytest-runtime",
)


def git_ignored_paths() -> Iterable[Path]:
    """
    Yield paths that are ignored by Git and present in the working tree.

    The function invokes ``git status --ignored --porcelain`` and parses
    its output, yielding paths that are reported as ignored (lines starting
    with ``"!! "``).

    Parameters
    ----------
    None

    Yields
    ------
    pathlib.Path
        Paths ignored by Git and present in the working tree.

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


def known_artifact_paths(repo_root: Path) -> Iterable[Path]:
    """
    Yield known repository-local artifact paths that currently exist.

    Parameters
    ----------
    repo_root : pathlib.Path
        Repository root used as the base for artifact discovery.

    Yields
    ------
    pathlib.Path
        Repository-relative paths matching known artifact names.
    """
    for pattern in KNOWN_ARTIFACT_PATTERNS:
        for path in repo_root.glob(pattern):
            yield path.relative_to(repo_root)


def cleanup_paths(repo_root: Path) -> list[Path]:
    """
    Return repository-relative cleanup paths in deterministic order.

    Parameters
    ----------
    repo_root : pathlib.Path
        Repository root used as the base for artifact discovery.

    Returns
    -------
    list[pathlib.Path]
        Deduplicated cleanup paths excluding protected top-level paths.
    """
    discovered = [*git_ignored_paths(), *known_artifact_paths(repo_root)]
    paths: list[Path] = []
    seen: set[Path] = set()

    for path in discovered:
        if not path.parts or path.parts[0] in PROTECTED_PATHS:
            continue
        if path in seen:
            continue
        if not (repo_root / path).exists():
            continue
        seen.add(path)
        paths.append(path)

    return sorted(paths)


def remove_path(path: Path, dry_run: bool) -> bool:
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
    bool
        ``True`` when the path was removed or only reported in dry-run mode,
        ``False`` when removal failed.

    Raises
    ------
    None
    """
    if dry_run:
        print(f"[DRY-RUN] Would remove: {path}")
        return True

    try:
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Removed directory: {path}")
        elif path.exists():
            path.unlink()
            print(f"Removed file: {path}")
    except OSError as exc:
        print(f"Failed to remove: {path} ({exc})")
        return False

    return True


def main() -> None:
    """
    Clean the repository by removing ignored and known temporary artifacts.

    This command-line entry point scans the current repository for files and
    directories that are ignored by Git (for example build artifacts, caches,
    or generated files), adds known pytest/runtime temporary paths, and removes
    them, excluding paths listed in ``PROTECTED_PATHS``.

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

    print("Cleaning repository (ignored and known temporary artifacts)...")
    if args.dry_run:
        print("Running in DRY-RUN mode.\n")
    else:
        print()

    ignored = cleanup_paths(repo_root)

    if not ignored:
        print("Nothing to clean. Repository is already clean.")
        return

    failed: list[Path] = []

    for path in ignored:
        full_path = repo_root / path
        if not remove_path(full_path, dry_run=args.dry_run):
            failed.append(path)

    if args.dry_run:
        print("\nDry-run completed. No files were removed.")
    elif failed:
        print("\nCleanup incomplete. Failed paths:")
        for path in failed:
            print(f"- {path}")
        raise SystemExit(1)
    else:
        print("\nDone. Repository is clean.")


if __name__ == "__main__":
    main()
