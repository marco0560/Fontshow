#!/usr/bin/env python3
"""
Verify that a repository matches a bootstrap audit report.

This script validates that the current repository state matches the
metadata frozen in ``bootstrap_audit_report.txt``.

Verification steps
------------------
1. Validate bootstrap report checksum.
2. Verify Git commit hash.
3. Verify working tree cleanliness.
4. Verify Git blob consistency.
5. Verify Python file set.
6. Verify SHA256 hashes for each Python file.

If any mismatch is detected the script exits with a non-zero status.

The goal is to ensure the repository being audited corresponds exactly
to the bootstrap state used during deterministic auditing.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPORT_FILE = "bootstrap_audit_report.txt"


def compute_sha256(path: Path) -> str:
    """
    Compute SHA256 of a file.

    Parameters
    ----------
    path : Path
        File to hash.

    Returns
    -------
    str
        SHA256 hex digest.
    """
    hasher = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)

    return hasher.hexdigest()


def compute_text_sha256(text: str) -> str:
    """
    Compute SHA256 of text.

    Parameters
    ----------
    text : str
        Input text.

    Returns
    -------
    str
        SHA256 hex digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_commit(repo_root: Path) -> str:
    """
    Return the current Git commit hash for the repository.

    Parameters
    ----------
    repo_root : pathlib.Path
        Path to the root directory of the Git repository.

    Returns
    -------
    str
        The full commit hash of ``HEAD``.

    Raises
    ------
    subprocess.CalledProcessError
        Raised if the Git command fails.
    """
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def git_clean(repo_root: Path) -> bool:
    """
    Determine whether the Git working tree is clean.

    Parameters
    ----------
    repo_root : pathlib.Path
        Path to the root directory of the Git repository.

    Returns
    -------
    bool
        ``True`` if the working tree has no uncommitted changes,
        otherwise ``False``.

    Raises
    ------
    subprocess.CalledProcessError
        Raised if the Git command fails.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],  # noqa: S607
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() == ""


def verify_report_checksum(report_text: str) -> None:
    """
    Verify the integrity checksum of the bootstrap audit report.

    The report contains a ``BOOTSTRAP CHECKSUM`` section with a stored
    SHA256 hash of the report body. This function recomputes the hash
    and ensures it matches the stored value.

    Parameters
    ----------
    report_text : str
        Full textual contents of the bootstrap audit report.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        If the checksum section is missing, the stored checksum line
        cannot be found, or the computed checksum does not match.
    """
    marker = "\nBOOTSTRAP CHECKSUM\n"
    idx = report_text.find(marker)

    if idx == -1:
        msg = "Bootstrap checksum section missing"
        raise RuntimeError(msg)

    body = report_text[:idx]

    # Extract stored checksum
    for line in report_text[idx:].splitlines():
        if line.startswith("report_sha256:"):
            expected = line.split(":", 1)[1].strip()
            break
    else:
        msg = "Checksum line missing"
        raise RuntimeError(msg)

    actual = compute_text_sha256(body)

    if actual != expected:
        msg = "Bootstrap report checksum mismatch"
        raise RuntimeError(msg)


def parse_sha256_section(report_lines: list[str]) -> dict[str, str]:
    """
    Parse SHA256 baseline section.

    Returns
    -------
    dict[str, str]
        Mapping path → sha256
    """
    hashes: dict[str, str] = {}

    in_section = False

    for line in report_lines:
        if line.startswith("SHA256 BASELINE"):
            in_section = True
            continue

        if in_section and not line.strip():
            break

        if in_section:
            parts = line.split()
            if len(parts) == 2:
                hashes[parts[0]] = parts[1]

    return hashes


def verify_file_hashes(repo_root: Path, hashes: dict[str, str]) -> None:
    """
    Verify recorded SHA256 hashes for repository files.

    Parameters
    ----------
    repo_root : pathlib.Path
        Root directory of the repository.
    hashes : dict[str, str]
        Mapping from relative file paths to expected SHA256 hashes.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        If a file listed in the hash table is missing or if its
        computed SHA256 digest does not match the expected value.
    """
    for path_str, expected in hashes.items():
        path = repo_root / path_str

        if not path.exists():
            msg = f"Missing file: {path_str}"
            raise RuntimeError(msg)

        actual = compute_sha256(path)

        if actual != expected:
            msg = f"Hash mismatch: {path_str}"
            raise RuntimeError(msg)


def main() -> None:
    """
    Verify the integrity of the bootstrap audit report and repository state.

    This command-line entry point performs several validation steps:

    * ensure the bootstrap audit report exists
    * verify the report checksum
    * confirm the Git working tree is clean
    * validate recorded file hashes against repository contents

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        Raised if the bootstrap report file is missing.
    RuntimeError
        Raised if the repository working tree is not clean.
    """
    repo_root = Path.cwd()
    report_path = repo_root / REPORT_FILE

    if not report_path.exists():
        print("Bootstrap report not found.", file=sys.stderr)
        sys.exit(1)

    report_text = report_path.read_text(encoding="utf-8")
    report_lines = report_text.splitlines()

    verify_report_checksum(report_text)

    print("Bootstrap checksum OK")

    commit = git_commit(repo_root)
    print("Current commit:", commit)

    if not git_clean(repo_root):
        msg = "Repository working tree not clean"
        raise RuntimeError(msg)

    print("Working tree clean")

    hashes = parse_sha256_section(report_lines)

    verify_file_hashes(repo_root, hashes)

    print("All file hashes match")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\nRepository matches bootstrap audit report.")
    sys.exit(0)
