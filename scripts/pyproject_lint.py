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
    print(f"[ERR ] {msg}", file=sys.stderr)
    raise LintError(msg)


def ok(msg: str) -> None:
    print(f"[OK  ] {msg}")


# ---------------------------------------------------------------------------
# Core checks
# ---------------------------------------------------------------------------


def check_project_table(data: dict[str, Any]) -> None:
    project = data.get("project")
    if not isinstance(project, dict):
        fail("Missing [project] table")

    required = ["name", "requires-python"]
    for field in required:
        if field not in project:
            fail(f"[project] missing required field: {field}")

    ok("[project] required fields present")


def check_license_rules(data: dict[str, Any]) -> None:
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
    build = data.get("build-system")
    if not isinstance(build, dict):
        fail("Missing [build-system]")

    requires = build.get("requires")
    backend = build.get("build-backend")

    if not requires or not isinstance(requires, list):
        fail("[build-system.requires] must be a list")

    if not backend or not isinstance(backend, str):
        fail("[build-system.build-backend] missing or invalid")

    ok("build-system valid")


def check_tooling(data: dict[str, Any]) -> None:
    tool = data.get("tool", {})

    if "ruff" not in tool:
        fail("Missing [tool.ruff] configuration")

    if "mypy" not in tool:
        fail("Missing [tool.mypy] configuration")

    ok("tooling configuration present")


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------


def main() -> int:
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
