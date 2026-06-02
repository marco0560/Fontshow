"""Verify the repository validation helper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_repo.py"
_SPEC = importlib.util.spec_from_file_location("validate_repo", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
validate_repo = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = validate_repo
_SPEC.loader.exec_module(validate_repo)


def test_validation_steps_run_tests_under_coverage() -> None:
    """
    Ensure the standard validator enforces coverage-backed test execution.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    expected_steps = (
        validate_repo.ValidationStep("ruff", "ruff", ("check", ".")),
        validate_repo.ValidationStep("ruff-format", "ruff", ("format", "--check", ".")),
        validate_repo.ValidationStep("mypy", "mypy", ("src",)),
        validate_repo.ValidationStep(
            "pre-commit-noncode", "pre-commit-noncode", ("run", "--all-files")
        ),
        validate_repo.ValidationStep(
            "coverage", "coverage", ("run", "-m", "pytest", "-q", "tests")
        ),
        validate_repo.ValidationStep(
            "coverage-json", "coverage", ("json", "-o", ".coverage-report.json")
        ),
        validate_repo.ValidationStep(
            "coverage-summary", "python", ("scripts/coverage_summary.py",)
        ),
    )

    assert expected_steps == validate_repo.VALIDATION_STEPS


def test_build_validation_commands_delegates_coverage_steps() -> None:
    """
    Ensure generated commands preserve the coverage validation sequence.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    commands = validate_repo.build_validation_commands(python="/tmp/python")

    assert commands[-3:] == (
        (
            "/tmp/python",
            str(validate_repo.RUN_REPO_TOOL),
            "coverage",
            "run",
            "-m",
            "pytest",
            "-q",
            "tests",
        ),
        (
            "/tmp/python",
            str(validate_repo.RUN_REPO_TOOL),
            "coverage",
            "json",
            "-o",
            ".coverage-report.json",
        ),
        (
            "/tmp/python",
            str(validate_repo.RUN_REPO_TOOL),
            "python",
            "scripts/coverage_summary.py",
        ),
    )
