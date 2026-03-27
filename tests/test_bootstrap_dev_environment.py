"""
Verify the development bootstrap maintenance script.
"""

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


def test_git_alias_entries_are_repo_safe_and_self_contained() -> None:
    """
    Ensure bootstrap installs only portable repository-local Git aliases.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """

    entries = dict(bootstrap_dev_environment.git_alias_entries())

    assert entries["core.hooksPath"] == ".githooks"
    assert entries["commit.template"] == ".gitmessage"
    assert "alias.rel" in entries
    assert "alias.gen-boot-report" in entries
    assert "alias.gen-issues" not in entries
    assert "alias.gen-miles" not in entries
    assert "alias.gen-zip" not in entries
    assert ".venv" in entries["alias.clean-artifacts"]


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
        ),
    )

    assert commands[0].argv == (
        "/usr/bin/python3",
        "-m",
        "venv",
        "/tmp/fontshow/.venv",
    )
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
        ),
    )

    assert commands[2].argv[-1] == ".[dev,docs]"
    assert not any("pre-commit" in command.description for command in commands)
    assert not any("pytest" in command.description for command in commands)
