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


def test_install_target_tracks_requested_dependency_groups() -> None:
    """
    Ensure editable install extras remain explicit and deterministic.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert bootstrap_dev_environment.install_target(with_docs=False) == ".[dev]"
    assert bootstrap_dev_environment.install_target(with_docs=True) == ".[dev,docs]"


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
        (
            "alias.check",
            "!bash -lc 'source .venv/bin/activate && black --check . && ruff check . && mypy . && pytest -q'",
        ),
        ("alias.fix", "!ruff check . --fix"),
        ("alias.clean-repo", '!f() { python scripts/clean_repo.py "$@"; }; f'),
        (
            "alias.test-coverage",
            '!f() { pytest --cov=fontshow --cov-report=term-missing "$@"; }; f',
        ),
        (
            "alias.test-html",
            "!pytest --cov=fontshow --cov-report=html && xdg-open htmlcov/index.html",
        ),
        ("alias.new-decision", '!f() { python scripts/new_decision.py "$@"; }; f'),
        (
            "alias.release-preview",
            '!f() { python scripts/release_preview.py "$@"; }; f',
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
        ("alias.gen-boot-report", "!python scripts/generate_bootstrap_audit_report.py"),
        ("alias.ver-boot-report", "!python scripts/verify_bootstrap_audit_report.py"),
        (
            "alias.install-dev-codira",
            '!python ../codira/scripts/install_first_party_packages.py --python "$VIRTUAL_ENV/bin/python" --include-core --core-extra semantic --include-bundle',
        ),
        ("pull.ff", "only"),
        ("pull.rebase", "false"),
        ("rebase.autostash", "true"),
    ]


def test_select_bootstrap_python_uses_base_interpreter_for_target_venv() -> None:
    """
    Ensure bootstrap avoids recreating the target virtual environment with itself.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    repo_root = Path("/tmp/fontshow")
    selected = bootstrap_dev_environment.select_bootstrap_python(
        "/tmp/fontshow/.venv/bin/python",
        repo_root=repo_root,
        venv_dir=".venv",
    )

    assert Path(selected).resolve() == Path(sys._base_executable).resolve()


def test_select_bootstrap_python_preserves_explicit_external_interpreter() -> None:
    """
    Ensure an explicit external interpreter is preserved unchanged.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    repo_root = Path("/tmp/fontshow")
    requested_python = "/usr/bin/python3"

    selected = bootstrap_dev_environment.select_bootstrap_python(
        requested_python,
        repo_root=repo_root,
        venv_dir=".venv",
    )

    assert selected == requested_python


def test_build_bootstrap_commands_include_git_setup_and_validation() -> None:
    """
    Ensure the default bootstrap plan covers install, config, and validation.

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
        python_executable="/usr/bin/python3",
        git_executable="/usr/bin/git",
        options=bootstrap_dev_environment.BootstrapOptions(
            venv_dir=".venv",
            with_docs=False,
            run_validation=True,
            create_venv=True,
        ),
    )

    assert commands[0].argv[:3] == (
        "/usr/bin/python3",
        "-m",
        "venv",
    )
    assert Path(commands[0].argv[3]) == repo_root / ".venv"
    assert bootstrap_dev_environment.BOOTSTRAP_SETUPTOOLS_SPEC in commands[1].argv
    assert commands[2].argv[-1] == ".[dev]"
    assert any(
        command.argv[:4] == ("/usr/bin/git", "config", "--local", "alias.rel")
        for command in commands
    )
    assert commands[-2].argv[-2:] == ("run", "--all-files")
    assert commands[-1].argv[-1] == "-q"


def test_build_bootstrap_commands_can_skip_validation_and_include_docs() -> None:
    """
    Ensure optional docs install and validation skipping affect only planned steps.

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
        python_executable="/usr/bin/python3",
        git_executable="/usr/bin/git",
        options=bootstrap_dev_environment.BootstrapOptions(
            venv_dir=".venv",
            with_docs=True,
            run_validation=False,
            create_venv=False,
        ),
    )

    assert commands[1].argv[-1] == ".[dev,docs]"
    assert all(command.argv[1:3] != ("-m", "venv") for command in commands)
    assert not any("pre-commit" in command.description for command in commands)
    assert not any("pytest" in command.description for command in commands)
