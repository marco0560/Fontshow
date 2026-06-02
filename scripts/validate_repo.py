#!/usr/bin/env python3
"""Run the standard repository validation through safe tool-state routing.

Responsibilities
----------------
- Provide one obvious command for local validation.
- Delegate all cache and temporary directory handling to
  ``scripts/run_repo_tool.py``.
- Stop at the first failing validation step and return its exit status.

Design principles
-----------------
This wrapper must not create repository-local cache or temporary directories.
The lower-level tool runner owns that policy.

Architectural role
------------------
This module belongs to the **developer tooling layer** and composes the
repository-owned tool runner.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_REPO_TOOL = REPO_ROOT / "scripts" / "run_repo_tool.py"


@dataclass(frozen=True)
class ValidationStep:
    """One validation command routed through the repository tool runner."""

    name: str
    tool: str
    args: tuple[str, ...]


VALIDATION_STEPS: tuple[ValidationStep, ...] = (
    ValidationStep("ruff", "ruff", ("check", ".")),
    ValidationStep("ruff-format", "ruff", ("format", "--check", ".")),
    ValidationStep("mypy", "mypy", ("src",)),
    ValidationStep("pre-commit-noncode", "pre-commit-noncode", ("run", "--all-files")),
    ValidationStep("coverage", "coverage", ("run", "-m", "pytest", "-q", "tests")),
    ValidationStep(
        "coverage-json",
        "coverage",
        (
            "json",
            "-o",
            ".coverage-report.json",
        ),
    ),
    ValidationStep(
        "coverage-summary",
        "python",
        ("scripts/coverage_summary.py",),
    ),
)


def build_parser() -> argparse.ArgumentParser:
    """
    Build the command-line parser for the repository validator.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.ArgumentParser
        Parser for repository validation options.
    """

    parser = argparse.ArgumentParser(
        description="Run the standard repository validation sequence.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print delegated validation commands without executing them.",
    )
    return parser


def build_validation_commands(
    *, python: str = sys.executable
) -> tuple[tuple[str, ...], ...]:
    """
    Build the standard validation commands.

    Parameters
    ----------
    python : str, optional
        Python executable used to invoke ``scripts/run_repo_tool.py``.

    Returns
    -------
    tuple[tuple[str, ...], ...]
        Ordered command vectors for the validation steps.
    """

    return tuple(
        (python, str(RUN_REPO_TOOL), step.tool, *step.args) for step in VALIDATION_STEPS
    )


def run_validation(commands: tuple[tuple[str, ...], ...] | None = None) -> int:
    """
    Execute validation commands in order.

    Parameters
    ----------
    commands : tuple[tuple[str, ...], ...] | None, optional
        Explicit command vectors to run. When omitted, the standard validation
        commands are built with the current Python executable.

    Returns
    -------
    int
        Zero when all validation steps pass, otherwise the first non-zero child
        exit status.
    """

    selected_commands = (
        commands if commands is not None else build_validation_commands()
    )
    for command in selected_commands:
        completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def render_validation_commands(commands: tuple[tuple[str, ...], ...]) -> str:
    """
    Render delegated validation commands for dry-run output.

    Parameters
    ----------
    commands : tuple[tuple[str, ...], ...]
        Command vectors that would be executed by the validator.

    Returns
    -------
    str
        One shell-quoted command per line.
    """

    return "\n".join(shlex.join(command) for command in commands)


def main(argv: Sequence[str] | None = None) -> int:
    """
    Run the standard repository validation sequence.

    Parameters
    ----------
    argv : collections.abc.Sequence[str] | None, optional
        Explicit command-line arguments. When omitted, ``sys.argv[1:]`` is
        used.

    Returns
    -------
    int
        Validation exit status.
    """

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    commands = build_validation_commands()
    if args.dry_run:
        print(render_validation_commands(commands))
        return 0
    return run_validation(commands)


if __name__ == "__main__":
    raise SystemExit(main())
