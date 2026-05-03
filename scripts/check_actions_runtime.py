#!/usr/bin/env python3
"""
GitHub Actions runtime compatibility scanner.

This tool analyzes GitHub workflow files and determines whether
the actions used are likely compatible with the upcoming Node.js
24 runtime migration for GitHub Actions.

The script performs two analyses:

1. Local scan
   Detects actions used in workflow YAML files.

2. Remote scan
   Queries the GitHub API to retrieve the latest release version
   of each action repository and compares it with the version used
   locally.

This helps identify actions that may still rely on deprecated
Node.js runtimes (e.g. Node 20).

The tool is deterministic and safe to run offline except for the
optional GitHub API queries.

Examples
--------
Run the scanner from repository root:

>>> python scripts/check_actions_runtime.py

Environment variables
---------------------
GITHUB_TOKEN : str, optional
    GitHub token used to avoid low API rate limits.

Notes
-----
The script intentionally avoids deep heuristics about Node runtime
internals and instead uses conservative signals:

* action major version used locally
* latest release available upstream

This prevents false claims about runtime compatibility.

Returns
-------
None
    Prints a diagnostic report to stdout.
"""

from __future__ import annotations

import importlib
import os
import pathlib
import re
import sys
from typing import Any, cast

requests = cast("Any", importlib.import_module("requests"))

WORKFLOW_DIR = pathlib.Path(".github/workflows")

USES_RE = re.compile(r"uses:\s*([^@]+)@v?(\d+)")

# Minimum versions known to support Node 24
NODE24_READY: dict[str, int] = {
    "actions/checkout": 5,
    "actions/setup-python": 6,
    "actions/setup-node": 6,
    "actions/upload-artifact": 6,
}

CACHE: dict[str, int | None] = {}


def scan_file(path: pathlib.Path) -> set[tuple[str, int]]:
    """
    Extract GitHub Actions usage from a workflow file.

    Parameters
    ----------
    path : pathlib.Path
        Workflow YAML file.

    Returns
    -------
    set[tuple[str, int]]
        Unique pairs of action repository and major version.

    Examples
    --------
    >>> scan_file(Path(".github/workflows/ci.yml"))
    {('actions/checkout', 5), ('actions/setup-python', 6)}
    """
    found: set[tuple[str, int]] = set()

    for line in path.read_text().splitlines():
        m = USES_RE.search(line)
        if m:
            action = m.group(1)
            version = int(m.group(2))
            found.add((action, version))

    return found


def scan_local() -> dict[str, set[tuple[str, int]]]:
    """
    Scan all workflows in the repository.

    Parameters
    ----------
    None

    Returns
    -------
    dict[str, set[tuple[str, int]]]
        Mapping of workflow file → actions used.
    """
    results: dict[str, set[tuple[str, int]]] = {}

    if not WORKFLOW_DIR.exists():
        print("No .github/workflows directory found.")
        sys.exit(1)

    for wf in sorted(WORKFLOW_DIR.glob("*.yml")):
        results[str(wf)] = scan_file(wf)

    return results


def get_latest_major(action: str) -> int | None:
    """
    Retrieve latest major release of a GitHub action.

    Parameters
    ----------
    action : str
        Action repository name (e.g. "actions/checkout").

    Returns
    -------
    int or None
        Latest major version if detectable.

    Notes
    -----
    Uses GitHub REST API endpoint:

    https://api.github.com/repos/{owner}/{repo}/releases/latest
    """
    if action in CACHE:
        return CACHE[action]

    url = f"https://api.github.com/repos/{action}/releases/latest"

    headers = {}
    token = os.getenv("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()
        tag = data.get("tag_name", "")

        m = re.search(r"v(\d+)", tag)
        if m:
            result = int(m.group(1))
            CACHE[action] = result
            return result

    except (requests.exceptions.RequestException, ValueError):
        CACHE[action] = None
        return None
    return None


def evaluate_action(action: str, version: int) -> str:
    """
    Evaluate Node 24 compatibility status.

    Parameters
    ----------
    action : str
        Action repository identifier.
    version : int
        Major version used locally.

    Returns
    -------
    str
        Diagnostic message describing compatibility.
    """
    if action in NODE24_READY:
        required = NODE24_READY[action]

        if version >= required:
            return "✓ Node 24 compatible"
        return f"⚠ upgrade to v{required}+"

    latest = get_latest_major(action)

    if latest is None:
        return "? unknown runtime (manual check)"

    if version < latest:
        return f"⚠ newer major available: v{latest}"

    return "✓ latest version"


def print_report(local_results: dict[str, set[tuple[str, int]]]) -> None:
    """
    Print human-readable compatibility report.

    Parameters
    ----------
    local_results : dict[str, set[tuple[str, int]]]
        Output of ``scan_local()``.

    Returns
    -------
    None
    """
    print("\nGitHub Actions runtime compatibility report\n")

    for wf, actions in local_results.items():
        print(f"Workflow: {wf}")

        for action, version in sorted(actions):
            status = evaluate_action(action, version)

            print(f"  {action}@v{version:<2}  {status}")

        print()


def main() -> None:
    """
    Entry point.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    local = scan_local()
    print_report(local)


if __name__ == "__main__":
    main()
