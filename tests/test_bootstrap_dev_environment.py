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
