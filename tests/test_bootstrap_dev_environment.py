"""Verify the development bootstrap maintenance script."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_dev_environment.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "bootstrap_dev_environment", _SCRIPT_PATH
)
assert _SPEC is not None and _SPEC.loader is not None
bootstrap_dev_environment = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = bootstrap_dev_environment
_SPEC.loader.exec_module(bootstrap_dev_environment)


def test_uv_sync_command_tracks_requested_dependency_groups() -> None:
    """
    Ensure uv dependency-group synchronization remains explicit and deterministic.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert bootstrap_dev_environment.uv_sync_command(with_docs=False) == (
        "uv",
        "sync",
        "--group",
        "dev",
    )

    assert bootstrap_dev_environment.uv_sync_command(with_docs=True) == (
        "uv",
        "sync",
        "--group",
        "dev",
        "--extra",
        "docs",
    )


def test_git_local_config_entries_match_repository_contract() -> None:
    """
    Ensure bootstrap applies the full repository-local Git config contract.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    entries = bootstrap_dev_environment.git_local_config_entries()

    assert entries == [
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
        ("alias.check", "!uv run python scripts/validate_repo.py"),
        (
            "alias.fix",
            "!uv run python scripts/run_repo_tool.py ruff check . --fix && uv run python scripts/run_repo_tool.py ruff format .",
        ),
        ("alias.clean-repo", '!f() { uv run python scripts/clean_repo.py "$@"; }; f'),
        (
            "alias.new-decision",
            '!f() { uv run python scripts/new_decision.py "$@"; }; f',
        ),
        (
            "alias.gen-issues",
            "!uv run python scripts/generate_github_snapshot.py issues --output issues.json",
        ),
        (
            "alias.gen-miles",
            "!uv run python scripts/generate_github_snapshot.py milestones --output milestones.json",
        ),
        (
            "alias.txz",
            """!f() { name="${1:-fontshow}"; tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT; mkdir -p "$tmp/fontshow"; { git ls-files -z; printf "%s\\0" issues.json milestones.json; } | XZ_OPT="-9e -T0" tar --null -T - -cJf "$PWD/$name.tar.xz" --transform='s,^,fontshow/,'; }; f""",
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
        ("pull.ff", "only"),
        ("pull.rebase", "false"),
        ("rebase.autostash", "true"),
    ]


def test_build_bootstrap_commands_include_git_setup_and_validation() -> None:
    """
    Ensure the default bootstrap plan covers environment sync,
    repository-local Git configuration, and validation steps.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    repo_root = Path("/tmp/fontshow")

    commands = bootstrap_dev_environment.build_bootstrap_commands(
        repo_root=repo_root,
        git_executable="/usr/bin/git",
        options=bootstrap_dev_environment.BootstrapOptions(
            venv_dir=".venv",
            with_docs=False,
            run_validation=True,
        ),
    )

    argvs = [command.argv for command in commands]

    assert ("uv", "sync", "--group", "dev") in argvs
    assert ("uv", "pip", "check") in argvs
    assert any(
        argv[:4]
        == (
            "/usr/bin/git",
            "config",
            "--local",
            "alias.rel",
        )
        for argv in argvs
    )
    assert ("uv", "run", "python", "scripts/validate_repo.py") in argvs


def test_build_bootstrap_commands_can_skip_validation_and_include_docs() -> None:
    """
    Ensure docs dependency synchronization is enabled while validation
    commands are omitted when requested.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    repo_root = Path("/tmp/fontshow")

    commands = bootstrap_dev_environment.build_bootstrap_commands(
        repo_root=repo_root,
        git_executable="/usr/bin/git",
        options=bootstrap_dev_environment.BootstrapOptions(
            venv_dir=".venv",
            with_docs=True,
            run_validation=False,
        ),
    )

    argvs = [command.argv for command in commands]

    assert ("uv", "sync", "--group", "dev", "--extra", "docs") in argvs
    assert ("uv", "pip", "check") in argvs
    assert any(
        argv[:4]
        == (
            "/usr/bin/git",
            "config",
            "--local",
            "alias.rel",
        )
        for argv in argvs
    )
    assert not any(
        argv == ("uv", "run", "python", "scripts/validate_repo.py") for argv in argvs
    )
