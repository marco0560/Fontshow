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
    assert resolved is not None

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


def uv_sync_command(*, with_docs: bool) -> tuple[str, ...]:
    """
    Build the uv sync command for the repository environment.

    Parameters
    ----------
    with_docs : bool
        Whether to include the documentation dependency group.

    Returns
    -------
    tuple[str, ...]
        Command suitable for ``uv sync`` execution.
    """
    command = ["uv", "sync", "--extra", "dev"]

    if with_docs:
        command.extend(["--extra", "docs"])

    return tuple(command)


def git_local_config_entries() -> list[tuple[str, str]]:
    """
    Return the repository-local Git configuration contract.

    Parameters
    ----------
    None

    Returns
    -------
    list[tuple[str, str]]
        Ordered ``(config_key, config_value)`` entries to apply via
        ``git config --local``.
    """
    return [
        ("core.repositoryformatversion", "0"),
        ("core.filemode", "true"),
        ("core.bare", "false"),
        ("core.logallrefupdates", "true"),
        ("core.hooksPath", ".githooks"),
        ("remote.origin.url", "git@github.com:marco0560/Fontshow.git"),
        ("remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"),
        ("init.defaultBranch", "main"),
        ("branch.main.remote", "origin"),
        ("branch.main.merge", "refs/heads/main"),
        ("branch.main.vscode-merge-base", "origin/main"),
        ("commit.template", ".gitmessage"),
        ("commit.gpgsign", "true"),
        ("commit.verbose", "true"),
        ("alias.st", "status"),
        ("alias.co", "checkout"),
        ("alias.br", "branch"),
        ("alias.ci", "commit"),
        ("alias.lg", "log --oneline --graph --decorate -50"),
        (
            "alias.check",
            "!uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run python -m pytest -q",
        ),
        (
            "alias.fix",
            "!uv run ruff check . --fix && uv run ruff format .",
        ),
        (
            "alias.clean-repo",
            """!f() { uv run python scripts/clean_repo.py "$@"; }; f""",
        ),
        (
            "alias.test-coverage",
            """!f() { uv run python -m pytest --cov=fontshow --cov-report=term-missing "$@"; }; f""",
        ),
        (
            "alias.test-html",
            "!uv run python -m pytest --cov=fontshow --cov-report=html && xdg-open htmlcov/index.html",
        ),
        (
            "alias.new-decision",
            """!f() { uv run python scripts/new_decision.py "$@"; }; f""",
        ),
        (
            "alias.release-preview",
            """!f() { uv run python scripts/release_preview.py "$@"; }; f""",
        ),
        (
            "alias.gen-issues",
            """!f() { rm -f issues.json &> /dev/null; timeout 10s gh api graphql -f query='query {repository(owner: "marco0560", name: "Fontshow") {issues(first: 100, states: OPEN, orderBy: {field: CREATED_AT, direction: ASC}) {totalCount pageInfo {hasNextPage endCursor} nodes {number title body url state createdAt updatedAt author {login} assignees(first: 20) {nodes {login}} labels(first: 20) {nodes {name}} milestone {number title} comments {totalCount}}}}}' > issues.json; }; f""",
        ),
        (
            "alias.gen-miles",
            """!f() { rm -f milestones.json &> /dev/null; timeout 10s gh api graphql -f query='query {repository(owner: "marco0560", name: "Fontshow") {milestones(first: 20, states: OPEN, orderBy: {field: DUE_DATE, direction: ASC}) {totalCount pageInfo {hasNextPage endCursor} nodes {number title description dueOn progressPercentage issues(first: 100) {totalCount pageInfo {hasNextPage endCursor} nodes {number title url state createdAt updatedAt labels(first: 20) { nodes {name}}}}}}}}' > milestones.json; }; f""",
        ),
        (
            "alias.txz",
            """!f(){ name="${1:-repo}"; tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT; mkdir -p "$tmp/repo"; git ls-files -z | XZ_OPT="-9e -T0" tar --null -T - -cJf "$PWD/$name.tar.xz" --transform='s,^,repo/,'; }; f""",
        ),
        (
            "alias.txz",
            """!f() { name="${1:-repo}"; tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT; mkdir -p "$tmp/repo"; { git ls-files -z; printf "%s\0" issues.json milestones.json; } | XZ_OPT="-9e -T0" tar --null -T - -cJf "$PWD/$name.tar.xz" --transform='s,^,repo/,'; }; f""",
        ),
        (
            "alias.gen-zip-common",
            """!f() { name="${1:-guidelines}"; tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT; mkdir -p "$tmp/$name"; [ -f "$HOME/OneDrive/Documenti/Fontshow/Comuni/chatgpt_guidelines.md" ] && cp -f "$HOME/OneDrive/Documenti/Fontshow/Comuni/chatgpt_guidelines.md" "$tmp/$name/"; [ -f "$HOME/OneDrive/Documenti/Fontshow/Comuni/patch_discipline.md" ] && cp -f "$HOME/OneDrive/Documenti/Fontshow/Comuni/patch_discipline.md" "$tmp/$name/"; [ -f "$HOME/OneDrive/Documenti/Fontshow/Comuni/anti-hallucination.md" ] && cp -f "$HOME/OneDrive/Documenti/Fontshow/Comuni/anti-hallucination.md" "$tmp/$name/"; XZ_OPT="-9e -T0" tar --sort=name --mtime="UTC 1970-01-01" --owner=0 --group=0 --numeric-owner -C "$tmp" -cJf "$PWD/$name.tar.xz" "$name"; }; f""",
        ),
        ("alias.safe-push", "!git fetch && git pull --ff-only && git push"),
        ("alias.release-audit", "!bash scripts/release_audit.sh"),
        (
            "alias.rel",
            "!git fetch && git pull --ff-only && bash scripts/release_rel.sh && sleep 30s && git fetch && git pull --ff-only",
        ),
        (
            "alias.re-clean",
            "!git clean-repo && git gen-issues && git gen-miles && git txz",
        ),
        (
            "alias.gen-boot-report",
            "!uv run python scripts/generate_bootstrap_audit_report.py",
        ),
        (
            "alias.ver-boot-report",
            "!uv run python scripts/verify_bootstrap_audit_report.py",
        ),
        (
            "alias.install-dev-codira",
            '!f() { uv run python ../codira/scripts/install_first_party_packages.py --python "$VIRTUAL_ENV/bin/python" --include-core --core-extra semantic; }; f',
        ),
        ("pull.ff", "only"),
        ("pull.rebase", "false"),
        ("rebase.autostash", "true"),
    ]


def build_bootstrap_commands(
    *,
    repo_root: Path,
    git_executable: str,
    options: BootstrapOptions,
) -> list[CommandSpec]:
    """
    Build the ordered bootstrap command plan.

    Parameters
    ----------
    repo_root : pathlib.Path
        Absolute repository root path.
    git_executable : str
        Absolute path to the Git executable used for local config.
    options : BootstrapOptions
        Bootstrap options controlling dependency groups and validation.

    Returns
    -------
    list[CommandSpec]
        Ordered command plan for the bootstrap workflow.
    """
    commands: list[CommandSpec] = [
        CommandSpec(
            description="Synchronize uv-managed development environment",
            argv=uv_sync_command(with_docs=options.with_docs),
            cwd=repo_root,
        ),
        CommandSpec(
            description="Verify installed package requirements",
            argv=("uv", "run", "python", "-m", "pip", "check"),
            cwd=repo_root,
        ),
    ]

    for key, value in git_local_config_entries():
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
                    description="Run repository validation (ruff)",
                    argv=("uv", "run", "ruff", "check", ".", "--fix"),
                    cwd=repo_root,
                ),
                CommandSpec(
                    description="Run repository validation (ruff format)",
                    argv=("uv", "run", "ruff", "format", "--check", "."),
                    cwd=repo_root,
                ),
                CommandSpec(
                    description="Run repository validation (mypy)",
                    argv=("uv", "run", "mypy", "src"),
                    cwd=repo_root,
                ),
                CommandSpec(
                    description="Run repository validation (pytest)",
                    argv=("uv", "run", "python", "-m", "pytest", "-q"),
                    cwd=repo_root,
                ),
                CommandSpec(
                    description="Run repository validation (pre-commit)",
                    argv=("uv", "run", "pre-commit", "run", "--all-files"),
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

    git_executable = resolve_executable("git")
    resolve_executable("uv")

    commands = build_bootstrap_commands(
        repo_root=repo_root,
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
