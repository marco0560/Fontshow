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
BOOTSTRAP_SETUPTOOLS_SPEC = "setuptools<82"
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
    create_venv : bool
        Whether to create or refresh the repository virtual environment.
    """

    venv_dir: str
    with_docs: bool
    run_validation: bool
    create_venv: bool


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


def select_bootstrap_python(
    requested_python: str, *, repo_root: Path, venv_dir: str
) -> str:
    """
    Choose the interpreter used to create the target virtual environment.

    Parameters
    ----------
    requested_python : str
        Interpreter path or executable name requested on the command line.
    repo_root : pathlib.Path
        Absolute repository root path.
    venv_dir : str
        Repository-relative virtual environment directory name.

    Returns
    -------
    str
        Interpreter path or executable name to use for ``python -m venv``.

    Notes
    -----
    When bootstrap runs from the target repository virtual environment and
    ``--python`` is left at its default value, the active virtual-environment
    interpreter cannot safely recreate itself. In that case bootstrap falls
    back to the base interpreter reported by ``sys._base_executable``.
    """
    target_venv = (repo_root / venv_dir).resolve()

    try:
        requested_path = Path(requested_python).resolve()
    except OSError:
        return requested_python

    if not requested_path.is_absolute():
        return requested_python

    try:
        requested_path.relative_to(target_venv)
    except ValueError:
        return requested_python

    base_executable = getattr(sys, "_base_executable", "")
    if not base_executable:
        return requested_python

    return str(Path(base_executable).resolve())


def target_venv_is_active(*, repo_root: Path, venv_dir: str) -> bool:
    """
    Report whether bootstrap is running from the target repository virtual environment.

    Parameters
    ----------
    repo_root : pathlib.Path
        Absolute repository root path.
    venv_dir : str
        Repository-relative virtual environment directory name.

    Returns
    -------
    bool
        ``True`` when the active interpreter lives under the target virtual
        environment directory, otherwise ``False``.
    """
    target_venv = (repo_root / venv_dir).resolve()
    active_python = Path(sys.executable).resolve()

    try:
        active_python.relative_to(target_venv)
    except ValueError:
        return False

    return True


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
            "!bash -lc 'source .venv/bin/activate && black --check . && ruff check . && mypy . && pytest -q'",
        ),
        ("alias.fix", "!ruff check . --fix"),
        (
            "alias.clean-repo",
            """!f() { python scripts/clean_repo.py "$@"; }; f""",
        ),
        (
            "alias.test-coverage",
            """!f() { pytest --cov=fontshow --cov-report=term-missing "$@"; }; f""",
        ),
        (
            "alias.test-html",
            "!pytest --cov=fontshow --cov-report=html && xdg-open htmlcov/index.html",
        ),
        (
            "alias.new-decision",
            """!f() { python scripts/new_decision.py "$@"; }; f""",
        ),
        (
            "alias.release-preview",
            """!f() { python scripts/release_preview.py "$@"; }; f""",
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
            "!git clean-repo && git gen-issues && git gen-miles && git gen-zip-repo",
        ),
        (
            "alias.gen-boot-report",
            "!python scripts/generate_bootstrap_audit_report.py",
        ),
        (
            "alias.ver-boot-report",
            "!python scripts/verify_bootstrap_audit_report.py",
        ),
        (
            "alias.install-dev-codira",
            '!python ../codira/scripts/install_first_party_packages.py --python "$VIRTUAL_ENV/bin/python" --include-core --core-extra semantic --include-bundle',
        ),
        ("pull.ff", "only"),
        ("pull.rebase", "false"),
        ("rebase.autostash", "true"),
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
            description="Upgrade pip, setuptools, and wheel in the virtual environment",
            argv=(
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
                BOOTSTRAP_SETUPTOOLS_SPEC,
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

    if options.create_venv:
        commands.insert(
            0,
            CommandSpec(
                description=f"Create or refresh virtual environment at {venv_path}",
                argv=(python_executable, "-m", "venv", str(venv_path)),
                cwd=repo_root,
            ),
        )

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
    python_executable = select_bootstrap_python(
        args.python,
        repo_root=repo_root,
        venv_dir=args.venv_dir,
    )
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
            create_venv=not target_venv_is_active(
                repo_root=repo_root,
                venv_dir=args.venv_dir,
            ),
        ),
    )
    run_plan(commands, dry_run=args.dry_run)

    print("\nBootstrap completed successfully.")
    if args.skip_validation:
        print("Validation was skipped by request.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
