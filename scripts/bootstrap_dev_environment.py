#!python
"""
Bootstrap the repository-local development environment.

This maintenance script prepares a fresh clone for local development by
creating the project virtual environment, installing the editable package
with development dependencies, and applying repository-local Git
configuration required by Fontshow.

Responsibilities
----------------
- Create the repository virtual environment under ``.venv``.
- Upgrade baseline packaging tools inside the virtual environment.
- Install Fontshow in editable mode with development dependencies.
- Apply repository-local Git configuration and sanctioned aliases.
- Optionally run the repository validation surface after setup.

Design principles
-----------------
Bootstrap behavior must be explicit, deterministic, and limited to
repository-owned state. The script only configures assets that are
portable and versioned by the repository, avoiding personal shell,
editor, cloud, or credential setup.

Architectural role
------------------
This module belongs to the developer tooling layer and provides a
portable bootstrap entrypoint for contributors working from a fresh
clone.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_VENV_DIR = ".venv"
REQUIRED_REPO_MARKERS = (
    ".git",
    ".githooks",
    ".gitmessage",
    "pyproject.toml",
)


@dataclass(frozen=True)
class CommandSpec:
    """
    Represent a bootstrap subprocess invocation.

    Parameters
    ----------
    description : str
        Human-readable summary of the command purpose.
    argv : tuple[str, ...]
        Command-line arguments passed to ``subprocess.run``.
    cwd : pathlib.Path
        Working directory used when running the command.
    """

    description: str
    argv: tuple[str, ...]
    cwd: Path


@dataclass(frozen=True)
class BootstrapOptions:
    """
    Hold bootstrap execution options that shape the command plan.

    Parameters
    ----------
    venv_dir : str
        Repository-relative virtual environment directory name.
    with_docs : bool
        Whether to include documentation dependencies in the editable install.
    run_validation : bool
        Whether to append repository validation commands.
    """

    venv_dir: str
    with_docs: bool
    run_validation: bool


def fail(msg: str, *, exit_code: int = 1) -> None:
    """
    Print an error message and terminate the program.

    Parameters
    ----------
    msg : str
        Human-readable error message.
    exit_code : int, default=1
        Process exit code used when terminating.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        Always raised with the provided exit code.
    """
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(exit_code)


def resolve_executable(name: str) -> str:
    """
    Resolve an executable to an absolute path.

    Parameters
    ----------
    name : str
        Executable name to resolve via ``PATH`` lookup.

    Returns
    -------
    str
        Absolute path to the executable.

    Raises
    ------
    SystemExit
        Raised if the executable cannot be found.
    """
    resolved = shutil.which(name)
    if resolved is None:
        fail(f"Required executable not found in PATH: {name}")

    return resolved


def detect_repo_root(repo_root: Path | None = None) -> Path:
    """
    Resolve and validate the repository root directory.

    Parameters
    ----------
    repo_root : pathlib.Path or None, optional
        Explicit repository root. When omitted, the root is derived from
        the script location.

    Returns
    -------
    pathlib.Path
        Absolute repository root path.

    Raises
    ------
    SystemExit
        Raised if the directory does not look like the Fontshow
        repository root.
    """
    candidate = (
        repo_root.resolve()
        if repo_root is not None
        else Path(__file__).resolve().parents[1]
    )

    missing = [
        marker for marker in REQUIRED_REPO_MARKERS if not (candidate / marker).exists()
    ]
    if missing:
        fail(
            "Repository root validation failed. Missing expected entries: "
            + ", ".join(missing)
        )

    return candidate


def venv_executable(repo_root: Path, venv_dir: str, executable_name: str) -> Path:
    """
    Compute a virtual-environment executable path.

    Parameters
    ----------
    repo_root : pathlib.Path
        Absolute repository root path.
    venv_dir : str
        Repository-relative virtual environment directory name.
    executable_name : str
        Basename of the executable to resolve.

    Returns
    -------
    pathlib.Path
        Path to the requested virtual-environment executable.
    """
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    suffix = ".exe" if os.name == "nt" else ""
    return repo_root / venv_dir / scripts_dir / f"{executable_name}{suffix}"


def install_target(*, with_docs: bool) -> str:
    """
    Build the editable installation target string.

    Parameters
    ----------
    with_docs : bool
        Whether to include the documentation dependency group.

    Returns
    -------
    str
        Editable install target suitable for ``pip install -e``.
    """
    extras = ["dev"]
    if with_docs:
        extras.append("docs")

    return f'.[{",".join(extras)}]'


def git_alias_entries() -> list[tuple[str, str]]:
    """
    Return the repository-local Git alias contract.

    Parameters
    ----------
    None

    Returns
    -------
    list[tuple[str, str]]
        Ordered ``(config_key, config_value)`` entries to apply via
        ``git config --local``.
    """
    venv_python = ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"
    venv_pytest = ".venv/Scripts/pytest.exe" if os.name == "nt" else ".venv/bin/pytest"

    return [
        ("core.hooksPath", ".githooks"),
        ("commit.template", ".gitmessage"),
        (
            "alias.clean-artifacts",
            (
                "!f() { ROOT=$(git rev-parse --show-toplevel) || exit $?; "
                f'"$ROOT/{venv_python}" "$ROOT/scripts/clean_repo.py" "$@"; '
                "}; f"
            ),
        ),
        (
            "alias.test-coverage",
            (
                "!f() { ROOT=$(git rev-parse --show-toplevel) || exit $?; "
                f'"$ROOT/{venv_pytest}" --cov=fontshow --cov-report=term-missing "$@"; '
                "}; f"
            ),
        ),
        (
            "alias.new-decision",
            (
                "!f() { ROOT=$(git rev-parse --show-toplevel) || exit $?; "
                f'"$ROOT/{venv_python}" "$ROOT/scripts/new_decision.py" "$@"; '
                "}; f"
            ),
        ),
        (
            "alias.release-preview",
            (
                "!f() { ROOT=$(git rev-parse --show-toplevel) || exit $?; "
                f'"$ROOT/{venv_python}" "$ROOT/scripts/release_preview.py" "$@"; '
                "}; f"
            ),
        ),
        ("alias.release-audit", "!bash scripts/release_audit.sh"),
        ("alias.release-check", "!bash scripts/release_system_selfcheck.sh"),
        ("alias.rel", "!bash scripts/release_rel.sh"),
        (
            "alias.gen-boot-report",
            (
                "!f() { ROOT=$(git rev-parse --show-toplevel) || exit $?; "
                f'"$ROOT/{venv_python}" "$ROOT/scripts/generate_bootstrap_audit_report.py" "$@"; '
                "}; f"
            ),
        ),
        (
            "alias.ver-boot-report",
            (
                "!f() { ROOT=$(git rev-parse --show-toplevel) || exit $?; "
                f'"$ROOT/{venv_python}" "$ROOT/scripts/verify_bootstrap_audit_report.py" "$@"; '
                "}; f"
            ),
        ),
    ]


def build_bootstrap_commands(
    *,
    repo_root: Path,
    python_executable: str,
    git_executable: str,
    options: BootstrapOptions,
) -> list[CommandSpec]:
    """
    Build the ordered bootstrap command plan.

    Parameters
    ----------
    repo_root : pathlib.Path
        Absolute repository root path.
    python_executable : str
        Absolute path to the Python interpreter used to create the
        virtual environment.
    git_executable : str
        Absolute path to the Git executable used for local config.
    options : BootstrapOptions
        Bootstrap options controlling virtual-environment placement,
        optional dependency groups, and validation behavior.

    Returns
    -------
    list[CommandSpec]
        Ordered command plan for the bootstrap workflow.
    """
    venv_path = repo_root / options.venv_dir
    venv_python = venv_executable(repo_root, options.venv_dir, "python")
    venv_pip = venv_executable(repo_root, options.venv_dir, "pip")
    venv_pre_commit = venv_executable(repo_root, options.venv_dir, "pre-commit")
    venv_pytest = venv_executable(repo_root, options.venv_dir, "pytest")

    commands = [
        CommandSpec(
            description=f"Create or refresh virtual environment at {venv_path}",
            argv=(python_executable, "-m", "venv", str(venv_path)),
            cwd=repo_root,
        ),
        CommandSpec(
            description="Upgrade pip, setuptools, and wheel in the virtual environment",
            argv=(
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
                "setuptools",
                "wheel",
            ),
            cwd=repo_root,
        ),
        CommandSpec(
            description="Install Fontshow in editable mode with development dependencies",
            argv=(
                str(venv_pip),
                "install",
                "-e",
                install_target(with_docs=options.with_docs),
            ),
            cwd=repo_root,
        ),
        CommandSpec(
            description="Verify installed package requirements",
            argv=(str(venv_python), "-m", "pip", "check"),
            cwd=repo_root,
        ),
    ]

    for key, value in git_alias_entries():
        commands.append(
            CommandSpec(
                description=f"Apply local Git config: {key}",
                argv=(git_executable, "config", "--local", key, value),
                cwd=repo_root,
            )
        )

    if options.run_validation:
        commands.extend(
            [
                CommandSpec(
                    description="Run repository validation (pre-commit)",
                    argv=(str(venv_pre_commit), "run", "--all-files"),
                    cwd=repo_root,
                ),
                CommandSpec(
                    description="Run repository validation (pytest)",
                    argv=(str(venv_pytest), "-q"),
                    cwd=repo_root,
                ),
            ]
        )

    return commands


def render_command(command: CommandSpec) -> str:
    """
    Render a command plan entry for user-readable output.

    Parameters
    ----------
    command : CommandSpec
        Command specification to render.

    Returns
    -------
    str
        Shell-quoted command line.
    """
    return " ".join(shlex.quote(arg) for arg in command.argv)


def run_plan(commands: list[CommandSpec], *, dry_run: bool) -> None:
    """
    Execute or print the bootstrap plan.

    Parameters
    ----------
    commands : list[CommandSpec]
        Ordered bootstrap command plan.
    dry_run : bool
        When ``True``, print commands without executing them.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        Raised if any subprocess exits with a non-zero status code.
    """
    for command in commands:
        print(f"==> {command.description}")
        print(f"    {render_command(command)}")

        if dry_run:
            continue

        try:
            subprocess.run(command.argv, cwd=command.cwd, check=True)
        except subprocess.CalledProcessError as exc:
            fail(
                f"Bootstrap step failed with exit code {exc.returncode}: "
                f"{render_command(command)}"
            )


def main(argv: list[str] | None = None) -> int:
    """
    Bootstrap the local repository development environment.

    Parameters
    ----------
    argv : list[str] or None, optional
        Command-line arguments to parse. When omitted, arguments are
        read from ``sys.argv``.

    Returns
    -------
    int
        Exit status code. Returns ``0`` on success.
    """
    parser = argparse.ArgumentParser(
        prog="bootstrap-dev-environment",
        description="Create .venv, install dev dependencies, and configure local Git state.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root to bootstrap (default: infer from script location)",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter used to create the virtual environment",
    )
    parser.add_argument(
        "--venv-dir",
        default=DEFAULT_VENV_DIR,
        help="Repository-relative virtual environment directory (default: .venv)",
    )
    parser.add_argument(
        "--with-docs",
        action="store_true",
        help="Install documentation dependencies in addition to dev dependencies",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip 'pre-commit run --all-files' and 'pytest -q' after setup",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the bootstrap plan without executing it",
    )

    args = parser.parse_args(argv)

    repo_root = detect_repo_root(args.repo_root)
    python_executable = args.python
    if not Path(python_executable).is_absolute():
        python_executable = resolve_executable(python_executable)
    git_executable = resolve_executable("git")

    commands = build_bootstrap_commands(
        repo_root=repo_root,
        python_executable=python_executable,
        git_executable=git_executable,
        options=BootstrapOptions(
            venv_dir=args.venv_dir,
            with_docs=args.with_docs,
            run_validation=not args.skip_validation,
        ),
    )
    run_plan(commands, dry_run=args.dry_run)

    print("\nBootstrap completed successfully.")
    if args.skip_validation:
        print("Validation was skipped by request.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
