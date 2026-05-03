#!/usr/bin/env python3
"""
Deterministic structural lint for pyproject.toml.

Hard-fail validator for:
- PEP 621 metadata consistency
- setuptools compatibility (PEP 639 license rules)
- dependency format sanity
- tool configuration presence

No heuristics. No silent fixes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    print("ERROR: Python 3.11+ required (tomllib missing)", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LintError(Exception):
    """Hard failure in pyproject structure."""


def fail(msg: str) -> None:
    """Raise a hard-failure lint error after reporting it.

    Parameters
    ----------
    msg : str
        Error message describing the structural lint failure.

    Returns
    -------
    None

    Raises
    ------
    LintError
        Always raised after the message is emitted.
    """
    print(f"[ERR ] {msg}", file=sys.stderr)
    raise LintError(msg)


def ok(msg: str) -> None:
    """Emit a success message for a completed lint check.

    Parameters
    ----------
    msg : str
        Success message describing the completed check.

    Returns
    -------
    None
    """
    print(f"[OK  ] {msg}")


# ---------------------------------------------------------------------------
# Core checks
# ---------------------------------------------------------------------------


def check_project_table(data: dict[str, Any]) -> None:
    """Validate the required PEP 621 project metadata table.

    Parameters
    ----------
    data : dict[str, Any]
        Parsed ``pyproject.toml`` content.

    Returns
    -------
    None

    Raises
    ------
    LintError
        Raised when the project table or required fields are missing.
    """
    project = data.get("project")
    if not isinstance(project, dict):
        fail("Missing [project] table")
    assert isinstance(project, dict)

    required = ["name", "requires-python"]
    for field in required:
        if field not in project:
            fail(f"[project] missing required field: {field}")

    ok("[project] required fields present")


def check_license_rules(data: dict[str, Any]) -> None:
    """Validate mutually exclusive license metadata rules.

    Parameters
    ----------
    data : dict[str, Any]
        Parsed ``pyproject.toml`` content.

    Returns
    -------
    None

    Raises
    ------
    LintError
        Raised when license metadata violates the enforced policy.
    """
    project = data["project"]

    license_field = project.get("license")
    classifiers = project.get("classifiers", [])

    if license_field and any(c.startswith("License ::") for c in classifiers):
        fail(
            "License classifiers are forbidden when 'license' is set "
            "(PEP 639). Remove License :: classifiers."
        )

    ok("license configuration valid")


def check_dependencies(data: dict[str, Any]) -> None:
    """Validate the main dependency list structure and uniqueness.

    Parameters
    ----------
    data : dict[str, Any]
        Parsed ``pyproject.toml`` content.

    Returns
    -------
    None

    Raises
    ------
    LintError
        Raised when dependency entries are malformed or duplicated.
    """
    project = data["project"]

    deps = project.get("dependencies", [])
    if not isinstance(deps, list):
        fail("[project.dependencies] must be a list")

    seen: set[str] = set()
    for dep in deps:
        if not isinstance(dep, str):
            fail(f"Invalid dependency entry (not string): {dep}")

        name = dep.split(">=")[0].split("==")[0]
        if name in seen:
            fail(f"Duplicate dependency: {name}")
        seen.add(name)

    ok("dependencies valid")


def check_optional_dependencies(data: dict[str, Any]) -> None:
    """Validate optional dependency groups and entry types.

    Parameters
    ----------
    data : dict[str, Any]
        Parsed ``pyproject.toml`` content.

    Returns
    -------
    None

    Raises
    ------
    LintError
        Raised when optional dependency groups are malformed.
    """
    project = data["project"]
    optional = project.get("optional-dependencies", {})

    if not isinstance(optional, dict):
        fail("[project.optional-dependencies] must be a table")

    for group, deps in optional.items():
        if not isinstance(deps, list):
            fail(f"Optional group '{group}' must be a list")

        for dep in deps:
            if not isinstance(dep, str):
                fail(f"Invalid dep in [{group}]: {dep}")

    ok("optional dependencies valid")


def check_build_system(data: dict[str, Any]) -> None:
    """Validate the build-system table and required keys.

    Parameters
    ----------
    data : dict[str, Any]
        Parsed ``pyproject.toml`` content.

    Returns
    -------
    None

    Raises
    ------
    LintError
        Raised when build-system configuration is missing or invalid.
    """
    build = data.get("build-system")
    if not isinstance(build, dict):
        fail("Missing [build-system]")
    assert isinstance(build, dict)

    requires = build.get("requires")
    backend = build.get("build-backend")

    if not requires or not isinstance(requires, list):
        fail("[build-system.requires] must be a list")

    if not backend or not isinstance(backend, str):
        fail("[build-system.build-backend] missing or invalid")

    ok("build-system valid")


def check_tooling(data: dict[str, Any]) -> None:
    """Validate presence of required tool configuration blocks.

    Parameters
    ----------
    data : dict[str, Any]
        Parsed ``pyproject.toml`` content.

    Returns
    -------
    None

    Raises
    ------
    LintError
        Raised when required tool sections are missing.
    """
    tool = data.get("tool", {})
    if not isinstance(tool, dict):
        fail("Missing [tool] configuration")
    assert isinstance(tool, dict)

    if "ruff" not in tool:
        fail("Missing [tool.ruff] configuration")

    if "mypy" not in tool:
        fail("Missing [tool.mypy] configuration")

    ok("tooling configuration present")


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------


def main() -> int:
    """Run the deterministic structural lint for ``pyproject.toml``.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Process exit status code for the lint run.

    Raises
    ------
    LintError
        Raised when the target file is missing or validation fails.
    """
    path = Path("pyproject.toml")

    if not path.exists():
        fail("pyproject.toml not found")

    with path.open("rb") as f:
        data = tomllib.load(f)

    check_project_table(data)
    check_license_rules(data)
    check_dependencies(data)
    check_optional_dependencies(data)
    check_build_system(data)
    check_tooling(data)

    ok("pyproject.toml structural lint PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LintError:
        raise SystemExit(1) from None
