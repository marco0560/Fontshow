#!/usr/bin/env python3
"""
Generate a deterministic bootstrap audit report for the Fontshow repository.

This script produces the artifact ``bootstrap_audit_report.txt`` used as the
authoritative Source of Truth (SOT) for deterministic auditing sessions with
AI assistants.

The generated report freezes the following repository metadata:

• repository directory tree
• list of Python files under src/fontshow/, tests/, and scripts/
• SHA256 hash baseline for every Python file
• deterministic FILE AUDIT ORDER
• frozen function inventory extracted via regex

The report allows an external auditor (human or AI) to verify repository
integrity and to perform reproducible code audits without reconstructing the
repository structure heuristically.

The output is deterministic as long as the repository contents do not change.

Notes
-----
The function inventory is extracted using the same regular expression used
in the auditing protocol:

``^[[:space:]]*(async[[:space:]]+def|def)[[:space:]]+...``

This captures:

• module-level functions
• class methods
• nested functions
• async functions

Only textual detection is performed; no AST parsing is required.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

EXCLUDED_TREE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
}

FUNC_PATTERN = re.compile(
    r"^[ \t]*(async[ \t]+def|def)[ \t]+[A-Za-z_][A-Za-z0-9_]*[ \t]*\(",
    re.MULTILINE,
)


def git_commit_hash(repo_root: Path) -> str:
    """
    Return the current Git commit hash.

    Parameters
    ----------
    repo_root : Path
        Root directory of the Git repository.

    Returns
    -------
    str
        Full 40-character commit SHA.
    """
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def git_is_clean(repo_root: Path) -> bool:
    """
    Determine whether the working tree contains uncommitted changes.

    Parameters
    ----------
    repo_root : Path
        Root directory of the Git repository.

    Returns
    -------
    bool
        True if the working tree is clean.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],  # noqa: S607
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() == ""


def verify_git_blobs(repo_root: Path) -> bool:
    """
    Verify that working-tree files match Git blob hashes.

    Parameters
    ----------
    repo_root : Path
        Root directory of the Git repository.

    Returns
    -------
    bool
        True if all tracked files match their Git blob hashes.
    """
    result = subprocess.run(
        ["git", "ls-files", "-s", "-z"],  # noqa: S607
        cwd=repo_root,
        capture_output=True,
        text=False,
        check=True,
    )

    entries = result.stdout.split(b"\0")

    for entry in entries:
        if not entry:
            continue

        meta, path = entry.split(b"\t", 1)
        mode, blob_hash, stage = meta.decode().split()

        path_str = path.decode()

        current = subprocess.run(
            ["git", "hash-object", path_str],  # noqa: S607
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        if current != blob_hash:
            return False

    return True


def git_tracked_files(repo_root: Path) -> list[Path]:
    """
    Return all files tracked by git in the repository.

    Parameters
    ----------
    repo_root : Path
        Root directory of the git repository.

    Returns
    -------
    list[Path]
        Paths of files tracked by git, relative to the repository root.

    Notes
    -----
    The function uses ``git ls-files`` which lists exactly the files
    under version control. This avoids including:

    • ignored artifacts
    • build outputs
    • temporary files
    • editor metadata

    The command is executed without shell expansion and does not
    incorporate user input, making it safe to run via subprocess.
    """
    result = subprocess.run(
        ["git", "ls-files"],  # noqa: S607
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    return [repo_root / line for line in result.stdout.splitlines()]


def compute_text_sha256(text: str) -> str:
    """
    Compute SHA256 of a text block.

    Parameters
    ----------
    text : str
        Input text to hash.

    Returns
    -------
    str
        SHA256 hexadecimal digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_sha256(path: Path) -> str:
    """
    Compute the SHA256 hash of a file.

    Parameters
    ----------
    path : Path
        Path to the file whose hash must be computed.

    Returns
    -------
    str
        Hexadecimal SHA256 digest.

    Notes
    -----
    The file is read in binary mode using fixed-size blocks to avoid
    excessive memory usage on large files.
    """
    hasher = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            hasher.update(block)

    return hasher.hexdigest()


def build_repository_tree(root: Path) -> list[str]:
    """
    Construct a textual representation of the repository directory tree.

    Parameters
    ----------
    root : Path
        Root directory of the repository.

    Returns
    -------
    list[str]
        Lines representing the directory tree structure.

    Notes
    -----
    The tree is sorted lexicographically to ensure deterministic output.
    """
    lines: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude git internal directory
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_TREE_DIRS]
        dirnames.sort()
        filenames.sort()
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts)

        indent = "    " * depth
        name = rel.name if rel.parts else root.name

        lines.append(f"{indent}{name}/")

        for fname in filenames:
            rel = (Path(dirpath) / fname).relative_to(root)
            lines.append(f"{indent}    {rel.as_posix()}")

    return lines


def list_python_files(repo_root: Path) -> list[Path]:
    """
    Enumerate Python files tracked by git within the audit scope.

    Parameters
    ----------
    repo_root : Path
        Repository root directory.

    Returns
    -------
    list[Path]
        Sorted list of Python files belonging to the audit scope.

    Notes
    -----
    Only Python files that are both:

    • tracked by git
    • located under src/fontshow/, tests/, scripts/ or githooks/

    are included.
    """
    tracked = git_tracked_files(repo_root)

    allowed_prefixes = (
        ("src", "fontshow"),
        ("tests",),
        ("scripts",),
        (".githooks",),
    )

    files = [
        path
        for path in tracked
        if path.suffix == ".py"
        and any(
            path.relative_to(repo_root).parts[: len(prefix)] == prefix
            for prefix in allowed_prefixes
        )
    ]

    return sorted(files)


def extract_function_inventory(path: Path) -> list[tuple[int, str]]:
    """
    Extract function definition lines from a Python source file.

    Parameters
    ----------
    path : Path
        Python file to analyze.

    Returns
    -------
    list[tuple[int, str]]
        list of tuples containing:

        • line number
        • exact function definition line

    Notes
    -----
    Detection uses a textual regular expression matching both
    ``def`` and ``async def`` declarations.

    The inventory includes:

    • module-level functions
    • class methods
    • nested functions
    • async functions
    """
    results: list[tuple[int, str]] = []

    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines, start=1):
        if FUNC_PATTERN.match(line):
            results.append((i, line.rstrip()))

    return results


def generate_report(repo_root: Path, output: Path) -> None:
    """
    Generate the bootstrap audit report.

    Parameters
    ----------
    repo_root : Path
        Root directory of the repository to analyze.

    output : Path
        Destination file for the generated report.

    Returns
    -------
    None

    Notes
    -----
    The report contains the following sections:

    1. Repository tree
    2. Python file list
    3. SHA256 baseline
    4. FILE AUDIT ORDER
    5. Frozen function inventory
    """
    py_files = list_python_files(repo_root)

    commit = git_commit_hash(repo_root)
    clean = git_is_clean(repo_root)
    blob_ok = verify_git_blobs(repo_root)

    lines: list[str] = []

    lines.append("BOOTSTRAP AUDIT REPORT\n")
    lines.append("======================\n\n")

    lines.append("GIT REPOSITORY STATE\n")
    lines.append("--------------------\n")
    lines.append(f"commit: {commit}\n")
    lines.append(f"working_tree_clean: {clean}\n")
    lines.append(f"blob_consistency: {blob_ok}\n")

    if not clean:
        lines.append("WARNING: repository contains uncommitted changes\n")

    if not blob_ok:
        lines.append("WARNING: working tree differs from commit blob hashes\n")

    lines.append("\n")

    lines.append("REPOSITORY TREE\n")
    lines.append("---------------\n")
    for line in build_repository_tree(repo_root):
        lines.append(line + "\n")

    lines.append("\nPYTHON FILE LIST\n")
    lines.append("----------------\n")
    for p in py_files:
        lines.append(p.relative_to(repo_root).as_posix() + "\n")

    lines.append("\nSHA256 BASELINE\n")
    lines.append("---------------\n")
    for p in py_files:
        h = compute_sha256(p)
        lines.append(f"{p.relative_to(repo_root).as_posix()}  {h}\n")

    lines.append("\nFILE AUDIT ORDER\n")
    lines.append("----------------\n")
    for p in py_files:
        lines.append(p.relative_to(repo_root).as_posix() + "\n")

    lines.append("\nFUNCTION INVENTORY\n")
    lines.append("------------------\n")

    for p in py_files:
        rel = p.relative_to(repo_root).as_posix()
        lines.append(f"\n{rel}\n")

        for lineno, line in extract_function_inventory(p):
            lines.append(f"{lineno}:{line}\n")

    report_body = "".join(lines)

    checksum = compute_text_sha256(report_body)

    lines.append("\nBOOTSTRAP CHECKSUM\n")
    lines.append("------------------\n")
    lines.append(f"report_sha256: {checksum}\n")

    with output.open("w", encoding="utf-8") as out:
        out.write("".join(lines))


def main() -> None:
    """
    Entry point for the bootstrap report generator.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    The script must be executed from the repository root directory.
    The output file ``bootstrap_audit_report.txt`` will be created
    in the current working directory.
    """
    repo_root = Path.cwd()
    output = repo_root / "bootstrap_audit_report.txt"

    generate_report(repo_root, output)

    print(f"Bootstrap report written to: {output}")


if __name__ == "__main__":
    main()
